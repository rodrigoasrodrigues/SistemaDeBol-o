from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bets = db.relationship("Bet", backref="user", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def total_points(self):
        return sum(b.points_earned or 0 for b in self.bets)

    def __repr__(self):
        return f"<User {self.username}>"


class Team(db.Model):
    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    country_code = db.Column(db.String(3), nullable=False)
    flag_url = db.Column(db.String(300))

    home_games = db.relationship(
        "Game", foreign_keys="Game.home_team_id", backref="home_team", lazy="dynamic"
    )
    away_games = db.relationship(
        "Game", foreign_keys="Game.away_team_id", backref="away_team", lazy="dynamic"
    )

    def __repr__(self):
        return f"<Team {self.name}>"


class Stadium(db.Model):
    __tablename__ = "stadiums"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)

    games = db.relationship("Game", backref="stadium", lazy="dynamic")

    def __repr__(self):
        return f"<Stadium {self.name}>"


class Game(db.Model):
    __tablename__ = "games"

    id = db.Column(db.Integer, primary_key=True)
    home_team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    stadium_id = db.Column(db.Integer, db.ForeignKey("stadiums.id"), nullable=True)
    location = db.Column(db.String(200))
    match_datetime = db.Column(db.DateTime, nullable=False)
    home_score = db.Column(db.Integer, nullable=True)
    away_score = db.Column(db.Integer, nullable=True)
    status = db.Column(
        db.String(20), default="scheduled"
    )  # scheduled, live, finished, cancelled
    round_name = db.Column(db.String(100))
    group_name = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bets = db.relationship("Bet", backref="game", lazy="dynamic")

    @property
    def is_finished(self):
        return self.status == "finished"

    @property
    def bet_count(self):
        return self.bets.count()

    @property
    def result_display(self):
        if self.home_score is not None and self.away_score is not None:
            return f"{self.home_score} x {self.away_score}"
        return "-"

    def __repr__(self):
        return f"<Game {self.home_team.name} vs {self.away_team.name}>"


class Bet(db.Model):
    __tablename__ = "bets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"), nullable=False)
    home_score = db.Column(db.Integer, nullable=False)
    away_score = db.Column(db.Integer, nullable=False)
    points_earned = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "game_id", name="uq_user_game_bet"),
    )

    def calculate_points(self, config):
        """Calculate points based on bet vs actual result."""
        game = self.game
        if not game.is_finished or game.home_score is None:
            return 0

        # Exact score match
        if self.home_score == game.home_score and self.away_score == game.away_score:
            self.points_earned = config.correct_score_points
            return self.points_earned

        # Correct winner or draw
        actual_result = _get_result(game.home_score, game.away_score)
        bet_result = _get_result(self.home_score, self.away_score)

        if actual_result == bet_result:
            if actual_result == "draw":
                self.points_earned = config.correct_draw_points
            else:
                self.points_earned = config.correct_winner_points
        else:
            self.points_earned = 0

        return self.points_earned

    def __repr__(self):
        return f"<Bet user={self.user_id} game={self.game_id}>"


def _get_result(home, away):
    if home > away:
        return "home"
    elif away > home:
        return "away"
    return "draw"


class PointConfig(db.Model):
    __tablename__ = "point_configs"

    id = db.Column(db.Integer, primary_key=True)
    correct_score_points = db.Column(db.Integer, default=3, nullable=False)
    correct_winner_points = db.Column(db.Integer, default=1, nullable=False)
    correct_draw_points = db.Column(db.Integer, default=1, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    @classmethod
    def get_current(cls):
        config = cls.query.first()
        if not config:
            config = cls(
                correct_score_points=3,
                correct_winner_points=1,
                correct_draw_points=1,
            )
            db.session.add(config)
            db.session.commit()
        return config


class ApiEndpoint(db.Model):
    __tablename__ = "api_endpoints"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    api_key_header = db.Column(db.String(100))
    api_key_value = db.Column(db.String(300))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ApiEndpoint {self.name}>"
