
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Picar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=False, unique=False)
    latitude = db.Column(db.String(64), index=False, unique=False)
    longitude = db.Column(db.String(64), index=False, unique=False)
    speed = db.Column(db.Float(2,2), index=False, unique=False)

    def __repr__(self):
        return '<Picar {}>'.format(self.id)
