import os
from decimal import Decimal
from solana.publickey import PublicKey

SOLANA_URL = os.environ.get("SOLANA_URL", "http://localhost:8899")
PP_SOLANA_URL = os.environ.get("PP_SOLANA_URL", SOLANA_URL)
EVM_LOADER_ID = os.environ.get("EVM_LOADER")
neon_cli_timeout = float(os.environ.get("NEON_CLI_TIMEOUT", "0.5"))
CONFIRMATION_CHECK_DELAY = float(os.environ.get("NEON_CONFIRMATION_CHECK_DELAY", "0.1"))
CONTINUE_COUNT_FACTOR = int(os.environ.get("CONTINUE_COUNT_FACTOR", "3"))
TIMEOUT_TO_RELOAD_NEON_CONFIG = int(os.environ.get("TIMEOUT_TO_RELOAD_NEON_CONFIG", "3600"))

MINIMAL_GAS_PRICE = os.environ.get("MINIMAL_GAS_PRICE", None)
if MINIMAL_GAS_PRICE is not None:
    MINIMAL_GAS_PRICE = int(MINIMAL_GAS_PRICE)*10**9
EXTRA_GAS = int(os.environ.get("EXTRA_GAS", "0"))
LOG_NEON_CLI_DEBUG = os.environ.get("LOG_NEON_CLI_DEBUG", "NO") == "YES"
USE_EARLIEST_BLOCK_IF_0_PASSED = os.environ.get("USE_EARLIEST_BLOCK_IF_0_PASSED", "NO") == "YES"
RETRY_ON_FAIL = int(os.environ.get("RETRY_ON_FAIL", "10"))
RETRY_ON_FAIL_ON_GETTING_CONFIRMED_TRANSACTION = max(int(os.environ.get("RETRY_ON_FAIL_ON_GETTING_CONFIRMED_TRANSACTION", "1000")), 1)
FUZZING_BLOCKHASH = os.environ.get("FUZZING_BLOCKHASH", "NO") == "YES"
CONFIRM_TIMEOUT = max(int(os.environ.get("CONFIRM_TIMEOUT", 10)), 10)
PARALLEL_REQUESTS = int(os.environ.get("PARALLEL_REQUESTS", 10))
HISTORY_START = "7BdwyUQ61RUZP63HABJkbW66beLk22tdXnP69KsvQBJekCPVaHoJY47Rw68b3VV1UbQNHxX3uxUSLfiJrfy2bTn"
INDEXER_POLL_COUNT = int(os.environ.get("INDEXER_POLL_COUNT", "1000"))
START_SLOT = os.environ.get('START_SLOT', 0)
INDEXER_RECEIPTS_COUNT_LIMIT = int(os.environ.get("INDEXER_RECEIPTS_COUNT_LIMIT", "1000"))
FINALIZED = os.environ.get('FINALIZED', 'finalized')
CANCEL_TIMEOUT = int(os.environ.get("CANCEL_TIMEOUT", 60))
SKIP_CANCEL_TIMEOUT = int(os.environ.get("CANCEL_TIMEOUT", 1000))
HOLDER_TIMEOUT = int(os.environ.get("HOLDER_TIMEOUT", "216000"))  # 1 day by default
ACCOUNT_PERMISSION_UPDATE_INT = int(os.environ.get("ACCOUNT_PERMISSION_UPDATE_INT", 60 * 5))
PERM_ACCOUNT_LIMIT = max(int(os.environ.get("PERM_ACCOUNT_LIMIT", 2)), 2)
OPERATOR_FEE = Decimal(os.environ.get("OPERATOR_FEE", "0.1"))
GAS_PRICE_SUGGESTED_PCT = Decimal(os.environ.get("GAS_PRICE_SUGGEST_PCT", "0.05"))
NEON_PRICE_USD = Decimal('0.25')
SOL_PRICE_UPDATE_INTERVAL = int(os.environ.get("SOL_PRICE_UPDATE_INTERVAL", 60))
GET_SOL_PRICE_MAX_RETRIES = int(os.environ.get("GET_SOL_PRICE_MAX_RETRIES", 10))
GET_SOL_PRICE_RETRY_INTERVAL = int(os.environ.get("GET_SOL_PRICE_RETRY_INTERVAL", 1))
INDEXER_LOG_SKIP_COUNT = int(os.environ.get("INDEXER_LOG_SKIP_COUNT", 100))
RECHECK_RESOURCE_LIST_INTERVAL = int(os.environ.get('RECHECK_RESOURCE_LIST_INTERVAL', 60))
MIN_OPERATOR_BALANCE_TO_WARN = max(int(os.environ.get("MIN_OPERATOR_BALANCE_TO_WARN", 9000000000)), 9000000000)
MIN_OPERATOR_BALANCE_TO_ERR = max(int(os.environ.get("MIN_OPERATOR_BALANCE_TO_ERR", 1000000000)), 1000000000)
SKIP_PREFLIGHT = os.environ.get("SKIP_PREFLIGHT", "NO") == "YES"
CONTRACT_EXTRA_SPACE = int(os.environ.get("CONTRACT_EXTRA_SPACE", 2048))
EVM_STEP_COUNT = int(os.environ.get("EVM_STEP_COUNT", 750))  # number of evm-steps, performed by one iteration
ENABLE_PRIVATE_API = os.environ.get("ENABLE_PRIVATE_API", "NO") == "YES"
GATHER_STATISTICS = os.environ.get("GATHER_STATISTICS", "NO") == "YES"
ALLOW_UNDERPRICED_TX_WITHOUT_CHAINID = os.environ.get("ALLOW_UNDERPRICED_TX_WITHOUT_CHAINID", "NO") == "YES"
LOG_FULL_OBJECT_INFO = os.environ.get("LOG_FULL_OBJECT_INFO", "NO") == "YES"
PYTH_MAPPING_ACCOUNT = os.environ.get("PYTH_MAPPING_ACCOUNT", None)
if PYTH_MAPPING_ACCOUNT is not None:
    PYTH_MAPPING_ACCOUNT = PublicKey(PYTH_MAPPING_ACCOUNT)
# uses the "earliest" tag if "0x0" or "0" is passed to the "eth_getBlockByNumber" RPC
USE_EARLIEST_BLOCK_IF_0_PASSED = os.environ.get("USE_EARLIEST_BLOCK_IF_0_PASSED", "NO") == "YES"
# fetches a block from Solana net if it wasn't found in the DB
FETCH_BLOCK_FROM_NET_IF_NOT_FOUND = os.environ.get("FETCH_BLOCK_FROM_NET_IF_NOT_FOUND", "YES") == "YES"
# only track Solana blocks that have NEON transactions in them
ONLY_TRACK_BLOCKS_WITH_NEON_TRANSACTION = os.environ.get("ONLY_TRACK_BLOCKS_WITH_NEON_TRANSACTION", "NO") == "YES"
GEN_FAKE_BLOCK_FOR_GET_BY_BLOCK_NUMBER = os.environ.get("GEN_FAKE_BLOCK_FOR_GET_BY_BLOCK_NUMBER", "YES") == "YES"
