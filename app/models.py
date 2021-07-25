import uuid
from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID

from app import db, login, nyse_symbols



class GUID(TypeDecorator):
    """Valor de GUID personalizado
    Usa el tipo de dato UUID de PostgreSQL o CHAR(32) en su defecto
    """

    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(UserMixin, db.Model):
    """Modelo para tabla Usuario"""

    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    enterprises = db.relationship("Enterprise", backref="author", lazy="dynamic")
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return "<User {}>".format(self.username)

    def get_id(self):
        return self.user_id

    def set_password(self, password: str):
        """No se guarda directamente la contraseña del usuario sino el hash

        :param password: Contraseña sin encriptar
        :type password: str
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Se valida que los hashes sean los mismos

        :param password: Contraseña sin encriptar
        :type password: str
        :return: Validación
        :rtype: Bool
        """
        return check_password_hash(self.password_hash, password)

    def get_all_enterprises(self):
        """Retorna todas las empresas creadas por el usuario

        :return: empresas ordenadas de más nueva a más vieja
        :rtype: lista de instancias de Enterprise
        """
        all_enterprises = Enterprise.query.order_by(Enterprise.timestamp.desc())
        return all_enterprises


values_enterprises = db.Table(
    "values_enterprises",
    db.Column("value_id", db.Integer, db.ForeignKey("values_table.value_id")),
    db.Column("enterprise_id", GUID(), db.ForeignKey("enterprises.enterprise_id")),
)


class Value(db.Model):
    """Modelo de tabla values. Para no chocar con la palabra reservada de SQL value se cambia el nombre de la tabla"""

    __tablename__ = "values_table"
    value_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return "<Value {}>".format(self.name)

    def get_id(self):
        return self.value_id


class Enterprise(db.Model):
    """Modelo de la tabla enterprises"""

    __tablename__ = "enterprises"
    enterprise_id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(64), index=True, unique=True)
    description = db.Column(db.String(140))
    symbol = db.Column(db.String(10), index=True, unique=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    values = db.relationship("Value", secondary=values_enterprises)

    def __repr__(self):
        return "<Enterprise {}>".format(self.name)

    def get_id(self):
        return self.enterprise_id
