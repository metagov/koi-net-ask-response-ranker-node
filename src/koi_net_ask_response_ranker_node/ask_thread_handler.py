from dataclasses import dataclass

from koi_net.components import Cache, KobjQueue
from koi_net.components.interfaces import KnowledgeHandler, HandlerType
from koi_net.protocol.knowledge_object import KnowledgeObject
from rid_lib.ext import Bundle
from slack_bolt import App

from .models import RankedResponsesModel
from .rid_types import AskCoreThread, AskRankedResponses


@dataclass
class AskThreadHandler(KnowledgeHandler):
    slack_app: App
    cache: Cache
    kobj_queue: KobjQueue
    
    handler_type = HandlerType.Network
    rid_types = (AskCoreThread,)
    
    def ensure_bot_in_channel(self, channel_id: str):
        try:
            result = self.slack_app.client.conversations_info(channel=channel_id)
            channel = result["channel"]
            
            if not channel.get("is_member", False):
                self.slack_app.client.conversations_join(channel=channel_id)
                self.log.info(f"Joined channel #{channel_id}")
        
        except Exception as e:
            self.log.error(f"Unhandled exception joining channel: {e}")
    
    def handle(self, kobj: KnowledgeObject):
        thread: AskCoreThread = kobj.rid
        
        ranked_responses_rid = AskRankedResponses(
            team_id=thread.team_id,
            channel_id=thread.channel_id,
            ts=thread.ts
        )
        
        if not self.cache.read(ranked_responses_rid):
            self.kobj_queue.push(bundle=Bundle.generate(
                rid=ranked_responses_rid,
                contents=RankedResponsesModel(thread=thread).model_dump()
            ))
        
        self.ensure_bot_in_channel(channel_id=thread.channel_id)
        
        self.slack_app.client.chat_postMessage(
            channel=thread.channel_id,
            thread_ts=thread.ts,
            blocks=[{
                "type": "rich_text",
                "elements": [
                    {
                        "type": "rich_text_section",
                        "elements": [
                            {
                                "type": "text",
                                "text": "React to "
                            },
                            {
                                "type": "text",
                                "text": "other responses",
                                "style": {
                                    "bold": True
                                }
                            },
                            {
                                "type": "text",
                                "text": " to rank them!\n"
                            }
                        ]
                    },
                    {
                        "type": "rich_text_list",
                        "style": "bullet",
                        "indent": 0,
                        "border": 0,
                        "elements": [
                            {
                                "type": "rich_text_section",
                                "elements": [
                                    {
                                        "type": "text",
                                        "text": "Community Voted "
                                    },
                                    {
                                        "type": "emoji",
                                        "name": "+1",
                                        "unicode": "1f44d"
                                    },
                                    {
                                        "type": "text",
                                        "text": " - anyone can vote!"
                                    }
                                ]
                            },
                            {
                                "type": "rich_text_section",
                                "elements": [
                                    {
                                        "type": "text",
                                        "text": "Staff Pick "
                                    },
                                    {
                                        "type": "emoji",
                                        "name": "sports_medal",
                                        "unicode": "1f3c5"
                                    },
                                    {
                                        "type": "text",
                                        "text": " - only Metagov staff can vote"
                                    }
                                ]
                            },
                            {
                                "type": "rich_text_section",
                                "elements": [
                                    {
                                        "type": "text",
                                        "text": "Accepted Answer "
                                    },
                                    {
                                        "type": "emoji",
                                        "name": "white_check_mark",
                                        "unicode": "2705"
                                    },
                                    {
                                        "type": "text",
                                        "text": " - only thread author can vote"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }]
        )