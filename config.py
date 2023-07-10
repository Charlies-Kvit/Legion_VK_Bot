from vkbottle import API, BuiltinStateDispenser
from vkbottle.bot import BotLabeler
from data import db_session
from data.user import User
api = API("vk1.a.Rowp9IopxJDDQ0LXuIsdBwJBKU9z9LOXPVELB32mSkjCuj5YpyKBL839Iu8Yk_eLxqP3otEgnDuiODQUmr6p2A3ABRv9xwGcBjUa4sjVoGNmfVesCeMCd3bHSMDsIpIRsDgf5aM7WPO5eFBt77YXPjqztQljIl3BbQIVjF6IzHLBU0K4Bt1zn1cS2nBqZ2Mo_jEaKsYhsa8nO6uQWhFxwQ")
labeler = BotLabeler()
state_dispenser = BuiltinStateDispenser()
db_session.global_init('db/db.sqlite')
session = db_session.create_session()
users_data = session.query(User).all()
users = {user.login: user.to_dict(only=("loyalty", "unemployed_days", "vacation")) for user in users_data}
