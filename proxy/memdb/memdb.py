from logged_groups import logged_group
from typing import Optional

from ..common_neon.environment_data import FINALIZED, ONLY_TRACK_BLOCKS_WITH_NEON_TRANSACTION

from ..indexer.indexer_db import IndexerDB

from ..common_neon.utils import NeonTxInfo, NeonTxResultInfo, NeonTxFullInfo
from ..common_neon.solana_interactor import SolanaInteractor

from ..memdb.blocks_db import MemBlocksDB, SolanaBlockInfo
from ..memdb.pending_tx_db import MemPendingTxsDB, NeonPendingTxInfo
from ..memdb.transactions_db import MemTxsDB


@logged_group("neon.Proxy")
class MemDB:
    def __init__(self, solana: SolanaInteractor):
        self._solana = solana
        self._db = IndexerDB(solana)

        self._blocks_db = MemBlocksDB(self._solana, self._db)
        self._txs_db = MemTxsDB(self._db)
        self._pending_tx_db = MemPendingTxsDB(self._db)

    def _before_slot(self) -> int:
        return self._blocks_db.get_db_block_slot() - 5

    def get_latest_block(self) -> SolanaBlockInfo:
        return self._blocks_db.get_latest_block()

    def get_latest_slot_with_transaction(self) -> int:
        return self._blocks_db.get_latest_slot_with_transaction()

    def get_latest_block_slot(self) -> int:
        return self._blocks_db.get_latest_block_slot()

    def get_starting_block_slot(self) -> int:
        return self._blocks_db.get_staring_block_slot()

    def get_starting_block(self) -> SolanaBlockInfo:
        return self._db.get_starting_block()

    def get_full_block_by_slot(self, block_slot: int, gen_fake_if_not_found = True) -> SolanaBlockInfo:
        return self._blocks_db.get_full_block_by_slot(block_slot, gen_fake_if_not_found, False)

    def get_block_by_hash(self, block_hash: str, update_dicts = True) -> SolanaBlockInfo:
        return self._blocks_db.get_block_by_hash(block_hash, update_dicts)

    def pend_transaction(self, tx: NeonPendingTxInfo):
        self._pending_tx_db.pend_transaction(tx, self._before_slot())

    def submit_transaction(self, neon_tx: NeonTxInfo, neon_res: NeonTxResultInfo, sign_list: [str]):
        block = self._blocks_db.submit_block(neon_res)
        neon_res.fill_block_info(block)
        self._txs_db.submit_transaction(neon_tx, neon_res, sign_list, self._before_slot())

    def get_tx_list_by_sol_sign(self, is_finalized: bool, sol_sign_list: [str]) -> [NeonTxFullInfo]:
        if (not sol_sign_list) or (not len(sol_sign_list)):
            return []
        before_slot = 0 if is_finalized else self._before_slot()
        return self._txs_db.get_tx_list_by_sol_sign(is_finalized, sol_sign_list, before_slot)

    def get_tx_by_neon_sign(self, neon_sign: str) -> Optional[NeonTxFullInfo]:
        is_using_finalized = ONLY_TRACK_BLOCKS_WITH_NEON_TRANSACTION and FINALIZED == 'finalized'
        if is_using_finalized:
            before_slot = 0
            is_pended_tx = False
        else:
            before_slot = self._before_slot()
            is_pended_tx = self._pending_tx_db.is_exist(neon_sign, before_slot)
        return self._txs_db.get_tx_by_neon_sign(neon_sign, is_pended_tx, before_slot)

    def get_logs(self, from_block, to_block, addresses, topics, block_hash):
        return self._txs_db.get_logs(from_block, to_block, addresses, topics, block_hash)

    def get_contract_code(self, address: str) -> str:
        return self._db.get_contract_code(address)

    def get_sol_sign_list_by_neon_sign(self, neon_sign: str) -> [str]:
        before_slot = self._before_slot()
        is_pended_tx = self._pending_tx_db.is_exist(neon_sign, before_slot)
        return self._txs_db.get_sol_sign_list_by_neon_sign(neon_sign, is_pended_tx, before_slot)
