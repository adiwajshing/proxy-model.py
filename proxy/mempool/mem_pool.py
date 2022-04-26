import asyncio
from typing import List, Tuple
from logged_groups import logged_group
import bisect

from .mempool_api import MemPoolRequest, MemPoolResultCode, MemPoolResult, IMemPoolExecutor


@logged_group("neon.MemPool")
class MemPool:

    TX_QUEUE_MAX_SIZE = 4096
    TX_QUEUE_SIZE = 4095
    CHECK_TASK_TIMEOUT_SEC = 0.05

    def __init__(self, executor: IMemPoolExecutor):
        self._tx_req_queue = []
        self._lock = asyncio.Lock()
        self._tx_req_queue_cond = asyncio.Condition()
        self._processing_tasks: List[Tuple[int, asyncio.Task, MemPoolRequest]] = []
        self._process_tx_results_task = asyncio.get_event_loop().create_task(self.check_processing_tasks())
        self._process_tx_queue_task = asyncio.get_event_loop().create_task(self.process_tx_queue())

        self._executor = executor

    async def enqueue_mp_request(self, mp_request: MemPoolRequest):
        tx_hash = mp_request.neon_tx.hash_signed().hex()
        try:
            self.debug(f"Got mp_tx_request: 0x{tx_hash} to be scheduled on the mempool")
            if len(self._tx_req_queue) > MemPool.TX_QUEUE_MAX_SIZE:
                self._tx_req_queue = self._tx_req_queue[-MemPool.TX_QUEUE_SIZE:]
            bisect.insort_left(self._tx_req_queue, mp_request)
            await self._kick_tx_queue()
        except Exception as err:
            self.error(f"Failed enqueue tx: {tx_hash} into queue: {err}")

    async def process_tx_queue(self):
        while True:
            async with self._tx_req_queue_cond:
                await self._tx_req_queue_cond.wait()
                if len(self._tx_req_queue) == 0:
                    self.debug("Tx queue empty - continue waiting for new")
                    continue
                if not self._executor.is_available():
                    self.debug("No way to process tx - no available executor")
                    continue
                mp_tx_request: MemPoolRequest = self._tx_req_queue.pop()
                self.submit_request_to_executor(mp_tx_request)

    def submit_request_to_executor(self, mp_tx_request: MemPoolRequest):
        resource_id, task = self._executor.submit_mempool_request(mp_tx_request)
        self._processing_tasks.append((resource_id, task, mp_tx_request))

    async def check_processing_tasks(self):
        while True:
            not_finished_tasks = []
            for resource_id, task, mp_request in self._processing_tasks:
                if not task.done():
                    not_finished_tasks.append((resource_id, task, mp_request))
                    self._executor.release_resource(resource_id)
                    continue
                exception = task.exception()
                if exception is not None:
                    self.error(f"Exception during processing request: {exception} - tx will be dropped away")
                    self._on_request_dropped_away(mp_request)
                    self._executor.release_resource(resource_id)
                    continue

                mp_result: MemPoolResult = task.result()
                assert isinstance(mp_result, MemPoolResult)
                assert mp_result.code != MemPoolResultCode.Dummy
                await self._process_mp_result(resource_id, mp_result, mp_request)

            self._processing_tasks = not_finished_tasks
            await asyncio.sleep(MemPool.CHECK_TASK_TIMEOUT_SEC)

    async def _process_mp_result(self, resource_id: int, mp_result: MemPoolResult, mp_request: MemPoolRequest):
        hash = "0x" + mp_request.neon_tx.hash_signed().hex()
        if mp_result.code == MemPoolResultCode.Done:
            self.debug(f"Neon tx: {hash} - processed on executor: {resource_id} - done")
            self._on_request_done(mp_request)
            self._executor.release_resource(resource_id)
            await self._kick_tx_queue()
            return
        self.warning(f"Failed to process tx: {hash} - on executor: {resource_id}, status: {mp_result} - reschedule")
        if mp_result.code == MemPoolResultCode.ToBeRepeat:
            self._executor.release_resource(resource_id)
        elif mp_result.code == MemPoolResultCode.NoLiquidity:
            self._executor.on_no_liquidity(resource_id)
            await self.enqueue_mp_request(mp_request)

    def _on_request_done(self, tx_request: MemPoolRequest):
        pass

    def _on_request_dropped_away(self, tx_request: MemPoolRequest):
        pass

    async def _kick_tx_queue(self):
        async with self._tx_req_queue_cond:
            self._tx_req_queue_cond.notify()