from __future__ import annotations

from logged_groups import logged_group

from ..common_neon.eth_proto import Trx as EthTx
from ..common_neon.address import EthereumAddress
from ..common_neon.errors import EthereumError
from ..common_neon.account_whitelist import AccountWhitelist
from ..common_neon.solana_receipt_parser import SolReceiptParser
from ..common_neon.solana_interactor import SolanaInteractor
from ..common_neon.estimate import GasEstimate

from ..common_neon.elf_params import ElfParams
from ..common_neon.environment_data import ACCOUNT_PERMISSION_UPDATE_INT, ALLOW_UNDERPRICED_TX_WITHOUT_CHAINID

from ..common_neon.emulator_interactor import call_trx_emulated
from ..common_neon.types import NeonTxPrecheckResult, NeonEmulatingResult


@logged_group("neon.Proxy")
class NeonTxValidator:
    MAX_U64 = pow(2, 64)
    MAX_U256 = pow(2, 256)

    def __init__(self, solana: SolanaInteractor, tx: EthTx, min_gas_price: int):
        self._solana = solana
        self._tx = tx

        self._sender = '0x' + tx.sender()
        self._neon_account_info = self._solana.get_neon_account_info(EthereumAddress(self._sender))

        self._deployed_contract = tx.contract()
        if self._deployed_contract:
            self._deployed_contract = '0x' + self._deployed_contract

        self._to_address = tx.toAddress.hex()
        if self._to_address:
            self._to_address = '0x' + self._to_address

        self._tx_hash = '0x' + self._tx.hash_signed().hex()
        self._min_gas_price = min_gas_price
        self._estimated_gas = 0

        self._tx_gas_limit = self._tx.gasLimit

        if self._tx.hasChainId() or (not ALLOW_UNDERPRICED_TX_WITHOUT_CHAINID):
            return

        if len(self._tx.callData) == 0:
            return
        no_chainid_gas_limit_multiplier = ElfParams().neon_gas_limit_multiplier_no_chainid
        tx_gas_limit = self._tx_gas_limit * no_chainid_gas_limit_multiplier
        if self.MAX_U64 > tx_gas_limit:
            self._tx_gas_limit = tx_gas_limit

    def is_underpriced_tx_without_chainid(self) -> bool:
        if self._tx.hasChainId():
            return False
        return (self._tx.gasPrice < self._min_gas_price) or (self._tx.gasLimit < self._estimated_gas)

    def precheck(self) -> NeonTxPrecheckResult:
        try:
            self._prevalidate_tx()
            emulating_result: NeonEmulatingResult = call_trx_emulated(self._tx)
            self._prevalidate_emulator(emulating_result)

            is_underpriced_tx_without_chainid = self.is_underpriced_tx_without_chainid()
            precheck_result = NeonTxPrecheckResult(emulating_result=emulating_result,
                                                   is_underpriced_tx_without_chainid=is_underpriced_tx_without_chainid)
            return precheck_result

        except Exception as e:
            self.extract_ethereum_error(e)
            raise

    def _prevalidate_tx(self):
        self._prevalidate_whitelist()
        self._prevalidate_tx_nonce()
        self._prevalidate_tx_gas()
        self._prevalidate_tx_chain_id()
        self._prevalidate_tx_size()
        self._prevalidate_sender_balance()

    def _prevalidate_emulator(self, emulator_json: dict):
        self._prevalidate_gas_usage(emulator_json)
        self._prevalidate_account_sizes(emulator_json)
        self._prevalidate_underpriced_tx_without_chainid()

    def extract_ethereum_error(self, e: Exception):
        receipt_parser = SolReceiptParser(e)
        nonce_error = receipt_parser.get_nonce_error()
        if nonce_error:
            self._raise_nonce_error(nonce_error[0], nonce_error[1])

    def _prevalidate_whitelist(self):
        w = AccountWhitelist(self._solana, ACCOUNT_PERMISSION_UPDATE_INT)
        if not w.has_client_permission(self._sender[2:]):
            self.warning(f'Sender account {self._sender} is not allowed to execute transactions')
            raise EthereumError(message=f'Sender account {self._sender} is not allowed to execute transactions')

        if (self._deployed_contract is not None) and (not w.has_contract_permission(self._deployed_contract[2:])):
            self.warning(f'Contract account {self._deployed_contract} is not allowed for deployment')
            raise EthereumError(message=f'Contract account {self._deployed_contract} is not allowed for deployment')

    def _prevalidate_tx_gas(self):
        if self._tx_gas_limit > self.MAX_U64:
            raise EthereumError(message='gas uint64 overflow')
        if (self._tx_gas_limit * self._tx.gasPrice) > (self.MAX_U256 - 1):
            raise EthereumError(message='max fee per gas higher than 2^256-1')
        if self._tx.gasPrice >= self._min_gas_price:
            return

        if ALLOW_UNDERPRICED_TX_WITHOUT_CHAINID and (not self._tx.hasChainId()) and (self._tx.gasPrice >= 10**10):
            return

        raise EthereumError(message=f"transaction underpriced: have {self._tx.gasPrice} want {self._min_gas_price}")

    def _prevalidate_tx_chain_id(self):
        if self._tx.chainId() not in (None, ElfParams().chain_id):
            raise EthereumError(message='wrong chain id')

    def _prevalidate_tx_size(self):
        if len(self._tx.callData) > (128 * 1024 - 1024):
            raise EthereumError(message='transaction size is too big')

    def _prevalidate_tx_nonce(self):
        if not self._neon_account_info:
            return

        tx_nonce = int(self._tx.nonce)
        if self.MAX_U64 not in (self._neon_account_info.trx_count, tx_nonce):
            if tx_nonce == self._neon_account_info.trx_count:
                return

        self._raise_nonce_error(self._neon_account_info.trx_count, tx_nonce)

    def _prevalidate_sender_eoa(self):
        if not self._neon_account_info:
            return

        if self._neon_account_info.code_account:
            raise EthereumError("sender not an eoa")

    def _prevalidate_sender_balance(self):
        if self._neon_account_info:
            user_balance = self._neon_account_info.balance
        else:
            user_balance = 0

        required_balance = self._tx.gasPrice * self._tx_gas_limit + self._tx.value

        if required_balance <= user_balance:
            return

        if len(self._tx.callData) == 0:
            message = 'insufficient funds for transfer'
        else:
            message = 'insufficient funds for gas * price + value'

        raise EthereumError(f"{message}: address {self._sender} have {user_balance} want {required_balance}")

    def _prevalidate_gas_usage(self, emulator_json: dict):
        request = {
            'from': self._sender,
            'to': self._to_address,
            'data': self._tx.callData.hex(),
            'value': hex(self._tx.value)
        }

        calculator = GasEstimate(request, self._solana)
        calculator.emulator_json = emulator_json
        self._estimated_gas = calculator.estimate()

        if self._estimated_gas <= self._tx_gas_limit:
            return

        message = 'gas limit reached'
        raise EthereumError(f"{message}: have {self._tx_gas_limit} want {self._estimated_gas}")

    def _prevalidate_underpriced_tx_without_chainid(self):
        if not self.is_underpriced_tx_without_chainid():
            return
        if ALLOW_UNDERPRICED_TX_WITHOUT_CHAINID:
            return

        raise EthereumError(f"proxy configuration doesn't allow underpriced transaction without chain-id")

    @staticmethod
    def _prevalidate_account_sizes(emulator_json: dict):
        for account_desc in emulator_json['accounts']:
            if ('code_size' not in account_desc) or ('address' not in account_desc):
                continue
            if (not account_desc['code_size']) or (not account_desc['address']):
                continue
            if account_desc['code_size'] > ((9 * 1024 + 512) * 1024):
                raise EthereumError(f"contract {account_desc['address']} " +
                                    f"requests a size increase to more than 9.5Mb")


    def _raise_nonce_error(self, account_tx_count: int, tx_nonce: int):
        if self.MAX_U64 in (account_tx_count, tx_nonce):
            message = 'nonce has max value'
        elif account_tx_count > tx_nonce:
            message = 'nonce too low'
        else:
            message = 'nonce too high'

        raise EthereumError(code=-32002,
                            message=f'{message}: address {self._sender}, tx: {tx_nonce} state: {account_tx_count}')
