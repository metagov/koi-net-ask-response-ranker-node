from koi_net.core import FullNode
from .config import AskResponseRankerNodeConfig
from .ranking_handler import RankingHandler


class AskResponseRankerNode(FullNode):
    config_schema = AskResponseRankerNodeConfig
    ranking_handler = RankingHandler