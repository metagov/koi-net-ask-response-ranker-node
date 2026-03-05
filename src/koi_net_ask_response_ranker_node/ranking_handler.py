from dataclasses import dataclass

from rid_lib.ext import Bundle
from koi_net.components.interfaces import KnowledgeHandler, HandlerType
from koi_net.components import Cache, Effector, KobjQueue
from koi_net.protocol import KnowledgeObject

from .config import AskResponseRankerNodeConfig
from .models import AskCoreResponseModel, AskCoreThreadModel, RankedResponsesModel
from .rid_types import AskCoreThread, AskCoreResponse, AskRankedResponses


THUMBS_UP = "+1"
SPORTS_MEDAL = "sports_medal"
CHECK_MARK = "white_check_mark"

@dataclass
class RankingHandler(KnowledgeHandler):
    cache: Cache
    effector: Effector
    config: AskResponseRankerNodeConfig
    kobj_queue: KobjQueue
    
    handler_type = HandlerType.Network
    rid_types = (AskCoreThread, AskCoreResponse)
    
    def handle(self, kobj: KnowledgeObject):
        if type(kobj.rid) is AskCoreThread:
            response = None
            thread_rid = kobj.rid
            
        elif type(kobj.rid) is AskCoreResponse:
            response = kobj.bundle.validate_contents(AskCoreResponseModel)
            thread_rid = response.thread
        
        ranked_responses_rid = AskRankedResponses(
            team_id=thread_rid.team_id,
            channel_id=thread_rid.channel_id,
            ts=thread_rid.ts
        )
        
        bundle = self.cache.read(ranked_responses_rid)
        if bundle:
            ranked_responses = bundle.validate_contents(RankedResponsesModel)
        else:
            ranked_responses = RankedResponsesModel(thread=thread_rid)
        
        if response:
            if THUMBS_UP in response.reactions:
                valid_reactions = len(response.reactions[THUMBS_UP])
                
                self.log.info(f"{valid_reactions} votes for community pick: {response.reactions[THUMBS_UP]}")
                
                if valid_reactions > ranked_responses.community_voted.ranking:
                    ranked_responses.community_voted.response = kobj.rid
                    ranked_responses.community_voted.ranking = valid_reactions
                    self.log.info("New community voted")
                
            if SPORTS_MEDAL in response.reactions:
                valid_reactions = 0
                user_group_bundle = self.effector.deref(
                    rid=self.config.response_ranking.staff_user_group, 
                    use_network=True
                )
                
                if user_group_bundle:
                    staff_user_group = user_group_bundle.contents
                    staff_users = staff_user_group.get("users", [])
                    
                    # only count reacters which belong to the staff user group
                    for reacter in response.reactions[SPORTS_MEDAL]:
                        if reacter.user_id in staff_users:
                            valid_reactions += 1
                            
                if valid_reactions > ranked_responses.staff_pick.ranking:
                    self.log.info("New staff pick")
                    ranked_responses.staff_pick.response = kobj.rid
                    ranked_responses.staff_pick.ranking = valid_reactions
                
            if CHECK_MARK in response.reactions:
                valid_reactions = 0
                thread_bundle = self.effector.deref(thread_rid, use_network=True)
                
                if thread_bundle:
                    thread = thread_bundle.validate_contents(AskCoreThreadModel)
                    
                    # only valid reactions are from the original thread asker
                    for reacter in response.reactions[CHECK_MARK]:
                        if reacter == thread.asker:
                            valid_reactions += 1
                
                if valid_reactions > ranked_responses.accepted_answer.ranking:
                    self.log.info("New accepted answer")
                    ranked_responses.accepted_answer.response = kobj.rid
                    ranked_responses.accepted_answer.ranking = valid_reactions
            
        self.kobj_queue.push(bundle=Bundle.generate(
            rid=ranked_responses_rid,
            contents=ranked_responses.model_dump()
        ))