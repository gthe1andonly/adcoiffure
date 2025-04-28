from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
# Initialisation des extensions
db = SQLAlchemy()



class User(db.Model, UserMixin):  # Hériter de UserMixin
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user' ou 'admin'
    status = db.Column(db.String(20), default='secondaire')  # 'secondaire' ou 'principal'

    reservations = db.relationship('Reservation', backref='user', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(200), nullable=True)  # Chemin vers l'image
    reservations = db.relationship('Reservation', backref='service', lazy=True)

    def __repr__(self):
        return f"<Service {self.name}>"

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(50), default="pending...")  # 'pending', 'confirmed', 'cancelled'

    def __repr__(self):
        return f"<Reservation {self.id}>"
class Promotion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=False)
    image = db.Column(db.String(200), nullable=True)  # Chemin vers l'image