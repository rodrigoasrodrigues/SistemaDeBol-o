from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from ..models import User


class LoginForm(FlaskForm):
    email = StringField("E-mail", validators=[DataRequired(), Email()])
    password = PasswordField("Senha", validators=[DataRequired()])
    remember_me = BooleanField("Lembrar de mim")
    submit = SubmitField("Entrar")


class RegisterForm(FlaskForm):
    username = StringField(
        "Nome de usuário", validators=[DataRequired(), Length(3, 64)]
    )
    email = StringField("E-mail", validators=[DataRequired(), Email()])
    password = PasswordField("Senha", validators=[DataRequired(), Length(6, 128)])
    password2 = PasswordField(
        "Confirmar senha",
        validators=[DataRequired(), EqualTo("password", message="As senhas não coincidem.")],
    )
    submit = SubmitField("Cadastrar")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("Nome de usuário já está em uso.")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("E-mail já cadastrado.")
