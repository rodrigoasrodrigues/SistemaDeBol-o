import os
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .models import db, User
from config import config


login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix="/auth")

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix="/admin")

    def _ensure_default_admin():
        # Skip if table is not available yet (e.g. before init-db/migrations in production).
        if not inspect(db.engine).has_table("users"):
            return

        admin_email = app.config.get("DEFAULT_ADMIN_EMAIL")
        admin_username = app.config.get("DEFAULT_ADMIN_USERNAME")
        admin_password = app.config.get("DEFAULT_ADMIN_PASSWORD")

        if not admin_email or not admin_username or not admin_password:
            return

        existing = User.query.filter_by(email=admin_email).first()
        if existing:
            return

        admin = User(username=admin_username, email=admin_email, is_admin=True)
        admin.set_password(admin_password)
        db.session.add(admin)
        try:
            db.session.commit()
        except IntegrityError:
            # Another worker may have created the same admin concurrently.
            db.session.rollback()
        except SQLAlchemyError:
            db.session.rollback()
            app.logger.exception("Failed to auto-create default admin user")

    # Optional bootstrap for local development environments.
    if app.config.get("AUTO_DB_BOOTSTRAP", False):
        with app.app_context():
            db.create_all()
            from .models import PointConfig

            PointConfig.get_current()

    with app.app_context():
        _ensure_default_admin()

    return app
