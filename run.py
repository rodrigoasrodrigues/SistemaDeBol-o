import os
from app import create_app
from app.models import db, User, PointConfig

app = create_app(os.environ.get("FLASK_ENV", "default"))


@app.cli.command("create-admin")
def create_admin():
    """Create the default admin user."""
    import click

    username = click.prompt("Admin username", default="admin")
    email = click.prompt("Admin email", default="admin@bolao.local")
    password = click.prompt("Password", hide_input=True, confirmation_prompt=True)

    with app.app_context():
        existing = User.query.filter_by(email=email).first()
        if existing:
            click.echo("User already exists.")
            return
        user = User(username=username, email=email, is_admin=True)
        user.set_password(password)
        db.session.add(user)

        # Ensure default point config exists
        PointConfig.get_current()

        db.session.commit()
        click.echo(f"Admin user '{username}' created successfully.")


@app.cli.command("seed-db")
def seed_db():
    """Seed the database with World Cup 2026 teams and stadiums."""
    import click

    with app.app_context():
        from app.models import Team, Stadium
        from datetime import datetime

        teams_data = [
            ("Brasil", "BRA", "https://flagcdn.com/w40/br.png"),
            ("Argentina", "ARG", "https://flagcdn.com/w40/ar.png"),
            ("França", "FRA", "https://flagcdn.com/w40/fr.png"),
            ("Inglaterra", "ENG", "https://flagcdn.com/w40/gb-eng.png"),
            ("Alemanha", "GER", "https://flagcdn.com/w40/de.png"),
            ("Espanha", "ESP", "https://flagcdn.com/w40/es.png"),
            ("Portugal", "POR", "https://flagcdn.com/w40/pt.png"),
            ("Holanda", "NED", "https://flagcdn.com/w40/nl.png"),
            ("Itália", "ITA", "https://flagcdn.com/w40/it.png"),
            ("Croácia", "CRO", "https://flagcdn.com/w40/hr.png"),
            ("Marrocos", "MAR", "https://flagcdn.com/w40/ma.png"),
            ("Japão", "JPN", "https://flagcdn.com/w40/jp.png"),
            ("Estados Unidos", "USA", "https://flagcdn.com/w40/us.png"),
            ("México", "MEX", "https://flagcdn.com/w40/mx.png"),
            ("Canadá", "CAN", "https://flagcdn.com/w40/ca.png"),
            ("Uruguai", "URU", "https://flagcdn.com/w40/uy.png"),
        ]

        stadiums_data = [
            ("MetLife Stadium", "East Rutherford (NJ)", "Estados Unidos"),
            ("Rose Bowl", "Los Angeles (CA)", "Estados Unidos"),
            ("AT&T Stadium", "Arlington (TX)", "Estados Unidos"),
            ("Levi's Stadium", "Santa Clara (CA)", "Estados Unidos"),
            ("Hard Rock Stadium", "Miami (FL)", "Estados Unidos"),
            ("SoFi Stadium", "Los Angeles (CA)", "Estados Unidos"),
            ("Estadio Azteca", "Cidade do México", "México"),
            ("Estadio BBVA", "Monterrey", "México"),
            ("BC Place", "Vancouver", "Canadá"),
            ("BMO Field", "Toronto", "Canadá"),
        ]

        added_teams = 0
        for name, code, flag in teams_data:
            if not Team.query.filter_by(country_code=code).first():
                db.session.add(Team(name=name, country_code=code, flag_url=flag))
                added_teams += 1

        added_stadiums = 0
        for name, city, country in stadiums_data:
            if not Stadium.query.filter_by(name=name).first():
                db.session.add(Stadium(name=name, city=city, country=country))
                added_stadiums += 1

        PointConfig.get_current()
        db.session.commit()
        click.echo(
            f"Seeded {added_teams} teams and {added_stadiums} stadiums."
        )


if __name__ == "__main__":
    app.run()
