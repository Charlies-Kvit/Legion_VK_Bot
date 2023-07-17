from vkbottle import API, BuiltinStateDispenser
from vkbottle.bot import BotLabeler
from data import db_session
from api_key import token
api = API(token)
labeler = BotLabeler()
state_dispenser = BuiltinStateDispenser()
db_session.global_init('db/db.sqlite')
REPORTS_CHAT_ID = 5
HOUR = 23
MINUTES = 50
WARNING_HOUR = 15
WARNING_MINUTES = 30
