import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin


class User(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'user'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    login = sqlalchemy.Column(sqlalchemy.String)
    loyalty = sqlalchemy.Column(sqlalchemy.Integer, default=1)
    unemployed_days = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    vacation = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    reports_count = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    warning_user = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
