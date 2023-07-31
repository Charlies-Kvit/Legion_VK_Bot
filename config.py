from data import db_session
from api_key import token

token = token
db_session.global_init('db/db.sqlite')
REPORTS_CHAT_ID = 2000000006  # 6 перед выкатом
HOUR = 23
MINUTES = 50
WARNING_HOUR = 15
WARNING_MINUTES = 30
