from koi_net.core import FullNode
from slack_bolt import App

from .ask_thread_handler import AskThreadHandler
from .config import AskResponseRankerNodeConfig
from .ranking_handler import RankingHandler


class AskResponseRankerNode(FullNode):
    config_schema = AskResponseRankerNodeConfig
    ranking_handler = RankingHandler
    
    slack_app: App = lambda config: App(
        token=config.env.ask_rr_slack_bot_token,
        signing_secret=config.env.ask_rr_slack_signing_secret
    )
    
    ask_thread_handler = AskThreadHandler
