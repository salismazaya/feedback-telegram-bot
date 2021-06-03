from flask_sqlalchemy import SQLAlchemy
import os

class Models:
    def __init__(self, app):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///data.db')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = 1
        self.db = SQLAlchemy(app)

        class Bot(self.db.Model):
            id = self.db.Column(self.db.Integer, primary_key = True)
            username = self.db.Column(self.db.String(30), unique = True, nullable = False)
            token = self.db.Column(self.db.String(200), unique = True, nullable = False)
            owner = self.db.Column(self.db.Integer, nullable = False)
            start_message = self.db.Column(self.db.Text, nullable = False)

        self.Bot = Bot
        self.db.create_all()