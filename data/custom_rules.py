from data import db_session
from data.admins import Admins


def check_chat(event, chat_id):
    return event['object']['message']['peer_id'] == chat_id


def check_super_admin(event):
    db_sess = db_session.create_session()
    admins = db_sess.query(Admins).all()
    for admin in admins:
        if admin.login == str(event['object']['message']['from_id']) and admin.permission == "super":
            return True
    return False


def check_admin(event):
    db_sess = db_session.create_session()
    admins = db_sess.query(Admins).all()
    for admin in admins:
        if admin.login == str(event['object']['message']['from_id']):
            return True
    return False
