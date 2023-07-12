from vkbottle.bot import Message
from vkbottle.dispatch.rules import ABCRule
from data import db_session
from data.admins import Admins


class MessageFromGroupChat(ABCRule[Message]):
    def __init__(self, chat_id):
        self.chat_id = chat_id

    async def check(self, message: Message):
        return message.chat_id == self.chat_id


class OnlySuperAdmins(ABCRule[Message]):
    async def check(self, message: Message):
        db_sess = db_session.create_session()
        admins = db_sess.query(Admins).all()
        for admin in admins:
            if admin.login == str(message.from_id) and admin.permission == "super":
                return True
        return False


class OnlyAdmins(ABCRule[Message]):
    async def check(self, message: Message):
        db_sess = db_session.create_session()
        admins = db_sess.query(Admins).all()
        for admin in admins:
            if admin.login == str(message.from_id):
                return True
        return False
