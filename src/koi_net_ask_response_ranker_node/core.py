from koi_net.core import FullNode
from .config import AskResponseRankerNodeConfig
from .knowledge_handlers import ranking_handler


class AskResponseRankerNode(FullNode):
    config_schema = AskResponseRankerNodeConfig
    knowledge_handlers = FullNode.knowledge_handlers + [
        ranking_handler
    ]