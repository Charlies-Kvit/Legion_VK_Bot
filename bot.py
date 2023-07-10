from data import db_session
from data.user import User
from vkbottle import Bot, GroupEventType, UserEventType, ShowSnackbarEvent
from vkbottle.bot import Message, MessageEvent, rules
from config import api, state_dispenser, labeler, users
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


@bot.on.message()
async def new_user(message: Message):
    users_info = await bot.api.users.get(message.from_id)
    if users_info[0].id not in users.keys():
        db_sess = db_session.create_session()
        users[users_info[0].id] = {"loyalty": 1, "unemployed_days": 0, "vacation": 0}
        user = User(
            login=users_info[0].id
        )
        db_sess.add(user)
        db_sess.commit()
        db_sess.close()
        await message.answer(users)
    if message.action.type.value == "chat_kick_user":
        users_info = await bot.api.users.get(message.action.member_id)
        users.pop(users_info[0].id)
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.login == users_info[0].id)[0]
        db_sess.delete(user)
        db_sess.commit()
        db_sess.close()
        await message.answer(f"Пользователь {users_info[0].first_name} удален из бд")


"""@bot.on.chat_message(action='CHAT_KICK_USER')
async def user_left(message: MessageEvent):
    await message.send_message('goodby')
    print("KIKED")"""

bot.run_forever()
