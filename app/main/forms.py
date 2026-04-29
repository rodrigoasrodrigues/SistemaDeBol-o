from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class BetForm(FlaskForm):
    home_score = IntegerField(
        "Gols do time da casa",
        validators=[DataRequired(message="Informe o placar."), NumberRange(min=0, max=99)],
    )
    away_score = IntegerField(
        "Gols do time visitante",
        validators=[DataRequired(message="Informe o placar."), NumberRange(min=0, max=99)],
    )
    submit = SubmitField("Confirmar Aposta")
