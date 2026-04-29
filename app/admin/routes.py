import requests as req
import logging
from datetime import datetime
from functools import wraps
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from . import admin
from .forms import (
    GameForm,
    GameResultForm,
    TeamForm,
    StadiumForm,
    PointConfigForm,
    ApiEndpointForm,
)
from ..models import db, Game, Team, Stadium, Bet, PointConfig, ApiEndpoint, User


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


@admin.route("/")
@login_required
@admin_required
def dashboard():
    stats = {
        "total_games": Game.query.count(),
        "finished_games": Game.query.filter_by(status="finished").count(),
        "total_bets": Bet.query.count(),
        "total_users": User.query.filter_by(is_admin=False).count(),
    }
    return render_template("admin/dashboard.html", stats=stats)


# ---------------------------------------------------------------------------
# Games
# ---------------------------------------------------------------------------


@admin.route("/games")
@login_required
@admin_required
def games():
    games_list = Game.query.order_by(Game.match_datetime.asc()).all()
    return render_template("admin/games.html", games=games_list)


@admin.route("/games/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_game():
    form = GameForm()
    _populate_game_form_choices(form)

    if form.validate_on_submit():
        game = Game(
            home_team_id=form.home_team_id.data,
            away_team_id=form.away_team_id.data,
            stadium_id=form.stadium_id.data or None,
            location=form.location.data,
            match_datetime=form.match_datetime.data,
            round_name=form.round_name.data,
            group_name=form.group_name.data,
        )
        db.session.add(game)
        db.session.commit()
        flash("Jogo cadastrado com sucesso!", "success")
        return redirect(url_for("admin.games"))

    return render_template("admin/game_form.html", form=form, title="Novo Jogo")


@admin.route("/games/<int:game_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_game(game_id):
    game = Game.query.get_or_404(game_id)
    form = GameForm(obj=game)
    _populate_game_form_choices(form)

    if form.validate_on_submit():
        game.home_team_id = form.home_team_id.data
        game.away_team_id = form.away_team_id.data
        game.stadium_id = form.stadium_id.data or None
        game.location = form.location.data
        game.match_datetime = form.match_datetime.data
        game.round_name = form.round_name.data
        game.group_name = form.group_name.data
        db.session.commit()
        flash("Jogo atualizado com sucesso!", "success")
        return redirect(url_for("admin.games"))

    return render_template("admin/game_form.html", form=form, title="Editar Jogo", game=game)


@admin.route("/games/<int:game_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_game(game_id):
    game = Game.query.get_or_404(game_id)
    Bet.query.filter_by(game_id=game_id).delete()
    db.session.delete(game)
    db.session.commit()
    flash("Jogo removido.", "info")
    return redirect(url_for("admin.games"))


@admin.route("/games/<int:game_id>/result", methods=["GET", "POST"])
@login_required
@admin_required
def set_result(game_id):
    game = Game.query.get_or_404(game_id)
    form = GameResultForm()

    if form.validate_on_submit():
        game.home_score = form.home_score.data
        game.away_score = form.away_score.data
        game.status = "finished"

        # Recalculate points for all bets on this game
        point_config = PointConfig.get_current()
        for bet in game.bets:
            bet.calculate_points(point_config)

        db.session.commit()
        flash("Resultado salvo e pontuações calculadas!", "success")
        return redirect(url_for("admin.games"))

    if game.home_score is not None:
        form.home_score.data = game.home_score
        form.away_score.data = game.away_score

    return render_template("admin/result_form.html", form=form, game=game)


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------


@admin.route("/teams")
@login_required
@admin_required
def teams():
    teams_list = Team.query.order_by(Team.name.asc()).all()
    return render_template("admin/teams.html", teams=teams_list)


@admin.route("/teams/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_team():
    form = TeamForm()
    if form.validate_on_submit():
        team = Team(
            name=form.name.data,
            country_code=form.country_code.data.upper(),
            flag_url=form.flag_url.data,
        )
        db.session.add(team)
        db.session.commit()
        flash("Time cadastrado com sucesso!", "success")
        return redirect(url_for("admin.teams"))
    return render_template("admin/team_form.html", form=form, title="Novo Time")


@admin.route("/teams/<int:team_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_team(team_id):
    team = Team.query.get_or_404(team_id)
    form = TeamForm(obj=team)
    if form.validate_on_submit():
        team.name = form.name.data
        team.country_code = form.country_code.data.upper()
        team.flag_url = form.flag_url.data
        db.session.commit()
        flash("Time atualizado!", "success")
        return redirect(url_for("admin.teams"))
    return render_template("admin/team_form.html", form=form, title="Editar Time", team=team)


@admin.route("/teams/<int:team_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_team(team_id):
    team = Team.query.get_or_404(team_id)
    db.session.delete(team)
    db.session.commit()
    flash("Time removido.", "info")
    return redirect(url_for("admin.teams"))


# ---------------------------------------------------------------------------
# Stadiums
# ---------------------------------------------------------------------------


@admin.route("/stadiums")
@login_required
@admin_required
def stadiums():
    stadiums_list = Stadium.query.order_by(Stadium.name.asc()).all()
    return render_template("admin/stadiums.html", stadiums=stadiums_list)


@admin.route("/stadiums/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_stadium():
    form = StadiumForm()
    if form.validate_on_submit():
        stadium = Stadium(
            name=form.name.data,
            city=form.city.data,
            country=form.country.data,
        )
        db.session.add(stadium)
        db.session.commit()
        flash("Estádio cadastrado com sucesso!", "success")
        return redirect(url_for("admin.stadiums"))
    return render_template("admin/stadium_form.html", form=form, title="Novo Estádio")


@admin.route("/stadiums/<int:stadium_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_stadium(stadium_id):
    stadium = Stadium.query.get_or_404(stadium_id)
    form = StadiumForm(obj=stadium)
    if form.validate_on_submit():
        stadium.name = form.name.data
        stadium.city = form.city.data
        stadium.country = form.country.data
        db.session.commit()
        flash("Estádio atualizado!", "success")
        return redirect(url_for("admin.stadiums"))
    return render_template(
        "admin/stadium_form.html", form=form, title="Editar Estádio", stadium=stadium
    )


@admin.route("/stadiums/<int:stadium_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_stadium(stadium_id):
    stadium = Stadium.query.get_or_404(stadium_id)
    db.session.delete(stadium)
    db.session.commit()
    flash("Estádio removido.", "info")
    return redirect(url_for("admin.stadiums"))


# ---------------------------------------------------------------------------
# Point configuration
# ---------------------------------------------------------------------------


@admin.route("/config", methods=["GET", "POST"])
@login_required
@admin_required
def point_config():
    config = PointConfig.get_current()
    form = PointConfigForm(obj=config)
    if form.validate_on_submit():
        config.correct_score_points = form.correct_score_points.data
        config.correct_winner_points = form.correct_winner_points.data
        config.correct_draw_points = form.correct_draw_points.data
        db.session.commit()
        flash("Configuração de pontos atualizada!", "success")
        return redirect(url_for("admin.point_config"))
    return render_template("admin/point_config.html", form=form, config=config)


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------


@admin.route("/api-endpoints")
@login_required
@admin_required
def api_endpoints():
    endpoints = ApiEndpoint.query.order_by(ApiEndpoint.name.asc()).all()
    return render_template("admin/api_endpoints.html", endpoints=endpoints)


@admin.route("/api-endpoints/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_api_endpoint():
    form = ApiEndpointForm()
    if form.validate_on_submit():
        endpoint = ApiEndpoint(
            name=form.name.data,
            url=form.url.data,
            description=form.description.data,
            api_key_header=form.api_key_header.data,
            api_key_value=form.api_key_value.data,
            is_active=form.is_active.data,
        )
        db.session.add(endpoint)
        db.session.commit()
        flash("Endpoint cadastrado!", "success")
        return redirect(url_for("admin.api_endpoints"))
    return render_template("admin/api_endpoint_form.html", form=form, title="Novo Endpoint")


@admin.route("/api-endpoints/<int:ep_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_api_endpoint(ep_id):
    endpoint = ApiEndpoint.query.get_or_404(ep_id)
    form = ApiEndpointForm(obj=endpoint)
    if form.validate_on_submit():
        endpoint.name = form.name.data
        endpoint.url = form.url.data
        endpoint.description = form.description.data
        endpoint.api_key_header = form.api_key_header.data
        endpoint.api_key_value = form.api_key_value.data
        endpoint.is_active = form.is_active.data
        db.session.commit()
        flash("Endpoint atualizado!", "success")
        return redirect(url_for("admin.api_endpoints"))
    return render_template(
        "admin/api_endpoint_form.html", form=form, title="Editar Endpoint", endpoint=endpoint
    )


@admin.route("/api-endpoints/<int:ep_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_api_endpoint(ep_id):
    endpoint = ApiEndpoint.query.get_or_404(ep_id)
    db.session.delete(endpoint)
    db.session.commit()
    flash("Endpoint removido.", "info")
    return redirect(url_for("admin.api_endpoints"))


@admin.route("/api-endpoints/<int:ep_id>/import", methods=["POST"])
@login_required
@admin_required
def import_games_from_api(ep_id):
    """Fetch games from external API endpoint and import them."""
    endpoint = ApiEndpoint.query.get_or_404(ep_id)
    if not endpoint.is_active:
        flash("Este endpoint está inativo.", "warning")
        return redirect(url_for("admin.api_endpoints"))

    headers = {}
    if endpoint.api_key_header and endpoint.api_key_value:
        headers[endpoint.api_key_header] = endpoint.api_key_value

    try:
        response = req.get(endpoint.url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except req.exceptions.RequestException as e:
        flash(f"Erro ao acessar a API: {e}", "danger")
        return redirect(url_for("admin.api_endpoints"))
    except ValueError:
        flash("Resposta da API não é um JSON válido.", "danger")
        return redirect(url_for("admin.api_endpoints"))

    imported = _import_games_from_data(data)
    flash(f"{imported} jogo(s) importado(s) com sucesso!", "success")
    return redirect(url_for("admin.api_endpoints"))


def _import_games_from_data(data):
    """Parse API data and create Game records. Returns count of imported games."""
    matches = []
    # Support multiple common API response shapes
    if isinstance(data, list):
        matches = data
    elif isinstance(data, dict):
        for key in ("matches", "games", "fixtures", "data", "results"):
            if key in data and isinstance(data[key], list):
                matches = data[key]
                break

    imported = 0
    for match in matches:
        try:
            home_name = (
                match.get("homeTeam", {}).get("name")
                or match.get("home_team", {}).get("name")
                or match.get("home_team")
            )
            away_name = (
                match.get("awayTeam", {}).get("name")
                or match.get("away_team", {}).get("name")
                or match.get("away_team")
            )
            dt_str = match.get("utcDate") or match.get("date") or match.get("datetime")

            if not home_name or not away_name or not dt_str:
                continue

            # Parse date/time – strip timezone info and try common formats
            match_dt = _parse_datetime(dt_str)
            if match_dt is None:
                continue

            home_code = (
                match.get("homeTeam", {}).get("tla")
                or match.get("home_team", {}).get("code")
                or home_name[:3].upper()
            )
            away_code = (
                match.get("awayTeam", {}).get("tla")
                or match.get("away_team", {}).get("code")
                or away_name[:3].upper()
            )

            home_team = Team.query.filter_by(name=home_name).first()
            if not home_team:
                home_team = Team(name=home_name, country_code=home_code[:3])
                db.session.add(home_team)

            away_team = Team.query.filter_by(name=away_name).first()
            if not away_team:
                away_team = Team(name=away_name, country_code=away_code[:3])
                db.session.add(away_team)

            db.session.flush()

            existing = Game.query.filter_by(
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                match_datetime=match_dt,
            ).first()
            if existing:
                continue

            game = Game(
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                match_datetime=match_dt,
                round_name=match.get("stage") or match.get("round"),
                group_name=match.get("group"),
            )
            db.session.add(game)
            imported += 1
        except Exception:
            logging.getLogger(__name__).warning(
                "Failed to import match record: %s", match, exc_info=True
            )
            continue

    db.session.commit()
    return imported


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _populate_game_form_choices(form):
    teams = Team.query.order_by(Team.name.asc()).all()
    form.home_team_id.choices = [(t.id, t.name) for t in teams]
    form.away_team_id.choices = [(t.id, t.name) for t in teams]

    stadiums = Stadium.query.order_by(Stadium.name.asc()).all()
    form.stadium_id.choices = [(0, "— Selecione —")] + [(s.id, s.name) for s in stadiums]


def _parse_datetime(dt_str):
    """Parse a datetime string from common API formats, returning a naive UTC datetime."""
    if not dt_str:
        return None
    # Remove trailing Z and any timezone offset (+HH:MM or -HH:MM) to get naive string
    naive = dt_str.strip()
    if naive.endswith("Z"):
        naive = naive[:-1]
    # Remove timezone offset: find a +/- after the time part (after position 10)
    for sep in ("+", "-"):
        idx = naive.find(sep, 10)
        if idx != -1:
            naive = naive[:idx]
            break
    # Try each candidate format
    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(naive, fmt)
        except ValueError:
            continue
    return None
