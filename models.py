from flask_sqlalchemy import SQLAlchemy
from database import database

class users(database.Model):
    __tablename__ = "users"
    id = database.Column(database.Integer, primary_key = True)
    username = database.Column(database.Text, unique=True, nullable=False)
    hash = database.Column(database.Text, nullable=False)

    def __repr__(self):
        return "<users %r>" % self.username


class schedule(database.Model):
    __tablename__ = "schedule"
    username = database.Column(database.Text, nullable=False, primary_key = True)
    days = database.Column(database.Text, nullable=False, primary_key = True)
    times = database.Column(database.Text, nullable=False, primary_key = True)
    hometeam = database.Column(database.Text, nullable=False, primary_key = True)
    awayteam = database.Column(database.Text, nullable=False, primary_key = True)
    table1 = database.Column(database.Text)
    team_table1 = database.Column(database.Text)
    table2 = database.Column(database.Text)
    team_table2 = database.Column(database.Text)
    table3 = database.Column(database.Text)
    team_table3 = database.Column(database.Text)
    zaalco = database.Column(database.Text)
    team_zaalco = database.Column(database.Text)
    referee1 = database.Column(database.Text)
    team_referee1 = database.Column(database.Text)
    referee2 = database.Column(database.Text)
    team_referee2 = database.Column(database.Text)
