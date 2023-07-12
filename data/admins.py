import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin


class Admins(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'admin'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    login = sqlalchemy.Column(sqlalchemy.String)
    permission = sqlalchemy.Column(sqlalchemy.String)
