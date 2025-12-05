
# backend/manage.py
from flask import Flask
from flask_migrate import Migrate
from app import create_app
from app.extensions import db
from app.models import *  # noqa


app: Flask = create_app("dev")
migrate = Migrate(app, db)


if __name__ == "__main__":
    # 这样你可以：python manage.py run / flask --app manage.py db migrate
    app.run(host="0.0.0.0", port=5000, debug=True)
