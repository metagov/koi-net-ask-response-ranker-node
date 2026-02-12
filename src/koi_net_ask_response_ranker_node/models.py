from pydantic import BaseModel, Field
from rid_lib.types import SlackMessage, SlackUser
from .rid_types import AskCoreResponse, AskCoreThread


class AskCoreResponseModel(BaseModel):
    author: SlackUser
    content: str
    original_msg: SlackMessage
    thread: AskCoreThread
    
    reactions: dict[str, list[SlackUser]] = Field(default_factory=dict)

class RankedResponsesModel(BaseModel):
    thread: AskCoreThread
    community_voted: AskCoreResponse | None = None # 👍 :+1
    metagov_staff_pick: AskCoreResponse | None = None# 🏅 :sports_medal
    accepted_answer: AskCoreResponse | None = None # ✅ :white_check_mark
    
    
