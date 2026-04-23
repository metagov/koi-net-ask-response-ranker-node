from pydantic import BaseModel, Field
from rid_lib.types import KoiNetNode, SlackUser, SlackUserGroup
from koi_net.config import (
    EnvConfig,
    FullNodeConfig, 
    KoiNetConfig, 
    FullNodeProfile, 
    NodeProvides
)

from .rid_types import AskCoreResponse, AskCoreThread, AskRankedResponses


class SlackEnvConfig(EnvConfig):
    ask_rr_slack_bot_token: str
    ask_rr_slack_signing_secret: str

class CustomConfig(BaseModel):
    staff_user_group: SlackUserGroup | None = None
    ignored_response_authors: list[SlackUser] = []

class AskResponseRankerNodeConfig(FullNodeConfig):
    koi_net: KoiNetConfig = KoiNetConfig(
        node_name="ask-response-ranker",
        node_profile=FullNodeProfile(
            provides=NodeProvides(
                event=[AskRankedResponses],
                state=[AskRankedResponses]
            )
        ),
        rid_types_of_interest=[KoiNetNode, AskCoreThread, AskCoreResponse, SlackUserGroup]
    )
    response_ranking: CustomConfig = CustomConfig()
    env: SlackEnvConfig = Field(default_factory=SlackEnvConfig)