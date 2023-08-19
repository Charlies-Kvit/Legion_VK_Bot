from data import db_session
from api_key import token

token = token
db_session.global_init('db/db.sqlite')
REPORTS_CHAT_ID = 2000000002  # 2 перед выкатом
NORMAL_CHAT_ID = 2000000003 # 3 перед выкатом
HOUR = 23
MINUTES = 50
WARNING_HOUR = 15
WARNING_MINUTES = 30
ranks = ["Гастат", "Принцип", "Принцип 1-го ранга", "Принцип 2-го ранга", "Принцип 3-го ранга", "Центурион", "Опцион",
         "Префект", "Трибун"]
posts = ["Рядовой", "[M]Наставник", "[F]Гвардеец", "[G]Легат", "[I]Разведчик"]