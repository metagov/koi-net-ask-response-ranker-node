from dataclasses import dataclass, field

from rid_lib.ext import Bundle
from koi_net.components.interfaces import KnowledgeHandler, HandlerType
from koi_net.components import Cache, Effector, KobjQueue
from koi_net.protocol import EventType, KnowledgeObject
from rid_lib.types import SlackUser
from slack_bolt import App

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
    slack_app: App
    bot_user: SlackUser = field(init=False, default="")
    
    handler_type = HandlerType.Network
    rid_types = (AskCoreResponse,)
    
    def user_is_staff(self, user: SlackUser) -> bool:
        user_group_bundle = self.effector.deref(
            rid=self.config.response_ranking.staff_user_group, 
            use_network=True
        )
        
        if user_group_bundle:
            staff_user_group = user_group_bundle.contents
            staff_users = staff_user_group.get("users", [])
            
            return user.user_id in staff_users
        return False
        
    def user_is_thread_author(self, user: SlackUser, response: AskCoreResponseModel):
        thread_bundle = self.effector.deref(response.thread, use_network=True)
        
        if thread_bundle:
            thread = thread_bundle.validate_contents(AskCoreThreadModel)
            
            return user == thread.asker
        return False
    
    def send_vote_feedback(self, reaction_delta_set, response):
        for emoji, user, added in reaction_delta_set:
            msg = None
            if emoji.startswith(THUMBS_UP):
                if added:
                    msg = f"Your :{THUMBS_UP}: vote has been counted!"
                else:
                    msg = f"Successively removed your :{THUMBS_UP}: vote"
                    
            elif emoji == SPORTS_MEDAL:
                if self.user_is_staff(user):
                    if added:
                        msg = f"Your :{SPORTS_MEDAL}: vote has been counted!"
                    else:
                        msg = f"Successively removed your :{SPORTS_MEDAL}: vote"
                elif added:
                    msg = f"Sorry, only staff members can vote :{SPORTS_MEDAL}:"
            
            elif emoji == CHECK_MARK:
                if self.user_is_thread_author(user, response):
                    if added:
                        msg = f"Your :{CHECK_MARK}: vote has been counted!"
                    else:
                        msg = f"Successively removed your :{CHECK_MARK}: vote"
                elif added:
                    msg = f"Sorry, only the thread author can vote :{CHECK_MARK}:"
            
            elif added:
                msg = f"Only :{THUMBS_UP}:, :{SPORTS_MEDAL}:, and :{CHECK_MARK}: are valid reaction votes"
            
            if msg is None:
                continue
            
            self.slack_app.client.chat_postEphemeral(
                channel=response.thread.channel_id,
                thread_ts=response.thread.ts,
                user=user.user_id,
                text=msg
            )
            
    def compute_rankings(self, thread: AskCoreThread, curr_response_bundle: Bundle):
        rankings = {}
        for rid in (*self.cache.list_rids(rid_types=(AskCoreResponse,)), curr_response_bundle.rid):
            bundle = self.cache.read(rid)
            if bundle:
                response = bundle.validate_contents(AskCoreResponseModel)
            elif rid == curr_response_bundle.rid:
                response = curr_response_bundle.validate_contents(AskCoreResponseModel)
            else:
                continue
            
            if response.author in self.config.response_ranking.ignored_response_authors:
                continue

            if response.thread != thread:
                continue
            
            reaction_counts = {
                THUMBS_UP: 0,
                SPORTS_MEDAL: 0,
                CHECK_MARK: 0
            }
            
            for emoji, users in response.reactions.items():
                if emoji.startswith(THUMBS_UP):
                    reaction_counts[THUMBS_UP] += len(users)
                elif emoji == SPORTS_MEDAL:
                    for user in users:
                        if self.user_is_staff(user):
                            reaction_counts[SPORTS_MEDAL] += 1
                elif emoji == CHECK_MARK:
                    for user in users:
                        if self.user_is_thread_author(user, response):
                            reaction_counts[CHECK_MARK] += 1
            rankings[rid] = reaction_counts
        return rankings
    
    def start(self):
        resp = self.slack_app.client.auth_test()
        self.bot_user = SlackUser(
            team_id=resp["team_id"],
            user_id=resp["user_id"]
        )
        
        if self.bot_user not in self.config.response_ranking.ignored_response_authors:
            self.config.response_ranking.ignored_response_authors.append(self.bot_user)
            self.config.save_to_yaml()

    def handle(self, kobj: KnowledgeObject):
        response = kobj.bundle.validate_contents(AskCoreResponseModel)
        
        if response.author in self.config.response_ranking.ignored_response_authors:
            self.log.info("Skipping response from ignored author")
            return
        
        ranked_responses_rid = AskRankedResponses(
            team_id=response.thread.team_id,
            channel_id=response.thread.channel_id,
            ts=response.thread.ts
        )
        
        if kobj.normalized_event_type == EventType.NEW:
            added = {(emoji, user) for emoji, users in response.reactions.items() for user in users}
            removed = set()
            
            if not added:
                return
            
        elif kobj.normalized_event_type == EventType.UPDATE:
            prev_response = kobj.prev_bundle.validate_contents(AskCoreResponseModel)

            prev_pairs = {(emoji, user) for emoji, users in prev_response.reactions.items() for user in users}
            curr_pairs = {(emoji, user) for emoji, users in response.reactions.items() for user in users}

            added = curr_pairs - prev_pairs
            removed = prev_pairs - curr_pairs

            if not added and not removed:
                return

        else:
            return
        
        # third value in tuple: True = added, False = removed
        reaction_delta_set = {(*t, t in added) for t in added | removed}
        self.send_vote_feedback(reaction_delta_set, response)
        
        bundle = self.cache.read(ranked_responses_rid)
        if bundle:
            ranked_responses = bundle.validate_contents(RankedResponsesModel)
        else:
            ranked_responses = RankedResponsesModel(thread=response.thread)
        
        
        response_rankings = self.compute_rankings(response.thread, kobj.bundle)
        
        def compute_max(rankings, emoji):
            max_response = max(rankings.items(), key=lambda t: t[1][emoji])
            return max_response[0], max_response[1][emoji]

        community_voted = compute_max(response_rankings, THUMBS_UP)
        staff_pick = compute_max(response_rankings, SPORTS_MEDAL)
        accepted_answer = compute_max(response_rankings, CHECK_MARK)
        
        self.log.info(f"COMMUNITY_VOTED: {community_voted}")
        self.log.info(f"STAFF_PICK: {staff_pick}")
        self.log.info(f"ACCEPTED_ANSWER: {accepted_answer}")

        if community_voted[1] > 0:
            ranked_responses.community_voted.response, ranked_responses.community_voted.ranking = community_voted
        else:
            ranked_responses.community_voted.response = None
            ranked_responses.community_voted.ranking = 0
        
        if staff_pick[1] > 0:
            ranked_responses.staff_pick.response, ranked_responses.staff_pick.ranking = staff_pick
        else:
            ranked_responses.staff_pick.response = None
            ranked_responses.staff_pick.ranking = 0
        
        if accepted_answer[1] > 0:
            ranked_responses.accepted_answer.response, ranked_responses.accepted_answer.ranking = accepted_answer
        else:
            ranked_responses.accepted_answer.response = None
            ranked_responses.accepted_answer.ranking = 0
        
        self.kobj_queue.push(bundle=Bundle.generate(
            rid=ranked_responses_rid,
            contents=ranked_responses.model_dump()
        ))