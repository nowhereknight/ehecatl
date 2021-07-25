import re

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length


from app.models import User, Enterprise
from app import nyse_symbols, logging, app


class LoginForm(FlaskForm):
    """Formulario para hacer el login"""

    username = StringField("Usuario", validators=[DataRequired()])
    password = StringField("Contraseña", validators=[DataRequired()])
    remember_me = BooleanField("Recuérdame")
    submit = SubmitField("Ingresar")


class RegistrationForm(FlaskForm):
    """Formulario para el registro de usuarios"""

    username = StringField("Usuario", validators=[DataRequired()])
    email = StringField("Correo electrónico", validators=[DataRequired(), Email()])
    password = PasswordField("Contraseña", validators=[DataRequired()])
    password2 = PasswordField("Repetir contraseña", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Registarse")

    def validate_username(self, username: str):
        """Valida que el nombre de usuario no esté ocupado

        :param username: nombre de usuario
        :type username: str
        :raises ValidationError: Esta excepción se levanta en routes.py en form.validate_on_submit():
        """
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError("Por favor usa un nombre de usuario diferente.")

    def validate_email(self, email: str):
        """Valida que la dirección de correo no haya sido usada

        :param email: Dirección de correo electrónico
        :type email: str
        :raises ValidationError: Esta excepción se levanta en routes.py en form.validate_on_submit():
        """
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError("Por favor usa una direccion de correo diferente.")


class EditProfileForm(FlaskForm):
    """Formulario para la edición de usuarios"""

    username = StringField("Usuario", validators=[DataRequired()])
    about_me = TextAreaField("Acerca de mi", validators=[Length(min=0, max=140)])
    submit = SubmitField("Enviar")

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username: str):
        """Valida que el nombre de usuario no esté ocupado

        :param username: nombre de usuario
        :type username: str
        :raises ValidationError: Esta excepción se levanta en routes.py en form.validate_on_submit():
        """
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError("Por favor usa un nombre de usuario diferente.")


class ValueListField(StringField):
    """Decorador para StringField para almacenar la lista de valores"""

    def __init__(self, label="", validators=None, remove_duplicates=True, to_lowercase=True, separator=" ", **kwargs):
        super(ValueListField, self).__init__(label, validators, **kwargs)
        self.remove_duplicates = remove_duplicates
        self.to_lowercase = to_lowercase
        self.separator = separator
        self.data = []

    def _value(self):
        if self.data:
            return u", ".join(self.data)
        else:
            return u""

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = [x.strip() for x in valuelist[0].split(self.separator)]
            if self.remove_duplicates:
                self.data = list(self._remove_duplicates(self.data))
            if self.to_lowercase:
                self.data = [x.lower() for x in self.data]

    @classmethod
    def _remove_duplicates(cls, seq):
        """Eliminar duplicados"""
        d = {}
        for item in seq:
            if item.lower() not in d:
                d[item.lower()] = True
                yield item


class EnterpriseForm(FlaskForm):
    """Formulario para registrar empresas"""

    name = TextAreaField("Nombre de la empresa", validators=[DataRequired(), Length(min=1, max=64)])
    description = TextAreaField("Descripción de la empresa", validators=[DataRequired(), Length(min=1, max=140)])
    symbol = TextAreaField("Símbolo de la empresa", validators=[DataRequired(), Length(min=1, max=10)])
    values = ValueListField(
        "Valores separados por coma",
        separator=",",
        validators=[Length(max=10, message="Sólo se pueden tener hasta 10 valores.")],
    )
    submit = SubmitField("Agregar")

    def validate_symbol(self, symbol: str):
        """Método que valida que el símbolo no haya sido usado ya en la BD, por la bolsa de
         valores de Nueva York, y que siga la expresión regular de los símbolos

        :param symbol: Símbolo de la empresa
        :type symbol: str
        :raises ValidationError: Esta excepción se levanta en routes.py en form.validate_on_submit():
        """
        if symbol.data in nyse_symbols:
            raise ValidationError("El símbolo de tu empresa ya está registrado en la bolsa de valores de Nueva York")
        enterprise = Enterprise.query.filter_by(symbol=self.symbol.data).first()
        if enterprise is not None:
            raise ValidationError("Símbolo ya usado. Por favor usa un símbolo diferente.")
        if re.match(r"\b[A-Z]{3}\b[.!?]?", str(symbol.data)) is None:
            raise ValidationError("Símbolo no sigue la expresión regular usada por el NYSE.")

    def validate_name(self, name: str):
        """Valida que el nombre de la empresa no haya sido usado ya

        :param name: Nombre de la empresa
        :type name: str
        :raises ValidationError: Esta excepción se levanta en routes.py en form.validate_on_submit():
        """
        enterprise = Enterprise.query.filter_by(name=self.name.data).first()
        if enterprise is not None:
            raise ValidationError("Por favor usa un nombre diferente.")


class EditEnterpriseForm(FlaskForm):
    """Formulario para editar empresas"""

    name = TextAreaField("Nombre de la empresa", validators=[DataRequired(), Length(min=1, max=64)])
    description = TextAreaField("Descripción de la empresa", validators=[DataRequired(), Length(min=1, max=140)])
    symbol = TextAreaField("Símbolo de la empresa", validators=[DataRequired(), Length(min=1, max=10)])
    submit = SubmitField("Editar")

    def __init__(self, original_name, original_symbol, *args, **kwargs):
        super(EditEnterpriseForm, self).__init__(*args, **kwargs)
        self.original_name = original_name
        self.original_symbol = original_symbol

    def validate_name(self, name):
        """Valida que el nombre de la empresa no haya sido usado ya

        :param name: Nombre de la empresa
        :type name: str
        :raises ValidationError: Esta excepción se levanta en routes.py en form.validate_on_submit():
        """
        if name.data != self.original_name:
            enterprise = Enterprise.query.filter_by(name=self.name.data).first()
            if enterprise is not None:
                raise ValidationError("Por favor usa un nombre diferente.")

    def validate_symbol(self, symbol):
        """Método que valida que el símbolo no haya sido usado ya en la BD, por la bolsa de
        valores de Nueva York, y que siga la expresión regular de los símbolos

        :param symbol: Símbolo de la empresa
        :type symbol: str
        :raises ValidationError: Esta excepción se levanta en routes.py en form.validate_on_submit():
        """
        if symbol.data != self.original_symbol:
            if symbol.data in nyse_symbols:
                raise ValidationError(
                    "El símbolo de tu empresa ya está registrado en la bolsa de valores de Nueva York"
                )
            enterprise = Enterprise.query.filter_by(symbol=self.symbol.data).first()
            if enterprise is not None:
                raise ValidationError("Símbolo ya usado. Por favor usa un símbolo diferente.")
            if re.match(r"\b[A-Z]{3}\b[.!?]?", str(symbol.data)) is None:
                raise ValidationError("Símbolo no sigue la expresión regular usada por el NYSE.")
