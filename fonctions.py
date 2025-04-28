from models import User
from flask import session, redirect, url_for, flash
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from models import Promotion
# from app import db
def is_admin():
    #verifier si l'tat de l'utilisateur est admin
    return session.get('role') == 'admin'

def authenticate_admin(user):
    if user is None:
        return False  # L'utilisateur n'est pas connecté
    if user.role == "admin":
        return True
    return False

def get_current_user():
    user_id = session.get('user_id')  # Récupérer l'ID de l'utilisateur depuis la session
    if user_id:
        return User.query.get(user_id)  # Rechercher l'utilisateur dans la base de données
    return None  # Retourner None si aucun utilisateur n'est connecté

