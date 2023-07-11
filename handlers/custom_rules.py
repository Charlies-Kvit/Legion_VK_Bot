from vkbottle.bot import Message
from vkbottle.dispatch.rules import ABCRule


class MessageFromGroupChat(ABCRule[Message]):
    def __init__(self, chat_id):
        self.chat_id = chat_id

    async def check(self, message: Message):
        return message.chat_id == self.chat_id
