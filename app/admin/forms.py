from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    IntegerField,
    SelectField,
    DateTimeLocalField,
    TextAreaField,
    BooleanField,
    SubmitField,
    URLField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional, URL


class GameForm(FlaskForm):
    home_team_id = SelectField("Time da Casa", coerce=int, validators=[DataRequired()])
    away_team_id = SelectField("Time Visitante", coerce=int, validators=[DataRequired()])
    stadium_id = SelectField("Estádio", coerce=int, validators=[Optional()])
    location = StringField("Local", validators=[Optional(), Length(max=200)])
    match_datetime = DateTimeLocalField(
        "Data e Hora", format="%Y-%m-%dT%H:%M", validators=[DataRequired()]
    )
    round_name = StringField("Fase / Rodada", validators=[Optional(), Length(max=100)])
    group_name = StringField("Grupo", validators=[Optional(), Length(max=50)])
    submit = SubmitField("Salvar Jogo")


class GameResultForm(FlaskForm):
    home_score = IntegerField(
        "Gols do time da casa", validators=[DataRequired(), NumberRange(min=0)]
    )
    away_score = IntegerField(
        "Gols do time visitante", validators=[DataRequired(), NumberRange(min=0)]
    )
    submit = SubmitField("Salvar Resultado")


class TeamForm(FlaskForm):
    name = StringField("Nome do Time", validators=[DataRequired(), Length(max=100)])
    country_code = StringField(
        "Código do País (3 letras)", validators=[DataRequired(), Length(min=2, max=3)]
    )
    flag_url = StringField("URL da Bandeira", validators=[Optional(), Length(max=300)])
    submit = SubmitField("Salvar Time")


class StadiumForm(FlaskForm):
    name = StringField("Nome do Estádio", validators=[DataRequired(), Length(max=150)])
    city = StringField("Cidade", validators=[DataRequired(), Length(max=100)])
    country = StringField("País", validators=[DataRequired(), Length(max=100)])
    submit = SubmitField("Salvar Estádio")


class PointConfigForm(FlaskForm):
    correct_score_points = IntegerField(
        "Pontos por acerto do placar exato",
        validators=[DataRequired(), NumberRange(min=0)],
    )
    correct_winner_points = IntegerField(
        "Pontos por acerto do vencedor",
        validators=[DataRequired(), NumberRange(min=0)],
    )
    correct_draw_points = IntegerField(
        "Pontos por acerto do empate",
        validators=[DataRequired(), NumberRange(min=0)],
    )
    submit = SubmitField("Salvar Configuração")


class ApiEndpointForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(max=100)])
    url = StringField("URL da API", validators=[DataRequired(), Length(max=500)])
    description = TextAreaField("Descrição", validators=[Optional()])
    api_key_header = StringField(
        "Header da API Key (ex: X-Auth-Token)", validators=[Optional(), Length(max=100)]
    )
    api_key_value = StringField("Valor da API Key", validators=[Optional(), Length(max=300)])
    is_active = BooleanField("Ativo", default=True)
    submit = SubmitField("Salvar Endpoint")
