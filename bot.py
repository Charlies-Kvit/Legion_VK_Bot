from other_functions import change_loyalty, check_time, check_warning_time
from data import db_session
from data.user import User
from data.admins import Admins
from vkbottle import Bot, PhotoMessageUploader
from vkbottle.bot import Message
from handlers.custom_rules import MessageFromGroupChat, OnlySuperAdmins, OnlyAdmins
from config import api, state_dispenser, labeler, REPORTS_CHAT_ID, HOUR, MINUTES

bot = Bot(
    api=api,
    labeler=labeler,
    state_dispenser=state_dispenser
)
photo_uploader = PhotoMessageUploader(bot.api)


@bot.on.chat_message(MessageFromGroupChat(REPORTS_CHAT_ID), action=["chat_invite_user", "chat_invite_user_by_link"])
async def new_user(message: Message):
    users_info = await bot.api.users.get(message.action.member_id)
    db_sess = db_session.create_session()
    user = User(
        login=users_info[0].id
    )
    db_sess.add(user)
    db_sess.commit()
    db_sess.close()
    await message.answer(f"Пользователь {users_info[0].first_name} добавлен в бд")


@bot.on.chat_message(MessageFromGroupChat(REPORTS_CHAT_ID), action=['chat_kick_user'])
async def delete_user(message: Message):
    users_info = await bot.api.users.get(message.action.member_id)
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.login == users_info[0].id).first()
    db_sess.delete(user)
    db_sess.commit()
    db_sess.close()
    await message.answer(f"Пользователь {users_info[0].first_name} удален из базы данных")


@bot.on.chat_message(text=['.отпуск <user> <days>', '.отпуск'])
async def take_vacation(message: Message, user=None, days=None):
    if user is None or days is None:
        await message.answer("Используйте следующий синтаксис: .отпуск <user> <days>\n"
                             "То есть например следующая команда: .отпуск @user 10 даст отпуск юзеру на 10 дней")
        return
    user_id = int(user[3:user.find("|")])
    user_info = await bot.api.users.get(user_id)
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.login == user_info[0].id).first()
    user.vacation = int(days)
    db_sess.commit()
    db_sess.close()
    await message.answer(f"Пользователь {user_info[0].first_name} получил отпуск: {days} дней(день), не знаю короче")


@bot.on.chat_message(OnlyAdmins(), text=['.отнять отпуск <user>', '.отнять отпуск'])
async def pick_up_vacation(message: Message, user=None):
    if user is None:
        await message.answer("Используйте следующий синтаксис, что бы аннулировать отпуск: .отнять отпуск <user>, \n"
                             "например .отнять отпуск @user аннулирует отпуск у пользователя user")
        return
    db_sess = db_session.create_session()
    user_id = int(user[3:user.find("|")])
    user_info = await bot.api.users.get(user_id)
    user = db_sess.query(User).filter(User.login == user_info[0].id).first()
    if not user:
        await message.answer("Такой пользователь не найден в бд группы")
        db_sess.close()
        return
    if user.vacation == 0:
        db_sess.close()
        await message.answer("У этого пользователя и так нет отпуска(дайте отпуск мне хотяб, плиз)")
        return
    user.vacation = 0
    db_sess.commit()
    db_sess.close()
    await message.answer(f"Отпуск у {user_info[0].first_name} успешно отнят(сука, за что?)")


@bot.loop_wrapper.interval(minutes=5)
async def auto_minus_loyalty():
    if check_time():
        db_sess = db_session.create_session()
        users = db_sess.query(User).all()
        for user in users:
            if user.vacation != 0:
                user.vacation -= 1
                continue
            user.loyalty -= 1
            if user.reports_count == 0:
                user.unemployed_days += 1
                if user.loyalty == -8:
                    user.warning_user = True
            else:
                user.reports_count = 0
                user.unemployed_days = 0
        db_sess.commit()
        db_sess.close()


@bot.loop_wrapper.interval(minutes=5)
async def user_warning():
    if check_warning_time():
        db_sess = db_session.create_session()
        warning_users = db_sess.query(User).filter(User.warning_user is True)
        for user in warning_users:
            await bot.api.messages.send(user_id=user.login, random_id=0, message="Внимание! Уважаемый пользователь, вам"
                                                                                 "нужно приступить к работе, иначе "
                                                                                 "через"
                                                                                 " два дня вы будете изгнаны автоматом,"
                                                                                 " с уважением,\n legion_as(Легион)")
            user.warning_user = False
        db_sess.commit()
        db_sess.close()


@bot.on.chat_message(OnlySuperAdmins(), text=['/BD'])
async def get_data_bd(message: Message):
    db_sess = db_session.create_session()
    answer = ['__users__']
    users = db_sess.query(User).all()
    db_sess.close()
    for user in users:
        string = f"{user.login}, {user.loyalty}, {user.unemployed_days}, {user.vacation}"
        answer.append(string)
    await message.answer('\n'.join(answer))


@bot.on.chat_message(OnlySuperAdmins(), text=['.добавить админа <user>', '.добавить админа'])
async def add_admin(message: Message, user=None):
    if user is None:
        await message.answer("Для добавления админа используйте .добавить админа @user")
    else:
        user_id = int(user[3:user.find("|")])
        user_info = await bot.api.users.get(user_id)
        db_sess = db_session.create_session()
        admins = db_sess.query(Admins).all()
        for admin in admins:
            if admin.login == str(user_id):
                db_sess.close()
                await message.answer(f"Пользователь {user_info[0].first_name} уже есть в базе данных админов")
                return
        admin = Admins(login=user_id, permission="not super")
        db_sess.add(admin)
        db_sess.commit()
        db_sess.close()
        await message.answer(f"Пользователь {user_info[0].first_name} добавлен в список админов")


@bot.on.chat_message(OnlySuperAdmins(), text=['.удалить админа <user>', '.удалить админа'])
async def remove_admin(message: Message, user=None):
    if user is None:
        await message.answer("Для удаления пользователя из бд админов используйте .удалить админа @user")
    else:
        user_id = user[3:user.find("|")]
        user_info = await bot.api.users.get(user_id)
        db_sess = db_session.create_session()
        admin = db_sess.query(Admins).filter(Admins.login == user_id).first()
        if not admin:
            await message.answer(f"Пользователь {user_info[0].first_name} не найден в базе данных админов")
            db_sess.close()
            return
        db_sess.delete(admin)
        db_sess.commit()
        db_sess.close()
        await message.answer(f"Пользователь {user_info[0].first_name} удален из списка админов")


@bot.on.chat_message(OnlyAdmins(), text=['.админы список'])
async def get_admin_list(message: Message):
    db_sess = db_session.create_session()
    admins = db_sess.query(Admins).all()
    answer = ['Список админов:']
    for num, admin in enumerate(admins):
        admin_info = await bot.api.users.get(admin.login)
        answer.append(f"{num + 1}. {admin_info[0].first_name} {admin_info[0].last_name}")
    db_sess.close()
    await message.answer('\n'.join(answer))


@bot.on.chat_message(OnlyAdmins(), text=['.хелп'])
async def get_help(message: Message):
    await message.answer("""Вот какие команды есть в боте:\n
    .отпуск - дает отпуск юзеру\n
    .отнять отпуск - отнимает отпуск\n
    .добавить админа - добавляет админа из бд(только для админов с правами супер)\n
    .удалить админа - удаляет админа из бд(только для админов с правами супер)\n
    .админы список - выдает список админов\n
    .изменить лояльность, .изм, .лоял, .лояльность - позваляет менять лояльность юзеру\n
    .топ - выводит топ юзеров по лояльности\n
    .юзер - выводит инфу о конкретном юзере(Если хотите узнать о конкретном пользователе, то используйте следующий
    синтаксис: .юзер <user>, иначе вы получите инфу о себе)\n
    В остальных же случаях вы можете подробнее узнать о команде введя ее без параметров)""")


@bot.on.chat_message(OnlyAdmins(), text=['.изменить лояльность <user> <loyalty>', '.изм <user> <loyalty>',
                                         '.лоял <user> <loyalty>', '.лояльность <user> <loyalty>',
                                         '.изменить лояльность', '.изм'])
async def change_loyalty_user(message: Message, user=None, loyalty=None):
    if user is None or loyalty is None:
        await message.answer(
            'Для добавления пользователю очков лояльности используйте команду: .изменить лояльность @user loyalty\n'
            'Например: .изменить лояльность @user +10, данная команда прибавит 10 очков лояльности юзеру')
        return
    db_sess = db_session.create_session()
    user_id = int(user[3:user.find("|")])
    user = db_sess.query(User).filter(User.login == user_id).first()
    final_loyalty = change_loyalty(loyalty, user.loyalty)
    if type(final_loyalty) == int:
        user.loyalty = final_loyalty
        db_sess.commit()
        user_info = await bot.api.users.get(user_id)
        await message.answer(f"Очки лояльности у пользователя {user_info[0].first_name} после изменения: "
                             f"{final_loyalty}")
    else:
        await message.answer(
            'Для добавления пользователю очков лояльности используйте команду: .изменить лояльность @user loyalty\n'
            'Например: .изменить лояльность @user +10, данная команда прибавит 10 очков лояльности юзеру')
    db_sess.close()


@bot.on.chat_message(OnlyAdmins(), text=['/топ', '.топ'])
async def get_top_users(message: Message):
    db_sess = db_session.create_session()
    users_info = db_sess.query(User).all()
    users = {user.login: user.loyalty for user in users_info}
    sorted_users = dict(sorted(users.items(), key=lambda item: item[1], reverse=True))
    users_id = sorted_users.keys()
    db_sess.close()
    answer = ['Топ по очкам лояльности:']
    for num, key in enumerate(users_id):
        user_name = await bot.api.users.get(key)
        answer.append(f"{num + 1}. {user_name[0].first_name}: {sorted_users[key]}")
    await message.answer('\n'.join(answer))


@bot.on.chat_message(MessageFromGroupChat(REPORTS_CHAT_ID))
async def get_report_message(message: Message):
    try:
        db_sess = db_session.create_session()
        if message.attachments[0].wall_reply.text:
            user = db_sess.query(User).filter(User.login == message.from_id)[0]
            user.loyalty += 1
            db_sess.commit()
            db_sess.close()
    except IndexError:
        db_sess.close()
        # await bot.api.messages.delete(peer_id=message.peer_id, message_ids=message_id, delete_for_all=True,
        #                              group_id=REPORTS_CHAT_ID)


@bot.on.chat_message(text=["/юзер <user>", ".юзер <user>", ".юзер", "/юзер"])
async def get_user_info(message: Message, user=None):
    if user is None:
        user_id = message.from_id
    else:
        user_id = int(user[3:user.find("|")])
    db_sess = db_session.create_session()
    user_info = db_sess.query(User).filter(User.login == user_id)[0]
    db_sess.close()
    answer = f"Дни неактива: {user_info.unemployed_days}\n" \
             f"Очки лояльности: {user_info.loyalty}\n" \
             f"Отпуск: {user_info.vacation}"
    await message.answer(answer)


@bot.on.chat_message(text=['чурбан', 'Чурбан'])
async def meme(message: Message):
    photo = await photo_uploader.upload(
        file_source="churman.jpg"
    )
    await message.answer("✅ На месте", attachment=photo)


@bot.on.chat_message()
async def leave(message: Message):
    session = db_session.create_session()
    session.close_all()
    print("all session close")


bot.run_forever()
