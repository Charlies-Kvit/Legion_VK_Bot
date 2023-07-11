import datetime
import asyncio
from data import db_session
from typing import Tuple
from data.user import User
from vkbottle import Bot
from vkbottle.bot import Message, BotLabeler, rules
from handlers.custom_rules import MessageFromGroupChat
from config import api, state_dispenser, labeler, REPORTS_CHAT_ID
from handlers import admin_labeler

labeler.load(admin_labeler)
bot = Bot(
    api=api,
    labeler=labeler,
    state_dispenser=state_dispenser
)


"""@bot.on.chat_message(action=["chat_invite_user", "chat_invite_user_by_link"])
async def new_user(message: Message):
    users_info = await bot.api.users.get(message.from_id)
    await message.answer(f"Hello, {users_info[0].first_name}")"""


def check_time():
    return datetime.datetime.now().hour == 23 and datetime.datetime.now().minute == 0


def minus_loyalty():
    if datetime.datetime.now().hour == 14:
        print("ok")


@bot.on.chat_message(MessageFromGroupChat(REPORTS_CHAT_ID))
async def get_report_message(message: Message):
    try:
        if message.attachments[0].wall_reply.text:
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.login == message.from_id)[0]
            user.loyalty += 1
            db_sess.commit()
            db_sess.close()
    except IndexError:
        pass
        # await bot.api.messages.delete(peer_id=message.peer_id, message_ids=message_id, delete_for_all=True,
        #                              group_id=REPORTS_CHAT_ID)


@bot.on.chat_message(text=["/юзер <user>", ".юзер <user>", ".юзер", "/юзер"])
async def get_user_info(message: Message, user=None):
    if user is None:
        answer = 'используйте .юзер @юзер или /юзер @юзер'
    else:
        user_id = int(user[3:user.find("|")])
        db_sess = db_session.create_session()
        user_info = db_sess.query(User).filter(User.login == user_id)[0]
        db_sess.close()
        answer = f"Безработные дни: {user_info.unemployed_days}\n" \
                 f"Очки лояльности: {user_info.loyalty}\n" \
                 f"Отпуск: {user_info.vacation}"
    await message.answer(answer)


@bot.on.chat_message()
async def add_delete_user(message: Message):

    users_info = await bot.api.users.get(message.from_id)
    db_sess = db_session.create_session()
    users_data = db_sess.query(User).all()
    users = {user.login: user.to_dict(only=("loyalty", "unemployed_days", "vacation")) for user in users_data}
    if users_info[0].id not in users.keys():
        user = User(
            login=users_info[0].id
        )
        db_sess.add(user)
        db_sess.commit()
        db_sess.close()
        await message.answer(users)
    try:
        if message.action.type.value == "chat_kick_user":
            users_info = await bot.api.users.get(message.action.member_id)
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.login == users_info[0].id)[0]
            db_sess.delete(user)
            db_sess.commit()
            db_sess.close()
            await message.answer(f"Пользователь {users_info[0].first_name} удален из базы данных")
    except Exception:
        pass

"""@bot.on.chat_message(action='CHAT_KICK_USER')
async def user_left(message: MessageEvent):
    await message.send_message('goodby')
    print("KIKED")"""
bot.run_forever()
