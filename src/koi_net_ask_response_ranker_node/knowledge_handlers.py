from rid_lib.ext import Bundle
import structlog
from koi_net.processor.handler import (
    KnowledgeHandler, 
    HandlerType, 
    HandlerContext,
    KnowledgeObject
)

from .models import AskCoreResponseModel, RankedResponsesModel

from .rid_types import AskCoreResponse, AskRankedResponses

log = structlog.stdlib.get_logger()


@KnowledgeHandler.create(
    handler_type=HandlerType.Network,
    rid_types=[AskCoreResponse])
def ranking_handler(ctx: HandlerContext, kobj: KnowledgeObject):
    response = kobj.bundle.validate_contents(AskCoreResponseModel)
    
    ranked_responses_rid = AskRankedResponses(
        team_id=response.thread.team_id,
        channel_id=response.thread.channel_id,
        ts=response.thread.ts
    )
    
    bundle = ctx.cache.read(ranked_responses_rid)
    if bundle:
        ranked_responses = bundle.validate_contents(RankedResponsesModel)
    else:
        ranked_responses = RankedResponsesModel(thread=response.thread)
    
    thumbs_up = "+1"
    medal = "sports_medal"
    check = "white_check_mark"
    
    if thumbs_up in response.reactions:
        reaction_count = len(response.reactions[thumbs_up])
        
        if ranked_responses.community_voted:
            ...
            
        elif reaction_count > 0:
            ctx.log.info("New thread")
            ranked_responses.community_voted = kobj.rid
            
    if medal in response.reactions:
        ...
        
    if check in response.reactions:
        ...
    
    ctx.kobj_queue.push(bundle=Bundle.generate(
        rid=ranked_responses_rid,
        contents=ranked_responses.model_dump()
    ))