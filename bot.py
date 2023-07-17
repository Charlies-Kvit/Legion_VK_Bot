import requests
import random
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


@bot.on.chat_message(OnlyAdmins(), text=['.удалить <user>', '.удалить'])
async def delete_user_bd(message: Message, user=None):
    if user is None:
        await message.answer(
            "Используйте следующий синтаксис: .удалить @user, то есть данная команда удалит из бд юзера")
        return
    user_id = int(user[3:user.find("|")])
    users_info = await bot.api.users.get(user_id)
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.login == users_info[0].id).first()
    if not user:
        db_sess.close()
        await message.answer('Пользователь в бд не найден')
        return
    db_sess.delete(user)
    db_sess.commit()
    db_sess.close()
    await message.answer(f"Пользователь {users_info[0].first_name} удален из базы данных")


@bot.on.chat_message(OnlyAdmins(), text=['.проверить бд'])
async def check_database(message: Message):
    users_in_chat = await bot.api.messages.get_conversation_members(peer_id="2000000004")
    users_id = [int(user.id) for user in users_in_chat.profiles]
    db_sess = db_session.create_session()
    users_from_bd = db_sess.query(User).all()
    for user in users_from_bd:
        if int(user.login) in users_id:
            continue
        db_sess.delete(user)
        user_info = await bot.api.users.get(user.login)
        await message.answer(f'Пользователь {user_info[0].first_name} {user_info[0].last_name} удален из бд')
    db_sess.commit()
    await message.answer("Из бд удалены все юзеры, не найденные в чате")


@bot.on.chat_message(OnlyAdmins(), text=['.отпуск <user> <days>', '.отпуск'])
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
    if days[-1] == '1' and int(days) != 11:
        answer = 'день'
    elif days[-1] in ['2', '3', '4']:
        answer = 'дня'
    else:
        answer = "дней"
    await message.answer(
        f"Пользователь {user_info[0].first_name} получил отпуск на {days} {answer}")


@bot.on.chat_message(OnlyAdmins(), text=['.отпуск список'])
async def get_list_vacation(message: Message):
    db_sess = db_session.create_session()
    users = db_sess.query(User).filter(User.vacation > 0)
    answer = ['Пользователи в отпуске:']
    for num, user in enumerate(users):
        user_info = await bot.api.users.get(user.login)
        answer.append(f"{num + 1}. @id{user.login}({user_info[0].first_name} {user_info[0].last_name}), осталось: "
                      f"{user.vacation} д.")
    db_sess.close()
    await message.answer('\n'.join(answer))


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
        await message.answer("У этого пользователя и так нет отпуска")
        return
    user.vacation = 0
    db_sess.commit()
    db_sess.close()
    await message.answer(f"Отпуск у {user_info[0].first_name} успешно аннулирован")


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
        await bot.api.messages.send(chat_id=0, random_id=0, message="Авто минус очков лояльности прошел успешно")
        db_sess.commit()
        db_sess.close()


@bot.loop_wrapper.interval(minutes=5)
async def user_warning():
    if check_warning_time():
        db_sess = db_session.create_session()
        warning_users = db_sess.query(User).filter(User.warning_user is True)
        for user in warning_users:
            user_info = await bot.api.users.get(user.login)
            first_name, last_name = user_info[0].first_name, user_info[0].last_name
            await bot.api.messages.send(chat_id=4, random_id=0, message=f"Внимание! Уважаемый @id{user.login}"
                                                                        f"({first_name} {last_name}), вам"
                                                                        "нужно приступить к работе, иначе "
                                                                        "через два дня вы будете изгнаны автоматом,"
                                                                        " с уважением,\n @legion_as(Легион)")
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


@bot.on.chat_message(text=['.инфо', '.о боте'])
async def get_info_about_bot(message: Message):
    await message.answer("Версия бота: Бета 1.0.0\n"
                         "Идея: Имя Фамилия\n"
                         "Разработчик: Глеб Бутович\n"
                         "Главный по поддержке хоста: Евгений Грущенко\n"
                         "Выражаю благодарность Тиомну, подсказывал тогда, когда я был невнимателен")


@bot.on.chat_message(OnlyAdmins(), text=['.хелп'])
async def get_help(message: Message):
    await message.answer("""Вот какие команды есть в боте:\n
    .отпуск - дает отпуск юзеру\n
    .отнять отпуск - отнимает отпуск\n
    .отпуск список - показывает\n
    .добавить админа - добавляет админа из бд(только для админов с правами супер)\n
    .удалить админа - удаляет админа из бд(только для админов с правами супер)\n
    .админы список - выдает список админов\n
    .изменить лояльность, .изм, .лоял, .лояльность - позваляет менять лояльность юзеру\n
    .рейтинг - выводит топ юзеров по лояльности\n
    .удалить - удаляет юзера из базы данных\n
    .проверить бд - удаляет всех из бд, кого нет в чате\n
    .регистрация - добавляет в бд всех, кого нет в бд, но есть в чате\n
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


@bot.on.chat_message(OnlyAdmins(), text=['/топ', '.рейтинг'])
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
        answer.append(f"{num + 1}. {user_name[0].first_name} {user_name[0].last_name}: {sorted_users[key]}")
    await message.answer('\n'.join(answer))


@bot.on.chat_message(MessageFromGroupChat(REPORTS_CHAT_ID))
async def get_report_message(message: Message):
    try:
        db_sess = db_session.create_session()
        if message.attachments[0].wall_reply:
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


@bot.on.chat_message(OnlyAdmins(), text=['чурбан', 'Чурбан'])
async def meme(message: Message):
    var = random.choice([0, 1])
    if var == 0:
        photo = await photo_uploader.upload(
            file_source="churman.jpg"
        )
        await message.answer("✅ На месте", attachment=photo)
    else:
        await message.answer("САМ ЧУРБАН")


@bot.on.chat_message(text=['.регистрация'])
async def registration(message: Message):
    db_sess = db_session.create_session()
    users = await bot.api.messages.get_conversation_members(peer_id=message.peer_id)
    users_list = [user.login for user in db_sess.query(User).all()]
    for user in users.profiles:
        if str(user.id) in users_list:
            continue
        user_new = User(login=user.id)
        db_sess.add(user_new)
    db_sess.commit()
    db_sess.close()
    await message.answer("Все пользователи успешно добавлены в бд)")


@bot.on.chat_message()
async def leave(message: Message):
    # await message.answer(message.chat_id)
    session = db_session.create_session()
    session.close_all()


if __name__ == '__main__':
    bot.run_forever()
