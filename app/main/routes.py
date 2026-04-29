from datetime import datetime
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func
from . import main
from .forms import BetForm
from ..models import db, User, Game, Bet, PointConfig


@main.route("/")
def index():
    point_config = PointConfig.get_current()

    # Ranking: users sorted by total points
    users = User.query.filter_by(is_admin=False).all()
    ranking = sorted(users, key=lambda u: u.total_points, reverse=True)

    # Next upcoming games (up to 5)
    upcoming_games = (
        Game.query.filter(
            Game.status == "scheduled",
            Game.match_datetime >= datetime.utcnow(),
        )
        .order_by(Game.match_datetime.asc())
        .limit(5)
        .all()
    )

    # Last 5 finished games
    recent_games = (
        Game.query.filter_by(status="finished")
        .order_by(Game.match_datetime.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "index.html",
        ranking=ranking,
        upcoming_games=upcoming_games,
        recent_games=recent_games,
        point_config=point_config,
    )


@main.route("/games")
def games():
    status_filter = request.args.get("status", "all")
    query = Game.query

    if status_filter == "scheduled":
        query = query.filter_by(status="scheduled")
    elif status_filter == "finished":
        query = query.filter_by(status="finished")

    games_list = query.order_by(Game.match_datetime.asc()).all()
    return render_template("games/list.html", games=games_list, status_filter=status_filter)


@main.route("/games/<int:game_id>/bet", methods=["GET", "POST"])
@login_required
def place_bet(game_id):
    game = Game.query.get_or_404(game_id)

    if game.status != "scheduled":
        flash("Apostas encerradas para este jogo.", "warning")
        return redirect(url_for("main.games"))

    if game.match_datetime <= datetime.utcnow():
        flash("O jogo já começou. Apostas encerradas.", "warning")
        return redirect(url_for("main.games"))

    existing_bet = Bet.query.filter_by(user_id=current_user.id, game_id=game_id).first()
    form = BetForm()

    if form.validate_on_submit():
        if existing_bet:
            existing_bet.home_score = form.home_score.data
            existing_bet.away_score = form.away_score.data
            flash("Aposta atualizada com sucesso!", "success")
        else:
            bet = Bet(
                user_id=current_user.id,
                game_id=game_id,
                home_score=form.home_score.data,
                away_score=form.away_score.data,
            )
            db.session.add(bet)
            flash("Aposta registrada com sucesso!", "success")
        db.session.commit()
        return redirect(url_for("main.games"))

    if existing_bet and request.method == "GET":
        form.home_score.data = existing_bet.home_score
        form.away_score.data = existing_bet.away_score

    # Last 5 finished games
    recent_games = (
        Game.query.filter_by(status="finished")
        .order_by(Game.match_datetime.desc())
        .limit(5)
        .all()
    )

    # Bet volume stats for this game
    bet_stats = _get_bet_stats(game)

    return render_template(
        "games/bet.html",
        game=game,
        form=form,
        existing_bet=existing_bet,
        recent_games=recent_games,
        bet_stats=bet_stats,
    )


def _get_bet_stats(game):
    """Return aggregated bet statistics for a game."""
    total = game.bet_count
    if total == 0:
        return {"total": 0, "home_wins": 0, "draws": 0, "away_wins": 0}

    bets = game.bets.all()
    home_wins = sum(1 for b in bets if b.home_score > b.away_score)
    draws = sum(1 for b in bets if b.home_score == b.away_score)
    away_wins = sum(1 for b in bets if b.away_score > b.home_score)

    return {
        "total": total,
        "home_wins": home_wins,
        "draws": draws,
        "away_wins": away_wins,
        "home_pct": round(home_wins / total * 100),
        "draw_pct": round(draws / total * 100),
        "away_pct": round(away_wins / total * 100),
    }


@main.route("/my-bets")
@login_required
def my_bets():
    bets = (
        Bet.query.filter_by(user_id=current_user.id)
        .join(Game)
        .order_by(Game.match_datetime.desc())
        .all()
    )
    return render_template("games/my_bets.html", bets=bets)
