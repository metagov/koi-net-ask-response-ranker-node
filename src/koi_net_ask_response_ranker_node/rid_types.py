from rid_lib.types import SlackMessage


class AskCoreThread(SlackMessage):
    namespace = "ask-core.thread"
    
class AskCoreResponse(SlackMessage):
    namespace = "ask-core.response"

class AskRankedResponses(SlackMessage):
    namespace = "ask.ranked_responses"