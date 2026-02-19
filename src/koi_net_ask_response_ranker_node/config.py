from pydantic import BaseModel
from rid_lib.types import KoiNetNode, SlackUserGroup
from koi_net.config.full_node import (
    FullNodeConfig, 
    KoiNetConfig, 
    ServerConfig, 
    NodeProfile, 
    NodeProvides
)

from .rid_types import AskCoreResponse, AskRankedResponses


class CustomConfig(BaseModel):
    staff_user_group: SlackUserGroup | None = None

class AskResponseRankerNodeConfig(FullNodeConfig):
    koi_net: KoiNetConfig = KoiNetConfig(
        node_name="ask-response-ranker",
        node_profile=NodeProfile(
            provides=NodeProvides(
                event=[AskRankedResponses],
                state=[AskRankedResponses]
            )
        ),
        rid_types_of_interest=[KoiNetNode, AskCoreResponse]
    )
    response_ranking: CustomConfig = CustomConfig()