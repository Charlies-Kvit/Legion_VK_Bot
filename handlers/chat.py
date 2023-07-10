from vkbottle.bot import BotLabeler, Message, rules
from vkbottle_types.objects import MessagesConversation


class ChatInfoRule(rules.ABCRule[Message]):
    async def check(self, message: Message):
        chats_info = await message.ctx_api.messages.get_conversations_by_id(message.peer_id)
        return {"chat": chats_info.items[0]}


chat_labeler = BotLabeler()
chat_labeler.vbml_ignore_case = True
chat_labeler.auto_rules = [rules.PeerRule(from_chat=True), ChatInfoRule()]


