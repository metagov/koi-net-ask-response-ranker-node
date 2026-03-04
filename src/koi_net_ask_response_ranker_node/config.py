from pydantic import BaseModel
from rid_lib.types import KoiNetNode, SlackUserGroup
from koi_net.config import (
    FullNodeConfig, 
    KoiNetConfig, 
    FullNodeProfile, 
    NodeProvides
)

from .rid_types import AskCoreResponse, AskRankedResponses


class CustomConfig(BaseModel):
    staff_user_group: SlackUserGroup | None = None

class AskResponseRankerNodeConfig(FullNodeConfig):
    koi_net: KoiNetConfig = KoiNetConfig(
        node_name="ask-response-ranker",
        node_profile=FullNodeProfile(
            provides=NodeProvides(
                event=[AskRankedResponses],
                state=[AskRankedResponses]
            )
        ),
        rid_types_of_interest=[KoiNetNode, AskCoreResponse, SlackUserGroup]
    )
    response_ranking: CustomConfig = CustomConfig()