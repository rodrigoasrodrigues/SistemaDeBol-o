"""
Tests for the Bolão Copa 2026 Flask application.
These tests use an in-memory SQLite database and do not require MySQL.
"""
import pytest
from app import create_app
from app.models import db as _db, User, Team, Stadium, Game, Bet, PointConfig
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

import uuid


def _uid():
    return uuid.uuid4().hex[:8]


@pytest.fixture(scope="session")
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope="function")
def db(app):
    """Each test runs inside a savepoint that is rolled back afterwards."""
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()
        # Bind the session to this connection so the savepoint rolls back cleanly
        _db.session.bind = connection  # type: ignore[assignment]
        _db.session.begin_nested()

        yield _db

        _db.session.rollback()
        transaction.rollback()
        connection.close()
        _db.session.remove()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def admin_user(db):
    u = _uid()
    user = User(username=f"admin_{u}", email=f"admin_{u}@test.com", is_admin=True)
    user.set_password("adminpass")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope="function")
def regular_user(db):
    u = _uid()
    user = User(username=f"user_{u}", email=f"user_{u}@test.com", is_admin=False)
    user.set_password("userpass")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope="function")
def two_teams(db):
    u = _uid()
    t1 = Team(name=f"Brasil_{u}", country_code="BRA")
    t2 = Team(name=f"Argentina_{u}", country_code="ARG")
    db.session.add_all([t1, t2])
    db.session.commit()
    return t1, t2


@pytest.fixture(scope="function")
def future_game(db, two_teams):
    t1, t2 = two_teams
    game = Game(
        home_team_id=t1.id,
        away_team_id=t2.id,
        match_datetime=datetime.utcnow() + timedelta(days=1),
        status="scheduled",
    )
    db.session.add(game)
    db.session.commit()
    return game


@pytest.fixture(scope="function")
def finished_game(db, two_teams):
    t1, t2 = two_teams
    game = Game(
        home_team_id=t1.id,
        away_team_id=t2.id,
        match_datetime=datetime.utcnow() - timedelta(days=1),
        status="finished",
        home_score=2,
        away_score=1,
    )
    db.session.add(game)
    db.session.commit()
    return game


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class TestUserModel:
    def test_password_hashing(self, db):
        user = User(username="hashtest", email="hash@test.com")
        user.set_password("mysecretpassword")
        assert user.check_password("mysecretpassword")
        assert not user.check_password("wrongpassword")

    def test_total_points_empty(self, db, regular_user):
        assert regular_user.total_points == 0

    def test_total_points_with_bets(self, db, regular_user, finished_game):
        config = PointConfig.get_current()
        bet = Bet(
            user_id=regular_user.id,
            game_id=finished_game.id,
            home_score=2,
            away_score=1,
            points_earned=config.correct_score_points,
        )
        db.session.add(bet)
        db.session.commit()
        assert regular_user.total_points == config.correct_score_points


class TestBetModel:
    def test_exact_score_points(self, db, regular_user, finished_game):
        config = PointConfig.get_current()
        bet = Bet(
            user_id=regular_user.id,
            game_id=finished_game.id,
            home_score=finished_game.home_score,
            away_score=finished_game.away_score,
        )
        db.session.add(bet)
        db.session.commit()
        pts = bet.calculate_points(config)
        assert pts == config.correct_score_points

    def test_correct_winner_points(self, db, regular_user, finished_game):
        config = PointConfig.get_current()
        # Correct winner (home wins), wrong score
        bet = Bet(
            user_id=regular_user.id,
            game_id=finished_game.id,
            home_score=3,
            away_score=0,
        )
        db.session.add(bet)
        db.session.commit()
        pts = bet.calculate_points(config)
        assert pts == config.correct_winner_points

    def test_wrong_bet_points(self, db, regular_user, finished_game):
        config = PointConfig.get_current()
        # Home won 2-1; bettor says away wins
        bet = Bet(
            user_id=regular_user.id,
            game_id=finished_game.id,
            home_score=0,
            away_score=2,
        )
        db.session.add(bet)
        db.session.commit()
        pts = bet.calculate_points(config)
        assert pts == 0


class TestPointConfig:
    def test_get_current_creates_default(self, db):
        config = PointConfig.get_current()
        assert config is not None
        assert config.correct_score_points == 3
        assert config.correct_winner_points == 1
        assert config.correct_draw_points == 1


class TestGameModel:
    def test_bet_count(self, db, future_game, regular_user):
        assert future_game.bet_count == 0
        bet = Bet(
            user_id=regular_user.id,
            game_id=future_game.id,
            home_score=1,
            away_score=0,
        )
        db.session.add(bet)
        db.session.commit()
        assert future_game.bet_count == 1

    def test_result_display(self, db, finished_game):
        assert finished_game.result_display == "2 x 1"

    def test_is_finished(self, db, finished_game, future_game):
        assert finished_game.is_finished
        assert not future_game.is_finished


# ---------------------------------------------------------------------------
# Route tests
# ---------------------------------------------------------------------------

class TestAuthRoutes:
    def test_register_get(self, client):
        resp = client.get("/auth/register")
        assert resp.status_code == 200
        assert b"Criar Conta" in resp.data

    def test_login_get(self, client):
        resp = client.get("/auth/login")
        assert resp.status_code == 200
        assert b"Entrar" in resp.data

    def test_login_invalid(self, client, app):
        with app.app_context():
            resp = client.post(
                "/auth/login",
                data={
                    "email": "nonexistent@test.com",
                    "password": "wrongpass",
                    "csrf_token": _get_csrf(client, "/auth/login"),
                },
                follow_redirects=True,
            )
            assert resp.status_code == 200


class TestMainRoutes:
    def test_index(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Copa" in resp.data

    def test_games_list(self, client):
        resp = client.get("/games")
        assert resp.status_code == 200

    def test_place_bet_requires_login(self, client, future_game):
        resp = client.get(f"/games/{future_game.id}/bet", follow_redirects=True)
        assert resp.status_code == 200
        assert b"login" in resp.data.lower()

    def test_my_bets_requires_login(self, client):
        resp = client.get("/my-bets", follow_redirects=True)
        assert resp.status_code == 200
        assert b"login" in resp.data.lower()


class TestAdminRoutes:
    def test_admin_requires_login(self, client):
        resp = client.get("/admin/", follow_redirects=True)
        assert resp.status_code == 200

    def test_admin_dashboard_forbidden_for_regular(self, client, app, regular_user):
        with app.app_context():
            with client.session_transaction() as sess:
                sess["_user_id"] = str(regular_user.id)
        resp = client.get("/admin/")
        assert resp.status_code == 403

    def test_admin_dashboard_ok_for_admin(self, client, app, admin_user):
        with app.app_context():
            with client.session_transaction() as sess:
                sess["_user_id"] = str(admin_user.id)
        resp = client.get("/admin/")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _get_csrf(client, url):
    """Retrieve CSRF token from a page."""
    from html.parser import HTMLParser

    class CsrfParser(HTMLParser):
        token = None
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == "input" and attrs.get("name") == "csrf_token":
                self.token = attrs.get("value")

    resp = client.get(url)
    parser = CsrfParser()
    parser.feed(resp.data.decode())
    return parser.token or ""
