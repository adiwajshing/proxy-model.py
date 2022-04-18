from .proxy import entry_point
from .mempool.mempool_service import MemPoolService

from .statistics_exporter.prometheus_proxy_server import PrometheusProxyServer


class NeonProxyApp:

    def __init__(self):
        self._mempool_service = MemPoolService()

    def start(self):
        self._mempool_service.start()
        PrometheusProxyServer()
        entry_point()
