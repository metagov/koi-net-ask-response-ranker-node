from rid_lib.types import KoiNetNode
from koi_net.config.full_node import (
    FullNodeConfig, 
    KoiNetConfig, 
    ServerConfig, 
    NodeProfile, 
    NodeProvides
)

from .rid_types import AskCoreResponse, AskRankedResponses


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