import random
import asyncio
from vkreal import VkApi, VkBotLongPoll
from other_functions import change_loyalty, check_time, check_warning_time
from data import db_session
from data.user import User
from data.admins import Admins
from data.custom_rules import check_chat, check_admin, check_super_admin
from config import REPORTS_CHAT_ID, NORMAL_CHAT_ID, token, ranks, posts


# @bot.on.chat_message(MessageFromGroupChat(REPORTS_CHAT_ID), action=["chat_invite_user", "chat_invite_user_by_link"])
async def new_user(vk, event):
    if check_chat(event, NORMAL_CHAT_ID):
        users_info = await vk.users_get(user_ids=event['object']['message']['action']['member_id'])
        db_sess = db_session.create_session()
        user = User(
            login=users_info[0]['id']
        )
        db_sess.add(user)
        db_sess.commit()
        db_sess.close()
        await vk.messages_send(message=f"Пользователь {users_info[0]['first_name']} добавлен в бд",
                               random_id=0,
                               peer_id=event['object']['message']['peer_id'])


# @bot.on.chat_message(MessageFromGroupChat(REPORTS_CHAT_ID), action=['chat_kick_user'])
async def delete_user(vk, event):
    if check_chat(event, NORMAL_CHAT_ID):
        users_info = await vk.users_get(user_ids=event['object']['message']['action']['member_id'])
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.login == users_info[0]['id']).first()
        db_sess.delete(user)
        db_sess.commit()
        db_sess.close()
        await vk.messages_send(message=f"Пользователь {users_info[0]['first_name']} удален из базы данных",
                               random_id=0,
                               peer_id=event['object']['message']['peer_id'])


# @bot.on.chat_message(OnlyAdmins(), text=[".кик <user>", '.кик'])
async def kick_user(vk, event):
    data = event['object']['message']['text'].split()
    if len(data) == 1:
        await vk.messages_send(message="Используйте .кик @user для кика юзера из чата",
                               random_id=0,
                               peer_id=event['object']['message']['peer_id'])
        return
    user = data[-1]
    user_id = int(user[3:user.find("|")])
    for i in [2, 3]:
        await vk.messages_removeChatUser(chat_id=i, user_id=user_id)
    user_info = await vk.users_get(user_ids=user_id)
    await vk.messages_send(message=f'Пользователь {user_info[0]["first_name"]} {user_info[0]["last_name"]} выгнан из чата',
                           random_id=0,
                           peer_id=event['object']['message']['peer_id'])


# @bot.on.chat_message(OnlyAdmins(), text=['.удалить <user>', '.удалить'])
async def delete_user_bd(vk, event):
    data = event['object']['message']['text'].split()
    if len(data) == 1:
        await vk.messages_send(
            random_id=0,
            peer_id=event['object']['message']['peer_id'],
            message="Используйте следующий синтаксис: .удалить @user, то есть данная команда удалит из бд юзера")
        return
    user = data[-1]
    user_id = int(user[3:user.find("|")])
    users_info = await vk.users_get(user_ids=user_id)
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.login == users_info[0]['id']).first()
    if not user:
        db_sess.close()
        await vk.messages_send(message='Пользователь в бд не найден',
                               peer_id=event['object']['message']['peer_id'],
                               random_id=0)
        return
    db_sess.delete(user)
    db_sess.commit()
    db_sess.close()
    await vk.messages_send(message=f"Пользователь {users_info[0]['first_name']} удален из базы данных",
                           random_id=0,
                           peer_id=event['object']['message']['peer_id'])


# @bot.on.chat_message(OnlyAdmins(), text=['.проверить бд'])
async def check_database(vk, event):
    users_in_chat = await vk.messages_getConversationMembers(peer_id=event['object']['message']['peer_id'])
    users_id = [int(user['id']) for user in users_in_chat['profiles']]
    db_sess = db_session.create_session()
    users_from_bd = db_sess.query(User).all()
    answer = ['Из бд удалены:']
    for user in users_from_bd:
        if int(user.login) in users_id:
            continue
        db_sess.delete(user)
        user_info = await vk.users_get(user_ids=user.login)
        answer.append(f"-{user_info[0]['first_name']} {user_info[0]['last_name']}")
    db_sess.commit()
    await vk.messages_send(message='\n'.join(answer), random_id=0, peer_id=event['object']['message']['peer_id'])
    await vk.messages_send(message="Из бд удалены все юзеры, не найденные в чате",
                           random_id=0,
                           peer_id=event['object']['message']['peer_id'])


# @bot.on.chat_message(OnlyAdmins(), text=['.отпуск <user> <days>', '.отпуск'])
async def take_vacation(vk, event):
    data = event['object']['message']['text'].split()
    if len(data) != 3:
        await vk.messages_send(message="Используйте следующий синтаксис: .отпуск <user> <days>\n"
                             "То есть например следующая команда: .отпуск @user 10 даст отпуск юзеру на 10 дней",
                               peer_id=event['object']['message']['peer_id'],
                               random_id=0)
        return
    user = data[1]
    days = data[-1]
    user_id = int(user[3:user.find("|")])
    user_info = await vk.users_get(user_ids=user_id)
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.login == user_info[0]['id']).first()
    user.vacation = int(days)
    user.unemployed_days = 0
    db_sess.commit()
    db_sess.close()
    if days[-1] == '1' and int(days) != 11:
        answer = 'день'
    elif days[-1] in ['2', '3', '4']:
        answer = 'дня'
    else:
        answer = "дней"
    await vk.messages_send(
        message=f"Пользователь {user_info[0]['first_name']} получил отпуск на {days} {answer}",
        peer_id=event['object']['message']['peer_id'],
        random_id=0)


# @bot.on.chat_message(OnlyAdmins(), text=['.неактивы'])
async def get_list_not_active(vk, event):
    db_sess = db_session.create_session()
    users_info = db_sess.query(User).filter(User.unemployed_days != 0)
    users = {user.login: user.unemployed_days for user in users_info}
    sorted_users = dict(sorted(users.items(), key=lambda item: item[1], reverse=True))
    users_id = sorted_users.keys()
    answer = ['Неактивные пользователи:']
    for num, key in enumerate(users_id):
        user_info = await vk.users_get(user_ids=key)
        answer.append(f"{num + 1}. Пользователь [https://vk.com/id{user_info[0]['id']}|{user_info[0]['first_name']} {user_info[0]['last_name']}] "
                      f"неактивен уже {sorted_users[key]} д.")
    db_sess.close()
    if len(answer) != 1:
        await vk.messages_send(message='\n'.join(answer), random_id=0, peer_id=event['object']['message']['peer_id'])
    else:
        await vk.messages_send(message="Неактивные пользователи отсутствуют", random_id=0, peer_id=event['object']
        ['message']['peer_id'])


# @bot.on.chat_message(OnlyAdmins(), text=['.отпуски'])
async def get_list_vacation(vk, event):
    db_sess = db_session.create_session()
    users = db_sess.query(User).filter(User.vacation > 0)
    answer = ['Пользователи в отпуске:']
    for num, user in enumerate(users):
        user_info = await vk.users_get(user_ids=user.login)
        answer.append(f"{num + 1}. @id{user.login}({user_info[0]['first_name']} {user_info[0]['last_name']}), осталось: "
                      f"{user.vacation} д.")
    db_sess.close()
    await vk.messages_send(message='\n'.join(answer), random_id=0, peer_id=event['object']['message']['peer_id'])


#  @bot.on.chat_message(OnlyAdmins(), text=['.отнять отпуск <user>', '.отнять отпуск'])
async def pick_up_vacation(vk, event):
    data = event['object']['message']['text'].split()
    if len(data) == 2:
        await vk.messages_send(message="Используйте следующий синтаксис, что бы аннулировать отпуск: .отнять отпуск <user>, \n"
                             "например .отнять отпуск @user аннулирует отпуск у пользователя user",
                               random_id=0,
                               peer_id=event['object']['message']['peer_id'])
        return
    db_sess = db_session.create_session()
    user = data[-1]
    user_id = int(user[3:user.find("|")])
    user_info = await vk.users_get(user_ids=user_id)
    user = db_sess.query(User).filter(User.login == user_info[0]['id']).first()
    if not user:
        await vk.messages_send(message="Такой пользователь не найден в бд группы",
                               random_id=0,
                               peer_id=event['object']['message']['peer_id'])
        db_sess.close()
        return
    if user.vacation == 0:
        db_sess.close()
        await vk.messages_send(message="У этого пользователя и так нет отпуска",
                               random_id=0,
                               peer_id=event['object']['message']['peer_id'])
        return
    user.vacation = 0
    db_sess.commit()
    db_sess.close()
    await vk.messages_send(message=f"Отпуск у {user_info[0]['first_name']} успешно аннулирован",
                           random_id=0,
                           peer_id=event['object']['message']['peer_id'])


async def auto_minus_loyalty(vk):
    if check_time():
        db_sess = db_session.create_session()
        users = db_sess.query(User).all()
        for user in users:
            if user.vacation != 0:
                user.vacation -= 1
                continue
            user.loyalty -= user.unemployed_days
            if user.unemployed_days == 7:
                user_id = int(user[3:user.find("|")])
                user_info = await vk.users_get(user_ids=user_id)
                await vk.messages_send(chat_id=0, random_id=0, peer_id=2000000001,
                                       message=f'Пользователь {user_info[0]["first_name"]} '
                                               f'{user_info[0]["last_name"]} должен быть выгнан из Легиона')
                continue
            if user.reports_count == 0:
                user.unemployed_days += 1
                if user.unemployed_days == 3 or user.unemployed_days == 5:
                    user.warning_user = True
            else:
                if user.reports_count < user.duty:
                    user.loyalty -= 1
                user.reports_count = 0
        await vk.messages_send(chat_id=0, random_id=0, message="Авто минус очков лояльности прошел успешно",
                               peer_id=2000000001)
        db_sess.commit()
        db_sess.close()
    await asyncio.sleep(300)
    loop.create_task(auto_minus_loyalty(vk))


async def user_warning(vk):
    if check_warning_time():
        db_sess = db_session.create_session()
        warning_users = db_sess.query(User).filter(User.warning_user is True)
        for user in warning_users:
            user_info = await vk.users_get(user_ids=user.login)
            first_name, last_name = user_info[0]['first_name'], user_info[0]['last_name']
            await vk.messages_send(chat_id=4, random_id=0, message=f"Внимание! Уважаемый @id{user.login}"
                                                                        f"({first_name} {last_name}), вам"
                                                                        "нужно приступить к работе, иначе "
                                                                        "совсем скоро вы будете изгнаны из Легиона,"
                                                                        " с уважением,\n @legion_as(Легион)",
                                        peer_id=2000000005)
            user.warning_user = False
        db_sess.commit()
        db_sess.close()
    await asyncio.sleep(300)
    loop.create_task(user_warning(vk))


async def give_post(vk, event):
    data = event['object']['message']['text'].split()
    if len(data) != 4:
        await vk.messages_send(peer_id=event['object']['message']['peer_id'], random_id=0,
                               message="Для того, чтоб дать должность, напишите .дать дол @user название должности, "
                                       "например команда .дать дол @user [M]Наставник даст звание наставник, если у "
                                       "пользователя есть нужный ранг")
    else:
        post = data[-1]
        if post not in post:
            await vk.messages_send(peer_id=event['object']['message']['peer_id'], random_id=0,
                                   message="Такой должности не существует или же вы не написали точь в точь, с"
                                           " должностями можно ознакомиться, написав команду .должности")
        user = data[-2]
        user_id = int(user[3:user.find("|")])
        user_info = await vk.users_get(user_ids = user_id)
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.login == user_id).first()
        if post in posts[1:3] and user.rank >= 7:
            user.post = posts.index(post)
        elif post in posts[3:] and user.rank >=8:
            user.post = posts.index(post)
        else:
            db_sess.close()
            if post in posts[1:3]:
                i = 7
            else:
                i = 8
            await vk.messages_send(peer_id=event['object']['message']['peer_id'], random_id=0,
                                   message=f"Пользователь {user_info[0]['first_name']} {user_info[0]['last_name']} "
                                           f"не может получить следующую должность: {post}, так как нужен ранг: "
                                           f"{ranks[i]}, а ранг пользователя: {ranks[user.rank]}")
            return
        db_sess.commit()
        db_sess.close()
        await vk.messages_send(peer_id=event['object']['message']['peer_id'], random_id=0,
                               message=f"Пользователь {user_info[0]['first_name']} {user_info[0]['last_name']} "
                                       f"получил должность: {post}")


async def pick_up_post(vk, event):
    data = event['object']['message']['text'].split()
    if len(data) != 3:
        await vk.messages_send(peer_id=event['object']['message']['peer_id'], random_id=0,
                               message="Чтобы аннулировать должность, используйте .забрать дол @user")
    else:
        user = data[-1]
        user_id = int(user[3:user.find("|")])
        user_info = await vk.users_get(user_ids=user_id)
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.login == user_id).first()
        if user.post == 0:
            await vk.messages_send(peer_id=event['object']['message']['peer_id'], random_id=0,
                                   message=f"Пользователь {user_info[0]['first_name']} {user_info[0]['last_name']} "
                                           f"итак рядовой, разжалование невозможно")
            return
        last_post = user.post
        user.post = 0
        db_sess.commit()
        db_sess.close()
        await vk.messages_send(peer_id=event['object']['message']['peer_id'], random_id=0,
                               message=f"Пользователь {user_info[0]['first_name']} {user_info[0]['last_name']} "
                                       f"разжалован с должности: {posts[last_post]}")


async def add_admin(vk, event):
    data = event['object']['message']['text'].split()
    if len(data) == 2:
        await vk.messages_send(peer_id=event['object']['message']['peer_id'],
                               message="Для добавления админа используйте .добавить админа @user",
                               random_id=0)
    else:
        user = data[-1]
        user_id = int(user[3:user.find("|")])
        user_info = await vk.users_get(user_ids=user_id)
        db_sess = db_session.create_session()
        admins = db_sess.query(Admins).all()
        for admin in admins:
            if admin.login == str(user_id):
                db_sess.close()
                await vk.messages_send(peer_id=event['object']['message']['peer_id'],
                                       message=f"Пользователь {user_info[0]['first_name']} уже есть в базе данных админов",
                                       random_id=0)
                return
        admin = Admins(login=user_id, permission="not super")
        db_sess.add(admin)
        db_sess.commit()
        db_sess.close()
        await vk.messages_send(message=f"Пользователь {user_info[0]['first_name']} добавлен в список админов",
                               random_id=0,
                               peer_id=event['object']['message']['peer_id'])


async def give_all_you_need(vk, event):
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()
    for user in users:
        if user.rank is None:
            user = get_rank(user)
            user.post = 0
            db_sess.commit()
    db_sess.close()
    await vk.messages_send(random_id=0, peer_id=event['object']['message']['peer_id'],
                           message="Все юзеры получили ранги")

# @bot.on.chat_message(OnlySuperAdmins(), text=['.удалить админа <user>', '.удалить админа'])
async def remove_admin(vk, event):
    data = event['object']['message']['text'].split()
    if len(data) == 2:
        await vk.messages_send(message="Для удаления пользователя из бд админов используйте .удалить админа @user",
                               random_id=0,
                               peer_id=event['object']['message']['peer_id'])
    else:
        user = data[-1]
        user_id = user[3:user.find("|")]
        user_info = await vk.users_get(user_ids=user_id)
        db_sess = db_session.create_session()
        admin = db_sess.query(Admins).filter(Admins.login == user_id).first()
        if not admin:
            await vk.messages_send(message=f"Пользователь {user_info[0]['first_name']} не найден в базе данных админов",
                                   peer_id=event['object']['message']['peer_id'],
                                   random_id=0)
            db_sess.close()
            return
        db_sess.delete(admin)
        db_sess.commit()
        db_sess.close()
        await vk.messages_send(message=f"Пользователь {user_info[0]['first_name']} удален из списка админов",
                               peer_id=event['object']['message']['peer_id'],
                               random_id=0)


# @bot.on.chat_message(OnlyAdmins(), text=['.админы список'])
async def get_admin_list(vk, event):
    db_sess = db_session.create_session()
    admins = db_sess.query(Admins).all()
    answer = ['Список админов:']
    for num, admin in enumerate(admins):
        admin_info = await vk.users_get(user_ids=admin.login)
        answer.append(f"{num + 1}. {admin_info[0]['first_name']} {admin_info[0]['last_name']}")
    db_sess.close()
    await vk.messages_send(message='\n'.join(answer), random_id=0, peer_id=event['object']['message']['peer_id'])


# @bot.on.chat_message(text=['.инфо', '.о боте'])
async def get_info_about_bot(vk, event):
    await vk.messages_send(message="Версия бота: 3.1.1\n"
                         "Идея: Имя Фамилия\n"
                         "Разработчик: Глеб Бутович\n"
                         "Главный по поддержке хоста: Евгений Грущенко\n"
                         "Выражаю благодарность Тимону, подсказывал тогда, когда я был невнимателен",
                         peer_id=event['object']['message']['peer_id'],
                         random_id=0)


# @bot.on.chat_message(OnlyAdmins(), text=['.хелп'])
async def get_help(vk, event):
    await vk.messages_send(message="""Вот какие команды есть в боте:\n
    .инфо - выводит информацию о боте\n
    .отпуск - дает отпуск юзеру\n
    .неактивы - показывает список неактивных пользователей\n
    .отнять отпуск - отнимает отпуск\n
    .отпуски - показывает список тех, кто в отпуске\n
    .добавить админа - добавляет админа из бд(только для админов с правами супер)\n
    .удалить админа - удаляет админа из бд(только для админов с правами супер)\n
    .админы список - выдает список админов\n
    .изменить лояльность, .изм, .лоял, .лояльность - позваляет менять лояльность юзеру\n
    .рейтинг - выводит топ юзеров по лояльности\n
    .удалить - удаляет юзера из базы данных\n
    .проверить бд - удаляет всех из бд, кого нет в чате\n
    .регистрация - добавляет в бд всех, кого нет в бд, но есть в чате\n
    .кик - кикает юзера из чата\n
    .юзер - выводит инфу о конкретном юзере(Если хотите узнать о конкретном пользователе, то используйте следующий
    синтаксис: .юзер <user>, иначе вы получите инфу о себе)\n
    В остальных же случаях вы можете подробнее узнать о команде введя ее без параметров)""",
                           random_id=0,
                           peer_id=event['object']['message']['peer_id'])


# @bot.on.chat_message(OnlyAdmins(), text=['.изменить лояльность <user> <loyalty>', '.изм <user> <loyalty>',
                                         # '.лоял <user> <loyalty>', '.лояльность <user> <loyalty>',
                                         # '.изменить лояльность', '.изм'])
async def change_loyalty_user(vk, event):
    data = event['object']['message']['text'].split()
    print(data)
    if len(data) != 4 and len(data) != 3:
        await vk.messages_send(
            message='Для добавления пользователю очков лояльности используйте команду: .изменить лояльность @user loyalty\n'
                    'Например: .изменить лояльность @user +10, данная команда прибавит 10 очков лояльности юзеру',
            random_id=0,
            peer_id=event['object']['message']['peer_id'])
        return
    db_sess = db_session.create_session()
    user = data[-2]
    loyalty = data[-1]
    user_id = int(user[3:user.find("|")])
    user = db_sess.query(User).filter(User.login == user_id).first()
    final_loyalty = change_loyalty(loyalty, user.loyalty)
    if type(final_loyalty) == int:
        user.loyalty = final_loyalty
        user = get_rank(user)
        db_sess.commit()
        user_info = await vk.users_get(user_ids=user_id)
        await vk.messages_send(message=f"Очки лояльности у пользователя {user_info[0]['first_name']} после изменения: "
                                       f"{final_loyalty}",
                               random_id=0,
                               peer_id=event['object']['message']['peer_id'])
    else:
        await vk.messages_send(
            message='Для добавления пользователю очков лояльности используйте команду: .изменить лояльность @user loyalty\n'
                    'Например: .изменить лояльность @user +10, данная команда прибавит 10 очков лояльности юзеру',
            peer_id=event['object']['message']['peer_id'],
            random_id=0)
    db_sess.close()


# @bot.on.chat_message(text=['/топ', '.рейтинг'])
async def get_top_users(vk, event):
    db_sess = db_session.create_session()
    users_info = db_sess.query(User).all()
    users = {user.login: user.loyalty for user in users_info}
    sorted_users = dict(sorted(users.items(), key=lambda item: item[1], reverse=True))
    users_id = sorted_users.keys()
    db_sess.close()
    answer = ['Топ по очкам лояльности:']
    for num, key in enumerate(users_id):
        user_name = await vk.users_get(user_ids=key)
        answer.append(f"{num + 1}. {user_name[0]['first_name']} {user_name[0]['last_name']}: {sorted_users[key]}")
    await vk.messages_send(message='\n'.join(answer), peer_id=event['object']['message']['peer_id'], random_id=0)


# @bot.on.chat_message(MessageFromGroupChat(REPORTS_CHAT_ID))
async def get_report_message(vk, event):
    try:
        db_sess = db_session.create_session()
        if "https://" in event['object']['message']['text'] or event['object']['message']['attachments'][0]['wall_reply']:
            user = db_sess.query(User).filter(User.login == event['object']['message']['from_id'])[0]
            if user is None:
                user = User(
                    login=event['object']['message']['from_id']
                )
                db_sess.add(user)
            user.loyalty += 1
            user.reports_count += 1
            user.unemployed_days = 0
            user.vacation = 0
            user = get_rank(user)
            db_sess.commit()
            db_sess.close()
            user_info = await vk.users_get(user_ids=event['object']['message']['from_id'])
            await vk.messages_send(chat_id=0, random_id=0, peer_id=2000000001,
                                        message=f"{user_info[0]['first_name']} {user_info[0]['last_name']} отправил отчет, успешно засчитан")
    except KeyError:
        db_sess.close()
        # await bot.api.messages.delete(peer_id=message.peer_id, message_ids=message_id, delete_for_all=True,
        #                              group_id=REPORTS_CHAT_ID)


# @bot.on.chat_message(text=["/юзер <user>", ".юзер <user>", ".юзер", "/юзер"])
async def get_user_info(vk, event):
    data = event['object']['message']['text'].split()
    if len(data) == 1:
        user_id = event['object']['message']['from_id']
    else:
        user = data[-1]
        user_id = int(user[3:user.find("|")])
    db_sess = db_session.create_session()
    user_info = db_sess.query(User).filter(User.login == user_id)[0]
    db_sess.close()
    answer = f"Дни неактива: {user_info.unemployed_days}\n" \
             f"Очки лояльности: {user_info.loyalty}\n" \
             f"Отпуск: {user_info.vacation}\n" \
             f"Ранг: {ranks[user_info.rank]}\n" \
             f"Занимаемая должность: {posts[user_info.post]}\n" \
             f"Обязанность по отчетам: {user_info.duty}"
    await vk.messages_send(message=answer, peer_id=event['object']['message']['peer_id'], random_id=0)


# @bot.on.chat_message(OnlyAdmins(), text=['чурбан', 'Чурбан'])
async def meme(vk, event):
    var = random.choice([0, 1])
    if var == 0:
        """photo = await photo_uploader.upload(
            file_source="churman.jpg"
        )"""
        await vk.messages_send(message="✅ На месте", peer_id=event['object']['message']['peer_id'], random_id=0)
    else:
        await vk.messages_send(message="САМ ЧУРБАН", peer_id=event['object']['message']['peer_id'], random_id=0)


async def get_ranks_info(vk, event):
    peer_id = event['object']['message']['peer_id']
    await vk.messages_send(message="Про систему рангов можете почитать здесь: "
                                   "https://vk.com/@bot_legion_news-sistema-rangov",
                           random_id=0, peer_id=peer_id)


async def get_posts_info(vk, event):
    peer_id = event['object']['message']['peer_id']
    await vk.messages_send(message="Поподробнее про должности можете почитать здесь: "
                                   "https://vk.com/@bot_legion_news-dolzhnosti-v-legione", random_id=0, peer_id=peer_id)


# @bot.on.chat_message(OnlyAdmins(), text=['.регистрация'])
async def registration(vk, event):
    db_sess = db_session.create_session()
    users = await vk.messages_getConversationMembers(peer_id=event['object']['message']['peer_id'])
    users_list = [user.login for user in db_sess.query(User).all()]
    for user in users['profiles']:
        if str(user['id']) in users_list:
            continue
        user_new = User(login=user['id'])
        db_sess.add(user_new)
    db_sess.commit()
    db_sess.close()
    await vk.messages_send(message="Все пользователи успешно добавлены в бд)", random_id=0, peer_id=event['object']
    ['message']['peer_id'])


async def leave():
    # await message.answer(message.chat_id)
    session = db_session.create_session()
    session.close_all()
    await asyncio.sleep(120)
    loop.create_task(leave())


def check_event(event):
    try:
        if event['object']['message']['text']:
            return True
        else:
            return False
    except KeyError:
        return False

def check_command(event):
    for el in ['.изменить лояльность', '.изм', '.лоял', '.лояльность']:
        if event['object']['message']['text'].startswith(el):
            return True
    return False


def get_rank(user):
    if user.loyalty < 300:
        user.rank = 0
        user.duty = 4
    elif 300 <= user.loyalty < 400:
        user.rank = 1
        user.duty = 2
    elif 400 <= user.loyalty < 500:
        user.rank = 2
        user.duty = 2
    elif 500 <= user.loyalty < 600:
        user.rank = 3
        user.duty = 2
    elif 600 <= user.loyalty < 700:
        user.rank = 4
        user.duty = 2
    elif 700 <= user.loyalty < 1200:
        user.rank = 5
        user.duty = 3
    elif 1200 <= user.loyalty < 1700:
        user.rank = 6
        user.duty = 5
    elif 1700 <= user.loyalty < 2500:
        user.rank = 7
        user.duty = 4
    elif user.loyalty >= 2500:
        user.rank = 8
        user.duty = 4
    return user


async def start():
    session = VkApi(token=token)
    vk = session.api_context()
    longpoll = VkBotLongPoll(session, "222041853")
    loop.create_task(auto_minus_loyalty(vk))
    loop.create_task(user_warning(vk))
    loop.create_task(leave())
    print("work")
    async for event in longpoll.listen():
        try:
            if event['type'] != "message_new":
                continue
            if check_event(event):
                if event['object']['message']['text'] == ".инфо":
                    loop.create_task(get_info_about_bot(vk, event))
                if event['object']['message']['text'].startswith(".юзер"):
                    loop.create_task(get_user_info(vk, event))
                if event['object']['message']['text'] == '.рейтинг':
                    loop.create_task(get_top_users(vk, event))
                if event['object']['message']['text'] == ".ранги":
                    loop.create_task(get_ranks_info(vk, event))
                if event['object']['message']['text'] == ".должности":
                    loop.create_task(get_posts_info(vk, event))
                if check_admin(event):
                    if event['object']['message']['text'].startswith(".дать дол"):
                        loop.create_task(give_post(vk, event))
                    if event['object']['message']['text'].startswith(".забрать дол"):
                        loop.create_task(pick_up_post(vk, event))
                    if "чурбан" in event['object']['message']['text'] or "Чурбан" in event['object']['message']['text']:
                        loop.create_task(meme(vk, event))
                    if event['object']['message']['text'] == '.хелп':
                        loop.create_task(get_help(vk, event))
                    if event['object']['message']['text'] == '.неактивы':
                        loop.create_task(get_list_not_active(vk, event))
                    if event['object']['message']['text'].startswith(".отнять отпуск"):
                        loop.create_task(pick_up_vacation(vk, event))
                    if event['object']['message']['text'] == '.отпуски':
                        loop.create_task(get_list_vacation(vk, event))
                    if event['object']['message']['text'].startswith(".отпуск "):
                        loop.create_task(take_vacation(vk, event))
                    if event['object']['message']['text'] == ".админы список":
                        loop.create_task(get_admin_list(vk, event))
                    if check_command(event):
                        loop.create_task(change_loyalty_user(vk, event))
                    if event['object']['message']['text'].startswith(".удалить"):
                        loop.create_task(delete_user_bd(vk, event))
                    if event['object']['message']['text'] == '.проверить бд':
                        loop.create_task(check_database(vk, event))
                    if event['object']['message']['text'] == '.регистрация':
                        loop.create_task(registration(vk, event))
                    if event['object']['message']['text'].startswith('.кик'):
                        loop.create_task(kick_user(vk, event))
                    if check_super_admin(event):
                        if event['object']['message']['text'].startswith(".добавить админа"):
                            loop.create_task(add_admin(vk, event))
                        if event['object']['message']['text'].startswith(".удалить админа"):
                            loop.create_task(remove_admin(vk, event))
                        if event['object']['message']['text'] == ".give_ranks":
                            loop.create_task(give_all_you_need(vk ,event))
            else:
                if check_chat(event, REPORTS_CHAT_ID):
                    loop.create_task(get_report_message(vk, event))
                if event['object']['message']['action'] in ["chat_invite_user", "chat_invite_user_by_link"]:
                    loop.create_task(new_user(vk, event))
                if event['object']['message']['action'] == "chat_kick_user":
                    loop.create_task(delete_user(vk, event))
        except:
            print("ERROR")

loop = asyncio.new_event_loop()
loop.create_task(start())
loop.run_forever()
