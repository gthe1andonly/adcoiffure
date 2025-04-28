from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from datetime import datetime, time as dt_time
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import os
from models import db, User, Service, Reservation, Promotion   # Importer depuis models.py
from fonctions import is_admin, authenticate_admin, get_current_user # Importer la fonction is_admin depuis fonctions.py
from apscheduler.schedulers.background import BackgroundScheduler
from flask_mail import Mail, Message
from collections import Counter
import random
import time
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask import make_response
import secrets
from itsdangerous import URLSafeTimedSerializer  # Pour générer des tokens sécurisés



# Initialisation de l'application Flask
app = Flask(__name__)
# Configuration de Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'adcoiffuredumonde@gmail.com'  # Remplacez par votre email
app.config['MAIL_PASSWORD'] = ''  # Remplacez par votre mot de passe
mail = Mail(app)

app.secret_key = 'secrets.token_hex(16)'  # Clé secrète pour les sessions
# Configuration de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Page de connexion par défaut

# Configuration de la base de données (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///adcoiffure.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuration pour le téléchargement d'images
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static', 'images')

# Initialisation des extensions
db.init_app(app)
bcrypt = Bcrypt(app)

# Création des tables dans larelle2005 données
with app.app_context():
    db.create_all()
    # password = arelleadelphe20052004te_password_hash("arelle").decode('utf-8')
    # admin =User(username = "arelle",email="oviane94@gmail.com",password_hash=password,role="admin")
    # db.session.add(admin)
    # db.session.commit()
from itsdangerous import URLSafeTimedSerializer  # Pour générer des tokens sécurisés
from flask_mail import Message

# Serializer pour générer des tokens sécurisés
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if user:
            # Générer un token unique pour l'utilisateur
            token = serializer.dumps(email, salt='password-reset-salt')

            # Créer le lien de réinitialisation
            reset_link = url_for('reset_password', token=token, _external=True)

            # Envoyer l'e-mail avec le lien de réinitialisation
            try:
                msg = Message(
                    subject="Password Reset Request",
                    sender=app.config['MAIL_USERNAME'],
                    recipients=[email]
                )
                msg.html = f"""
                <html>
                    <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; color: #333; padding: 20px;">
                        <div style="background-color: #ffffff; border-radius: 8px; padding: 20px; max-width: 600px; margin: 0 auto; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                            <h1 style="color: #ff6f61; font-size: 24px; text-align: center;">Password Reset</h1>
                            <p style="font-size: 16px; line-height: 1.5;">
                                Hello,<br><br>
                                You have requested to reset your password. Click the link below to set a new password:
                            </p>
                            <p style="text-align: center; margin: 20px 0;">
                                <a href="{reset_link}" style="display: inline-block; background-color: #3498db; color: #fff; font-size: 16px; font-weight: bold; padding: 15px 30px; border-radius: 6px; text-decoration: none;">
                                    Reset My Password
                                </a>
                            </p>
                            <p style="font-size: 14px; color: #777;">
                                If you did not request this password reset, please ignore this email.
                            </p>
                        </div>
                    </body>
                </html>
                """
                mail.send(msg)
                flash("An email with instructions to reset your password has been sent.", "info")
            except Exception as e:
                flash("An error occurred while sending the email. Please try again later.", "error")
        else:
            flash("No account found with this email.", "error")

    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        # Vérifier et décoder le token
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)  # Token valide pendant 1 heure
    except Exception:
        flash("The reset link is invalid or has expired.", "error")
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for('reset_password', token=token))

        if len(new_password) < 8:
            flash("The password must be at least 8 characters long.", "error")
            return redirect(url_for('reset_password', token=token))

        # Mettre à jour le mot de passe de l'utilisateur
        user = User.query.filter_by(email=email).first()
        if user:
            user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
            db.session.commit()
            flash("Your password has been successfully reset.", "success")
            return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)

@app.route('/')
def index():
    try:
        # Récupérer l'utilisateur actuel
        user = get_current_user()

        # Vérifier si l'utilisateur est connecté
        isConnect = user is not None

        # Vérifier si l'utilisateur est administrateur (si connecté)
        isAdmin = authenticate_admin(user) if user else False

        # Passer les données au template
        return render_template('index.html', isAdmin=isAdmin, isConnect=isConnect)

    except Exception as e:
        # Capturer toutes les erreurs (par exemple, erreurs de base de données ou de rendu de template)
        flash(f"An error occurred while loading the homepage. Please try again later. Error: {str(e)}", "error")
        return redirect(url_for('error_page'))  # Rediriger vers une page d'erreur générique

@app.route('/about')
def about():
    try:
        # Récupérer l'utilisateur actuel
        user = get_current_user()

        # Vérifier si l'utilisateur est connecté
        isConnect = user is not None

        # Vérifier si l'utilisateur est administrateur (si connecté)
        isAdmin = authenticate_admin(user) if user else False

        # Passer les données au template

        return render_template('about.html', isConnect=isConnect, isAdmim=isAdmin)

        
        

    except Exception as e:
        # Capturer toutes les erreurs (par exemple, erreurs de base de données ou de rendu de template)
        flash(f"An error occurred while loading the homepage. Please try again later. Error: {str(e)}", "error")
        return redirect(url_for('error_page'))  # Rediriger vers une page d'erreur générique

@app.route('/gallery')
def gallery():
    try:
        user = get_current_user()
        if user.role == "admin":
            # Récupérer les services par catégorie
            braids_services = Service.query.filter_by(category="braids").all()
            chemical_services = Service.query.filter_by(category="treatment").all()
            extensions_services = Service.query.filter_by(category="extensions").all()

            # Récupérer tous les services
            services = Service.query.all()

            # Passer les données au template
            return render_template(
                'gallery.html',
                braids_services=braids_services,
                chemical_services=chemical_services,
                extensions_services=extensions_services,
                services=services
            )
        else:
            flash("Access denied ")
            return redirect(url_for('index'))
    except Exception as e:
        # Capturer toutes les erreurs (par exemple, erreurs de base de données ou de rendu de template)
        flash(f"An error occurred while loading the gallery. Please try again later.", "error")
        return redirect(url_for('index'))  # Rediriger vers la page d'accueil en cas d'erreur
    
@app.route('/contactus')
def contactus():
    try:
        # Récupérer l'utilisateur actuel
        user = get_current_user()

        # Vérifier si l'utilisateur est connecté
        isConnect = user is not None

        # Vérifier si l'utilisateur est administrateur (si connecté)
        isAdmin = authenticate_admin(user) if user else False

        # Passer les données au template

        
        return render_template('contactus.html', isConnect=isConnect, isAdmim=isAdmin)

        
        

    except Exception as e:
        # Capturer toutes les erreurs (par exemple, erreurs de base de données ou de rendu de template)
        flash(f"An error occurred while loading the homepage. Please try again later. Error: {str(e)}", "error")
        return redirect(url_for('error_page'))  # Rediriger vers une page d'erreur générique

    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validation des champs
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for('register'))
        if len(password) < 8:
            flash("The password must be at least 8 characters long.", "error")
            return redirect(url_for('register'))
        if User.query.filter_by(phone=phone).first():
            flash("This phone number is already taken.", "error")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash("This email is already registered.", "error")
            return redirect(url_for('register'))

        # Générer un OTP et stocker le timestamp
        otp = str(random.randint(100000, 999999))  # Génère un code à 6 chiffres
        session['otp'] = otp
        session['otp_timestamp'] = time.time()  # Stocker le timestamp actuel
        session['registration_data'] = {
            'username': username,
            'phone': phone,
            'email': email,
            'password': password
        }

        # Envoyer l'OTP par e-mail
        try:
            msg = Message(
                subject="Your OTP for Registration",
                sender="adcoiffuredumonde@gmail.com",
                recipients=[email]
            )
            msg.body = f"Your OTP for registration is: {otp}. This OTP is valid for 5 minutes. Do not share it with anyone."
            mail.send(msg)

            flash("An OTP has been sent to your email. Please verify your email address.", "info")
            return redirect(url_for('verify_otp'))  # Rediriger vers la page de vérification OTP

        except Exception as e:
            flash(f"Failed to send OTP. Please try again later. Error: {str(e)}", "error")
            return redirect(url_for('register'))

    return render_template('register.html')  # Page d'inscription

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        stored_otp = session.get('otp')
        otp_timestamp = session.get('otp_timestamp')

        # Vérifier si l'OTP a expiré (5 minutes = 300 secondes)
        if otp_timestamp and (time.time() - otp_timestamp > 300):
            flash("OTP has expired. Please request a new one.", "error")
            return redirect(url_for('resend_otp'))  # Rediriger vers la page de renvoi OTP

        if entered_otp == stored_otp:
            # OTP valide, enregistrer l'utilisateur dans la base de données
            registration_data = session.get('registration_data')
            if registration_data:
                hashed_password = bcrypt.generate_password_hash(registration_data['password']).decode('utf-8')
                new_user = User(
                    username=registration_data['username'],
                    email=registration_data['email'],
                    phone=registration_data['phone'],
                    password_hash=hashed_password
                )

                try:
                    db.session.add(new_user)
                    db.session.commit()
                    session.pop('otp', None)  # Nettoyer l'OTP de la session
                    session.pop('otp_timestamp', None)
                    session.pop('registration_data', None)  # Nettoyer les données de l'utilisateur
                    flash("Email verified successfully! You can now log in.", "success")
                    return redirect(url_for('login'))
                except Exception as e:
                    db.session.rollback()
                    flash(f"An error occurred during registration. Please try again. Error ", "error")
                    return redirect(url_for('register'))
            else:
                flash("Registration data not found. Please try again.", "error")
                return redirect(url_for('register'))
        else:
            flash("Invalid OTP. Please try again.", "error")
            return redirect(url_for('verify_otp'))

    return render_template('verify_otp.html')  # Page pour entrer l'OTP

@app.route('/resend-otp', methods=['GET', 'POST'])
def resend_otp():
    registration_data = session.get('registration_data')
    if not registration_data:
        flash("No pending registration found. Please start over.", "error")
        return redirect(url_for('register'))

    # Générer un nouveau OTP
    otp = str(random.randint(100000, 999999))
    session['otp'] = otp
    session['otp_timestamp'] = time.time()  # Mettre à jour le timestamp

    # Envoyer le nouvel OTP par e-mail
    try:
        msg = Message("Your New OTP for Registration", sender="your_email@example.com", recipients=[registration_data['email']])
        msg.body = f"Your new OTP for registration is: {otp}"
        mail.send(msg)
        flash("A new OTP has been sent to your email. Please verify your email address.", "info")
        return redirect(url_for('verify_otp'))
    except Exception as e:
        flash(f"Failed to send OTP. Please try again later. Error: ", "error")
        return redirect(url_for('resend_otp'))
from flask import request, redirect, url_for, flash, session, make_response

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        remember_me = 'remember_me' in request.form  # Checkbox "Remember Me"

        # Vérification des identifiants de l'utilisateur
        user = User.query.filter_by(email=email).first()
        try:
            if user and bcrypt.check_password_hash(user.password_hash, password):
                # Stocker l'ID de l'utilisateur dans la session
                session['user_id'] = user.id
                session['role'] = 'admin' if user.role == 'admin' else 'user'

                # Si "Remember Me" est coché, créer un cookie persistant
                if remember_me:
                    resp = make_response(redirect(url_for('index')))
                    resp.set_cookie('user_id', str(user.id), max_age=60*60*24*7)  # Cookie valide pendant 7 jours
                    resp.set_cookie('role', user.role, max_age=60*60*24*7)  # Cookie pour le rôle
                    flash("Login successful with Remember Me enabled!", "success")
                    return resp

                flash("Login successful!", "success")
                return redirect(url_for('index'))

            # Si les identifiants sont incorrects
            flash("Invalid email or password.", "error")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.before_request
def load_user_from_cookie():
    if 'user_id' not in session:  # Si l'utilisateur n'est pas déjà connecté via la session
        user_id = request.cookies.get('user_id')  # Récupérer l'ID depuis le cookie
        role = request.cookies.get('role')  # Récupérer le rôle depuis le cookie

        if user_id and role:
            user = User.query.get(int(user_id))  # Charger l'utilisateur depuis la base de données
            if user:
                # Recréer la session à partir des cookies
                session['user_id'] = user.id
                session['role'] = role  # Stocker le rôle dans la session

@login_manager.user_loader
def load_user(user_id):
    # Charger l'utilisateur à partir de la base de données
    return User.query.get(int(user_id))




@app.route('/logout')
def logout():
    # Supprimer les cookies "Remember Me"
    resp = make_response(redirect(url_for('index')))
    resp.set_cookie('user_id', '', expires=0)  # Supprimer le cookie user_id
    resp.set_cookie('role', '', expires=0)  # Supprimer le cookie role

    # Effacer la session
    session.clear()

    flash("You have been logged out successfully.", "success")
    return resp


@app.route('/book-appointment/<int:service_id>', methods=['GET', 'POST'])
def book_appointment(service_id):
    # Vérifier si l'utilisateur est connecté
    if 'user_id' not in session:
        flash("Please log in to book an appointment.", "error")
        return redirect(url_for('login'))

    # Récupérer le service correspondant à l'ID
    service = Service.query.get_or_404(service_id)

    if request.method == 'POST':
        # Récupérer les données du formulaire
        
        selected_date = request.form['date']
        selected_time = request.form['time']

        # Convertir la date et l'heure en objets datetime
        try:
            date = datetime.strptime(selected_date, '%Y-%m-%d').date()
            time_selected = datetime.strptime(selected_time, '%H:%M').time()
        except ValueError:
            flash("Invalid date or time format.", "error")
            return redirect(url_for('book_appointment', service_id=service_id))

        # Vérifier si la date est déjà passée
        current_datetime = datetime.now()
        selected_datetime = datetime.combine(date, time_selected)
        if selected_datetime < current_datetime:
            flash("You cannot book an appointment for a past date or time.", "error")
            return redirect(url_for('book_appointment', service_id=service_id))

        

        # Créer une nouvelle réservation
        user_id = session['user_id']
        new_reservation = Reservation(
            user_id=user_id,
            service_id=service.id,
            date=date,
            time=time_selected
        )

        # Ajouter la réservation à la base de données
        db.session.add(new_reservation)
        db.session.commit()

        flash("Appointment booked successfully!", "success")
        return redirect(url_for('appointments'))

    # Afficher le formulaire de réservation pour une requête GET
    return render_template('book-appointment.html', user=User.query.get(session['user_id']), service=service)
@app.route('/appointments/<int:reservation_id>')
def appointment_details(reservation_id):
    try:
        # Vérifier si l'utilisateur est connecté
        if 'user_id' not in session:
            flash("Please log in to view your appointment details.", "error")
            return redirect(url_for('login'))

        # Récupérer la réservation ou renvoyer une erreur 404 si elle n'existe pas
        reservation = Reservation.query.get_or_404(reservation_id)

        # Vérifier si l'utilisateur actuel est autorisé à accéder à cette réservation
        if reservation.user_id != session['user_id']:
            flash("Access denied.", "error")
            return redirect(url_for('appointments'))

        # Rendre le template avec les détails de la réservation
        return render_template('appointment-details.html', reservation=reservation)

    except Exception as e:
        # Capturer toutes les erreurs (par exemple, erreurs de base de données)
        flash(f"An error occurred while loading the appointment details. Please try again later. Error: {str(e)}", "error")
        return redirect(url_for('appointments'))
    
@app.route('/appointments')
def appointments():
    try:
        # Vérifier si l'utilisateur est connecté
        if 'user_id' not in session:
            flash("Please log in to view your appointments.", "error")
            return redirect(url_for('login'))

        # Initialiser les variables
        user_id = None
        isConnect = False
        user = None
        isAdmin = False

        # Vérifier si l'utilisateur est connecté
        if 'user_id' in session:
            isConnect = True
            user_id = session['user_id']
            user = User.query.filter_by(id=user_id).first()

            # Vérifier si l'utilisateur est un administrateur
            if user:
                isAdmin = authenticate_admin(user)
            else:
                flash("User not found.", "error")
                return redirect(url_for('login'))

        # Récupérer les réservations de l'utilisateur
        user_reservations = Reservation.query.filter_by(user_id=session['user_id']).all()

        # Passer les données au template
        return render_template(
            'appointments.html',
            reservations=user_reservations,
            isAdmin=isAdmin,
            isConnect=isConnect
        )

    except Exception as e:
        # Capturer toutes les erreurs (par exemple, erreurs de base de données)
        flash(f"An error occurred while loading your appointments. Please try again later. Error: {str(e)}", "error")
        return redirect(url_for('index'))


@app.route('/edit-reservation/<int:reservation_id>', methods=['GET', 'POST'])
def edit_reservation(reservation_id):
    # Récupérer la réservation ou renvoyer une erreur 404 si elle n'existe pas
    reservation = Reservation.query.get_or_404(reservation_id)

    # Vérifier si l'utilisateur actuel est autorisé à modifier cette réservation
    if reservation.user_id != session['user_id']:
        flash("Access denied.", "error")
        return redirect(url_for('appointments'))

    # Vérifier si la réservation est déjà annulée, validée ou rejetée
    if reservation.status == 'Canceled':
        flash("Reservation is already canceled.", "error")
        return redirect(url_for('appointments'))
    if reservation.status == 'Validated':
        flash("Reservation is already validated.", "error")
        return redirect(url_for('appointments'))
    if reservation.status == 'Denied':
        flash("Reservation is already denied.", "error")
        return redirect(url_for('appointments'))

    # Traitement du formulaire en cas de requête POST
    if request.method == 'POST':
        try:
            # Mettre à jour la date et l'heure de la réservation
            reservation.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            reservation.time = datetime.strptime(request.form['time'], '%H:%M').time()

            # Valider et enregistrer les modifications dans la base de données
            db.session.commit()

            # Afficher un message de succès
            flash("Appointment updated successfully!", "success")
            return redirect(url_for('appointments'))

        except ValueError as ve:
            # Capturer les erreurs liées au format de la date ou de l'heure
            db.session.rollback()  # Annuler les modifications en cas d'erreur
            flash(f"Invalid date or time format. Please try again. Error: {str(ve)}", "error")
            return redirect(url_for('edit_reservation', reservation_id=reservation_id))

        except Exception as e:
            # Capturer toutes les autres erreurs (par exemple, erreurs de base de données)
            db.session.rollback()  # Annuler les modifications en cas d'erreur
            flash(f"An error occurred while updating the appointment. Please try again later. Error: {str(e)}", "error")
            return redirect(url_for('edit_reservation', reservation_id=reservation_id))

    # Rendre le template HTML pour afficher le formulaire de modification
    return render_template('edit-reservation.html', reservation=reservation)

@app.route('/delete-reservation/<int:reservation_id>')
def delete_reservation(reservation_id):
    # Récupérer la réservation ou renvoyer une erreur 404 si elle n'existe pas
    reservation = Reservation.query.get_or_404(reservation_id)

    # Vérifier si l'utilisateur actuel est autorisé à supprimer cette réservation
    if reservation.user_id != session['user_id']:
        flash("Access denied.", "error")
        return redirect(url_for('appointments'))

    # Vérifier si la réservation est déjà validée
    if reservation.status == 'Validated':
        flash("Appointment is already validated and cannot be canceled.", "error")
        return redirect(url_for('appointments'))

    try:
        # Mettre à jour le statut de la réservation à "Canceled"
        reservation.status = 'Canceled'

        # Valider et enregistrer les modifications dans la base de données
        db.session.commit()

        # Afficher un message de succès
        flash("Appointment deleted successfully!", "success")

    except Exception as e:
        # Capturer toutes les erreurs (par exemple, erreurs de base de données)
        db.session.rollback()  # Annuler les modifications en cas d'erreur
        flash(f"An error occurred while deleting the appointment. Please try again later. Error: {str(e)}", "error")

    # Rediriger vers la page des rendez-vous
    return redirect(url_for('appointments'))

# Route pour ajouter des services (Admin)
@app.route('/add-service', methods=['GET', 'POST'])
def add_service():
    user = get_current_user()
    if not is_admin():
        flash("Access denied. Only administrators can add services.", "error")
        return redirect(url_for('index'))

    try:
        if user.role != 'admin':
            flash("Access denied. Only administrators can view the dashboard.", "error")
            return redirect(url_for('index'))
    except:
        flash("Access denied. Only administrators can view the dashboard.", "error")
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')  # Champ facultatif
        price = request.form.get('price')
        duration = request.form.get('duration')
        category = request.form.get('category')
        image = request.files.get('image')

        # Vérification des champs obligatoires (sauf description)
        if not name or not price or not duration or not category:
            flash("All required fields must be filled.", "error")
            return redirect(url_for('add_service'))

        # Validation du prix
        try:
            price = float(price)
        except ValueError:
            flash("Price must be a valid number.", "error")
            return redirect(url_for('add_service'))

        # Validation de l'image
        if not image or image.filename == '':
            flash("Image is required.", "error")
            return redirect(url_for('add_service'))

        # Vérification de l'extension du fichier
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}  # Extensions autorisées
        filename = secure_filename(image.filename)
        extension = filename.rsplit('.', 1)[-1].lower()  # Récupérer l'extension du fichier

        if extension not in allowed_extensions:
            flash("Invalid file type. Only images (PNG, JPG, JPEG, GIF) are allowed.", "error")
            return redirect(url_for('add_service'))

        # Chemin de sauvegarde du fichier
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Création du dossier de téléchargement s'il n'existe pas
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        # Sauvegarde de l'image
        try:
            image.save(file_path)
        except Exception as e:
            flash(f"Error saving image: {str(e)}", "error")
            return redirect(url_for('add_service'))

        # Ajout du service dans la base de données
        new_service = Service(
            name=name,
            description=description,  # Peut être None ou vide
            price=price,
            duration=duration,
            category=category,
            image=filename
        )
        db.session.add(new_service)
        db.session.commit()

        flash("Service added successfully!", "success")
        return redirect(url_for('gallery'))

    return render_template('add-service.html')

@app.route('/edit_service/<int:service_id>', methods=['GET', 'POST'])
def edit_service(service_id):
    if not is_admin():
        flash("Access denied. Only administrators can edit services.", "error")
        return redirect(url_for('index'))
    
    service = Service.query.filter_by(id=service_id).first()
    if not service:
        flash("Service not found.", "error")
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description') or service.description  # Keep existing if not provided
        price = request.form.get('price')
        duration = request.form.get('duration')
        category = request.form.get('category')

        # Gestion de l'image
        image = request.files.get('image')
        if image and image.filename != '':
            filename = secure_filename(image.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            image.save(file_path)
            service.image = filename

        # Validation des champs
        if not name or not price or not duration or not category:
            flash("Name, price, duration, and category are required.", "error")
            return redirect(url_for('edit_service', service_id=service_id))

        try:
            price = float(price)
        except ValueError:
            flash("Price must be a valid number.", "error")
            return redirect(url_for('edit_service', service_id=service_id))

        # Mise à jour des données du service
        service.name = name
        service.description = description
        service.price = price
        service.duration = duration
        service.category = category

        db.session.commit()
        flash("Service updated successfully!", "success")
        return redirect(url_for('gallery'))  # Redirection vers la galerie après mise à jour

    return render_template("edit-service.html", service=service)



#route pour supprimer un service
@app.route('/delete-service/<int:service_id>', methods=['POST'])
def delete_service(service_id):
    if not is_admin():
        flash("Access denied. Only administrators can delete services.", "error")
        return redirect(url_for('index'))
    
    # Récupérer le service à supprimer
    service = Service.query.get_or_404(service_id)
    
    try:
        db.session.delete(service)
        db.session.commit()
        flash("Service deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting service  ", "error")
    
    return redirect(url_for('gallery'))


@app.route('/search_admin')
def search_admin():
    user = get_current_user()
    if user.role == "admin":
        # Récupérer le terme de recherche depuis les paramètres de l'URL
        query = request.args.get('query', '').strip().lower()
        if not query:
            flash("Please enter a search term.", "error")
            return redirect(url_for('gallery'))  # Rediriger vers la page de la galerie si aucun terme n'est saisi

        # Rechercher les services correspondants dans la base de données
        services = Service.query.filter(
            db.or_(
                Service.name.ilike(f'%{query}%'),
                Service.category.ilike(f'%{query}%'),
                Service.description.ilike(f'%{query}%')
            )
        ).all()

        # Passer les résultats au template
        return render_template('search_admin.html', services=services, query=query)



# Route pour ajouter les promotions
@app.route('/add-promotion', methods=['GET', 'POST'])
def add_promotion():
    if not is_admin():
        flash("Access denied. Only administrators can add promotions.", "error")
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        date_debut = request.form.get('date_debut')
        date_fin = request.form.get('date_fin')
        image = request.files.get('image')

        # Validation des champs obligatoires
        if not name or not description or not date_debut or not date_fin:
            flash("All fields are required.", "error")
            return redirect(url_for('add_promotion'))

        # Validation de l'image
        if not image or image.filename == '':
            flash("Image is required.", "error")
            return redirect(url_for('add_promotion'))

        # Vérification de l'extension du fichier
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}  # Extensions autorisées
        filename = secure_filename(image.filename)
        extension = filename.rsplit('.', 1)[-1].lower()  # Récupérer l'extension du fichier

        if extension not in allowed_extensions:
            flash("Invalid file type. Only images (PNG, JPG, JPEG, GIF) are allowed.", "error")
            return redirect(url_for('add_promotion'))

        # Chemin de sauvegarde du fichier
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Création du dossier de téléchargement s'il n'existe pas
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        # Sauvegarde de l'image
        try:
            image.save(file_path)
        except Exception as e:
            flash(f"Error saving image: {str(e)}", "error")
            return redirect(url_for('add_promotion'))

        # Conversion des dates en objets `date`
        try:
            date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
            date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.", "error")
            return redirect(url_for('add_promotion'))

        # Création de la promotion
        new_promotion = Promotion(
            name=name,
            description=description,
            date_debut=date_debut_obj,
            date_fin=date_fin_obj,
            image=filename
        )
        db.session.add(new_promotion)
        db.session.commit()

        flash("Promotion added successfully!", "success")
        return redirect(url_for('promotions_admin'))
    
    return render_template('add-promotion.html')




@app.route('/edit-promotion/<int:promotion_id>', methods=['GET', 'POST'])
def edit_promotion(promotion_id):
    # Vérifier si l'utilisateur est administrateur
    if not is_admin():
        flash("Access denied. Only administrators can edit promotions.", "error")
        return redirect(url_for('index'))
    
    # Récupérer la promotion ou renvoyer une erreur 404 si elle n'existe pas
    promotion = Promotion.query.get_or_404(promotion_id)
    
    if request.method == 'POST':
        try:
            # Mettre à jour les champs de la promotion
            promotion.name = request.form.get('name')
            promotion.description = request.form.get('description')
            promotion.date_debut = datetime.strptime(request.form.get('date_debut'), '%Y-%m-%d').date()
            promotion.date_fin = datetime.strptime(request.form.get('date_fin'), '%Y-%m-%d').date()
            
            # Gestion de l'image
            image = request.files.get('image')
            if image and image.filename != '':
                filename = secure_filename(image.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Créer le dossier s'il n'existe pas
                image.save(file_path)
                promotion.image = filename
            
            # Valider et enregistrer les modifications dans la base de données
            db.session.commit()

            # Afficher un message de succès
            flash("Promotion updated successfully!", "success")
            return redirect(url_for('promotions_admin'))

        except ValueError as ve:
            # Capturer les erreurs liées au format des dates
            db.session.rollback()  # Annuler les modifications en cas d'erreur
            flash(f"Invalid date format. Please use the YYYY-MM-DD format. Error: {str(ve)}", "error")
            return redirect(url_for('edit_promotion', promotion_id=promotion_id))

        except Exception as e:
            # Capturer toutes les autres erreurs (par exemple, erreurs de base de données ou de fichier)
            db.session.rollback()  # Annuler les modifications en cas d'erreur
            flash(f"An error occurred while updating the promotion. Please try again later. Error: {str(e)}", "error")
            return redirect(url_for('edit_promotion', promotion_id=promotion_id))
    
    # Rendre le template HTML pour afficher le formulaire de modification
    return render_template('edit-promotion.html', promotion=promotion)

@app.route('/delete-promotion/<int:promotion_id>', methods=['POST'])
def delete_promotion(promotion_id):
    if not is_admin():
        flash("Access denied. Only administrators can delete promotions.", "error")
        return redirect(url_for('index'))
    
    promotion = Promotion.query.get_or_404(promotion_id)
    
    try:
        db.session.delete(promotion)
        db.session.commit()
        flash("Promotion deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting promotion: ", "error")
    
    return redirect(url_for('promotions_admin'))






@app.route('/promotions_admin')
def promotions_admin():
    promotions = Promotion.query.all()
    return render_template('promotions_admin.html', promotions=promotions)

@app.route('/promotions')
def promotions():
    try:
        # Récupérer l'utilisateur actuel
        user = get_current_user()

        # Vérifier si l'utilisateur est connecté
        isConnect = user is not None

        # Vérifier si l'utilisateur est administrateur (si connecté)
        isAdmin = authenticate_admin(user) if user else False

        # Passer les données au template

        all_promotions = Promotion.query.all()
        
        return render_template('promotions.html', promotions=all_promotions, isConnect=isConnect, isAdmim=isAdmin)

        
        

    except Exception as e:
        # Capturer toutes les erreurs (par exemple, erreurs de base de données ou de rendu de template)
        flash(f"An error occurred while loading the homepage. Please try again later. Error: {str(e)}", "error")
        return redirect(url_for('error_page'))  # Rediriger vers une page d'erreur générique




@app.route('/braidsgallery')
def braids_gallery():
    try:
        # Récupérer l'utilisateur actuel
        user = get_current_user()

        # Vérifier si l'utilisateur est connecté
        isConnect = user is not None

        # Vérifier si l'utilisateur est administrateur (si connecté)
        isAdmin = authenticate_admin(user) if user else False
        services = Service.query.filter_by(category="braids").all()
        # Passer les données au template
        return render_template('braidsgallery.html', services=services, isAdmin=isAdmin, isConnect=isConnect)
        
       

    except Exception as e:
        # Capturer toutes les erreurs (par exemple, erreurs de base de données ou de rendu de template)
        flash(f"An error occurred while loading the homepage. Please try again later. ", "error")
        return redirect(url_for('error_page'))  # Rediriger vers une page d'erreur générique

   

@app.route('/treatmentgallery')
def treatment_gallery():
    try:
        # Récupérer l'utilisateur actuel
        user = get_current_user()

        # Vérifier si l'utilisateur est connecté
        isConnect = user is not None

        # Vérifier si l'utilisateur est administrateur (si connecté)
        isAdmin = authenticate_admin(user) if user else False
        services = Service.query.filter_by(category="treatment").all()
        # Passer les données au template
        return render_template('treatmentgallery.html', services=services, isAdmin=isAdmin, isConnect=isConnect)
        
       

    except Exception as e:
        # Capturer toutes les erreurs (par exemple, erreurs de base de données ou de rendu de template)
        flash(f"An error occurred while loading the homepage. Please try again later. ", "error")
        return redirect(url_for('error_page'))  # Rediriger vers une page d'erreur générique
    
 

@app.route('/extensionsgallery')
def extensions_gallery():
    try:
        # Récupérer l'utilisateur actuel
        user = get_current_user()

        # Vérifier si l'utilisateur est connecté
        isConnect = user is not None

        # Vérifier si l'utilisateur est administrateur (si connecté)
        isAdmin = authenticate_admin(user) if user else False
        services = Service.query.filter_by(category="extensions").all()
        # Passer les données au template
        return render_template('extensionsgallery.html', services=services, isAdmin=isAdmin, isConnect=isConnect)
        
       

    except Exception as e:
        # Capturer toutes les erreurs (par exemple, erreurs de base de données ou de rendu de template)
        flash(f"An error occurred while loading the homepage. Please try again later. ", "error")
        return redirect(url_for('error_page'))  # Rediriger vers une page d'erreur générique
  
@app.route('/error')
def error_page():

    error_message = "An unexpected error occurred. Please try again later."
    return render_template('error_page.html', error_message=error_message), 500


@app.route('/validate-reservation/<int:reservation_id>', methods=['POST'])
def validate_reservation(reservation_id):
    try:
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if user.role != 'admin':
            flash('Access denied', 'error')
            return redirect(url_for('index'))
        # Assurez-vous que l'utilisateur a un e-mail valide
        if not user.email:
            flash("User does not have a valid email address.", "error")
            return redirect(url_for('admin_reservation'))
        
        reservation = Reservation.query.get_or_404(reservation_id)
        if reservation.status == 'Denied':
            flash("Reservation has been denied and cannot be validated.", "error")
            return redirect(url_for('admin_reservation'))
        
        reservation.status = 'Validated'
        db.session.commit()
        flash("Reservation validated successfully!", "success")
        
    except Exception as e:
        flash("An error occurred while validating the reservation. Please try again later.", "error")
        return redirect(url_for('admin_reservation'))
        # Envoi d'un e-mail de confirmation 
    try:
        msg = Message(
        subject="✨ Your Reservation Confirmation ✨",
        sender=app.config['MAIL_USERNAME'],
        recipients=[reservation.user.email],
        html=f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; color: #333; padding: 20px;">
                <div style="background-color: #ffffff; border-radius: 8px; padding: 20px; max-width: 600px; margin: 0 auto; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <h1 style="color: #ff6f61; font-size: 24px; text-align: center;">🎉 Reservation Confirmed! 🎉</h1>
                    <p style="font-size: 16px; line-height: 1.5;">
                        Hi {reservation.user.username}, 😊<br><br>
                        We're delighted to confirm your reservation for <strong>{reservation.service.name}</strong> ✂️ on <strong>{reservation.date}</strong> at <strong>{reservation.time}</strong>. ⏰<br><br>
                        If you have any questions or need to modify your reservation, feel free to reach out. We're here to help! 💬<br><br>
                        Thank you for choosing AdCoiffure Du Monde. See you soon! ❤️
                    </p>
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    <p style="text-align: center; font-size: 14px; color: #777;">
                        <strong>AdCoiffure Du Monde</strong><br>
                        ✉️ Email: adcoiffuredumonde@gmail.com<br>
                        📞 Phone: +1 (240) 421-6230<br>
                        🌐 Website: adcoiffure.com
                    </p>
                </div>
            </body>
        </html>
        """
        )
        mail.send(msg)
        flash("Confirmation email sent to the client.", "success")
    except Exception as e:
        flash(f"Failed to send confirmation email ", "error")
        return render_template('error_page.html'), 500


    return redirect(url_for('admin_reservation'))



@app.route('/reject-reservation/<int:reservation_id>', methods=['POST'])
def reject_reservation(reservation_id):
    try:
        # Vérifier si l'utilisateur est connecté
        if 'user_id' not in session:
            flash("You need to be logged in to perform this action.", "error")
            return redirect(url_for('login'))

        # Récupérer l'utilisateur actuel
        user = User.query.get(session['user_id'])

        # Vérifier si l'utilisateur est un administrateur
        if user.role != 'admin':
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        # Récupérer la réservation ou renvoyer une erreur 404 si elle n'existe pas
        reservation = Reservation.query.get_or_404(reservation_id)
        if reservation.status == 'Validated':
            flash("Reservation has been validated and cannot be denied.", "error")
            return redirect(url_for('admin_reservation'))
        
        # Mettre à jour le statut de la réservation
        reservation.status = 'Denied'

        # Enregistrer les modifications dans la base de données
        db.session.commit()

        # Envoyer un e-mail au client pour informer du rejet
        try:
            # Créer le message
            msg = Message(
                subject="Your Reservation Has Been Denied",
                sender="adcoiffuredumonde@gmail.com",
                recipients=[reservation.user.email]  # Adresse e-mail du client
            )

            # Contenu HTML stylisé pour l'e-mail
            html_content = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Reservation Denied</title>
            </head>
            <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f9f9f9;">
                <!-- Main container -->
                <div style="max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 12px; padding: 20px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
                    <!-- Header section -->
                    <div style="text-align: center; margin-bottom: 20px;">
                        <h1 style="color: #e74c3c; font-size: 24px;">Your Reservation Has Been Denied</h1>
                        <p style="color: #555; font-size: 16px;">We regret to inform you that your reservation has been denied due to the selected time slot being unavailable.</p>
                    </div>

                    <!-- Reason section -->
                    <div style="text-align: left; margin-bottom: 20px;">
                        <p style="color: #555; font-size: 14px;">
                            Unfortunately, the time you selected for your reservation is already occupied. We apologize for any inconvenience caused.
                        </p>
                    </div>

                    <!-- Call-to-action section -->
                    <div style="text-align: center; margin-bottom: 20px;">
                        <a href="https://www.yourwebsite.com/reserve" style="display: inline-block; background-color: #3498db; color: #fff; font-size: 16px; font-weight: bold; padding: 15px 30px; border-radius: 6px; text-decoration: none;">
                            Book a New Reservation
                        </a>
                    </div>

                    <!-- Footer section -->
                    <div style="text-align: center; color: #777; font-size: 12px;">
                        <p>If you have any questions or need further assistance, please contact our support team.</p>
                        <p>&copy; 2023 A&D Coiffure du Monde. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            # Ajouter le contenu HTML et texte brut au message
            msg.html = html_content
            msg.body = (
                "We regret to inform you that your reservation has been denied because the selected time slot is already occupied. "
                "Please visit https://adcoiffure.com to book a new reservation."
            )

            # Envoyer l'e-mail
            mail.send(msg)

        except Exception as e:
            # En cas d'échec de l'envoi de l'e-mail
            flash(f"Failed to send rejection email. Please try again later. ", "error")

        # Afficher un message de succès
        flash("Reservation rejected successfully and an email has been sent to the client.", "success")
        return redirect(url_for('admin_reservation'))

    except Exception as e:
        # Capturer toutes les erreurs (par exemple, erreurs de base de données)
        db.session.rollback()  # Annuler les modifications en cas d'erreur
        flash(f"An error occurred while rejecting the reservation. Please try again later. ", "error")
        return redirect(url_for('admin_reservation'))

@app.route('/admin-dashboard')
def admin_dashboard():
    try:
        # Initialiser les variables
        isConnect = False
        isAdmin = False

        # Vérifier si l'utilisateur est connecté
        user_id = session.get('user_id')
        user = get_current_user()

        if user is None:
            flash("Please log in to access the dashboard.", "error")
            return redirect(url_for('login'))
        else:
            # Récupérer l'utilisateur depuis la base de données
            user = User.query.filter_by(id=user_id).first()
            if user is None:
                flash("User not found. Please log in again.", "error")
                return redirect(url_for('login'))

            # Vérifier si l'utilisateur est administrateur
            isAdmin = authenticate_admin(user)
            isConnect = True

        if not isAdmin:
            flash("Access denied. Only administrators can view the dashboard.", "error")
            return redirect(url_for('index'))

        # Récupérer toutes les réservations et utilisateurs
        reservations = Reservation.query.all()
        users = User.query.all()

        # Calcul des statistiques globales
        total_reservations = len(reservations)
        total_users = len(users)

        # Statistiques par statut de réservation
        reservation_statuses = [r.status for r in reservations]
        status_counts = Counter(reservation_statuses)

        # Passer les données au template
        stats = {
            "total_reservations": total_reservations,
            "total_users": total_users,
            "status_counts": status_counts,
        }

        return render_template(
            'admin-dashboard.html',
            reservations=reservations,
            isAdmin=isAdmin,
            isConnect=isConnect,
            users=users,
            stats=stats,
        )

    except Exception as e:
        # Capturer toutes les erreurs (par exemple, erreurs de base de données)
        flash(f"An error occurred while loading the dashboard. Please try again later. Error: {str(e)}", "error")
        return redirect(url_for('index'))





@app.route('/add_admin', methods=['GET', 'POST'])
def add_admin():
    # Vérifiez si un utilisateur est connecté
    if 'user_id' not in session:
        flash("Please log in to access this page.", "error")
        return redirect(url_for('login'))
    
    # Récupérez l'utilisateur actuel
    user = User.query.get(session['user_id'])
    if not user or user.role != 'admin':
        flash("Access denied. Only administrators can add new admins.", "error")
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Récupérez les données du formulaire
        username = request.form.get('username')
        phone = request.form.get('phone')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validation des champs
        if not username or not phone or not email or not password or not confirm_password:
            flash("All fields are required.", "error")
            return redirect(url_for('add_admin'))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for('add_admin'))

        if User.query.filter_by(phone=phone).first():
            flash("This phone number is already taken.", "error")
            return redirect(url_for('add_admin'))

        

        if User.query.filter_by(email=email).first():
            flash("This email is already registered.", "error")
            return redirect(url_for('add_admin'))

        # Hacher le mot de passe
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        try:
            # Créer un nouvel administrateur
            new_user = User(
                username=username,
                email=email,
                phone=phone,
                password_hash=hashed_password,
                role="admin"  # Spécifiez le rôle comme admin
            )
            db.session.add(new_user)
            db.session.commit()
            flash("Admin registration successful! The admin can now log in.", "success")
            return redirect(url_for('admin_list'))  # Assurez-vous que le nom de la route est correct
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while registering the admin: ", "error")
            return redirect(url_for('add_admin'))
        
        
    return render_template('add_admin.html')

@app.route('/promote-to-admin/<int:user_id>', methods=['POST'])
def promote_to_admin(user_id):
    # Vérifiez si un utilisateur est connecté et s'il est administrateur
    if 'user_id' not in session or not is_admin():
        flash("Access denied. Only administrators can promote users.", "error")
        return redirect(url_for('index'))

    # Récupérez l'utilisateur à promouvoir
    user = User.query.get_or_404(user_id)
    
    if user.role == 'admin':
        flash("This user is already an administrator.", "info")
        return redirect(url_for('admin_list'))

    try:
        # Mettre à jour le rôle de l'utilisateur
        user.role = 'admin'
        db.session.commit()
        flash(f"User {user.username} has been promoted to administrator.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while promoting the user ", "error")

    return redirect(url_for('admin_list'))

@app.route('/demote-to-user/<int:user_id>', methods=['POST'])
def demote_to_user(user_id):
    # Check if a user is logged in and is an admin
    if 'user_id' not in session:
        flash("Please log in to access this page.", "error")
        return redirect(url_for('login'))

    current_user = User.query.get(session['user_id'])
    if not current_user or current_user.role != 'admin':
        flash("Access denied. Only administrators can demote users.", "error")
        return redirect(url_for('index'))

    # Retrieve the user to be demoted
    user = User.query.get_or_404(user_id)
    
    # Check if the user is trying to demote themselves
    if current_user.id == user.id:
        flash("You cannot demote yourself.", "error")
        return redirect(url_for('admin_list'))

    # Check if the user is the principal administrator
    if getattr(user, 'status', None) == "principal":
        flash("You cannot demote the principal administrator.", "error")
        return redirect(url_for('admin_list'))

    # Check if the user is already a standard user
    if user.role == 'user':
        flash("This user is already a standard user.", "info")
        return redirect(url_for('admin_list'))

    try:
        # Update the user's role
        user.role = 'user'
        db.session.commit()
        flash(f"The user {user.username} has been demoted to a standard user.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while demoting the user ", "error")

    return redirect(url_for('admin_list'))


@app.route('/delete-admin/<int:user_id>', methods=['POST'])
def delete_admin(user_id):
    # Check if a user is logged in and is an admin
    if 'user_id' not in session:
        flash("Please log in to access this page.", "error")
        return redirect(url_for('login'))

    current_user = User.query.get(session['user_id'])
    if not current_user or current_user.role != 'admin':
        flash("Access denied. Only administrators can delete users.", "error")
        return redirect(url_for('index'))

    # Retrieve the user to be deleted
    user = User.query.get_or_404(user_id)

    # Check if the user is trying to delete themselves
    if current_user.id == user.id:
        flash("You cannot delete yourself.", "error")
        return redirect(url_for('admin_list'))

    # Check if the user is the principal administrator
    if getattr(user, 'status', None) == "principal":
        flash("You cannot delete the principal administrator.", "error")
        return redirect(url_for('admin_list'))

    try:
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        flash(f"The user {user.username} has been successfully deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while deleting the user ", "error")

    return redirect(url_for('admin_list'))

@app.route('/user_list')
def user_list():
    try:
        # Vérifier si un utilisateur est connecté
        if 'user_id' not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for('login'))

        # Récupérer l'utilisateur actuel
        user = User.query.get(session['user_id'])

        # Vérifier si l'utilisateur existe
        if not user:
            flash("User not found.", "error")
            return redirect(url_for('index'))

        # Vérifier si l'utilisateur est un administrateur
        if user.role != 'admin':
            flash("Access denied. Only administrators can view the list of users.", "error")
            return redirect(url_for('index'))

        # Récupérer la liste de tous les utilisateurs
        users = User.query.all()

        # Passer les données au template
        return render_template('user_list.html', users=users)

    except Exception as e:
        # Capturer toutes les erreurs (par exemple, erreurs de base de données)
        flash(f"An error occurred while loading the user list. Please try again later. Error: {str(e)}", "error")
        return redirect(url_for('index'))

    # Retrieve all users
    users = User.query.all()
    return render_template('user_list.html', users=users)

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    try:
        # Vérifiez si un utilisateur est connecté
        if 'user_id' not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for('login'))
        
        # Récupérer l'utilisateur actuel
        user = User.query.get(session['user_id'])

        # Vérifier si l'utilisateur est l'admin principal
        if user.status == "principal":
            flash("You cannot edit the principal admin.", "error")
            return redirect(url_for('user_list'))

        # Vérifier si l'utilisateur tente de modifier son propre compte
        if user.id == user_id:
            flash("You cannot edit yourself.", "error")
            return redirect(url_for('user_list'))

        # Vérifier si l'utilisateur existe
        if not user:
            flash("User not found.", "error")
            return redirect(url_for('index'))

        # Vérifier si l'utilisateur est un administrateur
        if user.role != 'admin':
            flash("Access denied. Only administrators can edit users.", "error")
            return redirect(url_for('index'))

        # Récupérer l'utilisateur à modifier
        user_to_edit = User.query.filter_by(id=user_id).first()
        if not user_to_edit:
            flash("The user you are trying to edit does not exist.", "error")
            return redirect(url_for('user_list'))

        # Traitement du formulaire en cas de requête POST
        if request.method == 'POST':
            # Mettre à jour les champs de l'utilisateur
            user_to_edit.username = request.form.get('username')
            user_to_edit.phone = request.form.get('phone')
            user_to_edit.email = request.form.get('email')

            # Valider et enregistrer les modifications dans la base de données
            db.session.commit()

            # Afficher un message de succès
            flash("User updated successfully!", "success")
            return redirect(url_for('user_list'))

        # Rendre le template HTML pour afficher le formulaire de modification
        return render_template('edit_user.html', user=user_to_edit)

    except Exception as e:
        # Capturer toutes les erreurs (par exemple, erreurs de base de données)
        db.session.rollback()  # Annuler les modifications en cas d'erreur
        flash(f"An error occurred while updating the user. Please try again later. Error: {str(e)}", "error")
        return redirect(url_for('user_list'))


@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    # Check if a user is logged in and is an admin
    if 'user_id' not in session:
        flash("Please log in to access this page.", "error")
        return redirect(url_for('login'))

    current_user = User.query.get(session['user_id'])
    if not current_user or current_user.role != 'admin':
        flash("Access denied. Only administrators can delete users.", "error")
        return redirect(url_for('index'))

    # Retrieve the user to be deleted
    user = User.query.get_or_404(user_id)

    # Check if the user is trying to delete themselves
    if current_user.id == user.id:
        flash("You cannot delete yourself.", "error")
        return redirect(url_for('admin_list'))

    # Check if the user is the principal administrator
    if getattr(user, 'status', None) == "principal":
        flash("You cannot delete the principal administrator.", "error")
        return redirect(url_for('admin_list'))

    try:
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        flash(f"The user {user.username} has been successfully deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while deleting the user ", "error")

    return redirect(url_for('user_list'))

@app.route('/admin_list')
def admin_list():
    user = get_current_user()
    try:
        if user.role != "admin":
            flash ("Access denied ", 'error')
            return redirect(url_for('index'))
        
    except:
        flash("Access denied. Only administrators can view the list of admins.", "error")
        return redirect(url_for('index'))
    # Récupérer tous les utilisateurs avec le rôle "admin"
    admins = User.query.filter_by(role="admin").all()
    return render_template('admin_list.html', admins=admins)


@app.route('/admin_reservation')
def admin_reservation():
    try:
        # Vérifier si un utilisateur est connecté
        if 'user_id' not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for('login'))

        # Récupérer l'utilisateur actuel
        user = User.query.get(session['user_id'])

        # Vérifier si l'utilisateur existe
        if not user:
            flash("User not found.", "error")
            return redirect(url_for('index'))

        # Vérifier si l'utilisateur est un administrateur
        if user.role != 'admin':
            flash("Access denied. Only administrators can view reservations.", "error")
            return redirect(url_for('index'))

        # Récupérer toutes les réservations
        reservations = Reservation.query.all()

        # Passer les données au template
        return render_template('admin_reservation.html', reservations=reservations)

    except Exception as e:
        # Capturer toutes les erreurs (par exemple, erreurs de base de données)
        flash(f"An error occurred while loading the reservations. Please try again later.", "error")
        return redirect(url_for('index'))
    
@app.route('/search-results')
def search_results():
    # Récupérer le terme de recherche depuis les paramètres de l'URL
    query = request.args.get('query', '').strip().lower()
    if not query:
        flash("Please enter a search term.", "error")
        return redirect(url_for('index'))  # Rediriger vers la page de la galerie si aucun terme n'est saisi

    # Rechercher les services correspondants dans la base de données
    services = Service.query.filter(
        db.or_(
            Service.name.ilike(f'%{query}%'),
            Service.category.ilike(f'%{query}%'),
            Service.description.ilike(f'%{query}%')
        )
    ).all()

    # Passer les résultats au template
    return render_template('search_result.html', services=services, query=query)

@app.route('/user_guide')
def user_guide():
    try:
        # Récupérer l'utilisateur actuel
        user = get_current_user()

        # Vérifier si l'utilisateur est connecté
        isConnect = user is not None

        # Vérifier si l'utilisateur est administrateur (si connecté)
        isAdmin = authenticate_admin(user) if user else False

        # Passer les données au template
        return render_template('user_guide.html', isAdmin=isAdmin, isConnect=isConnect)

    except Exception as e:
        # Capturer toutes les erreurs (par exemple, erreurs de base de données ou de rendu de template)
        flash(f"An error occurred while loading the user guide. Please try again later. Error: {str(e)}", "error")
        return redirect(url_for('error_page'))  # Rediriger vers une page d'erreur générique

    
@app.route('/admin_guide')
def admin_guide():
    try:
        # Récupérer l'utilisateur actuel
        user = get_current_user()

        # Vérifier si l'utilisateur est connecté
        isConnect = user is not None

        # Vérifier si l'utilisateur est administrateur (si connecté)
        isAdmin = authenticate_admin(user) if user else False

        # Passer les données au template
        return render_template('admin_guide.html', isAdmin=isAdmin, isConnect=isConnect)

    except Exception as e:
        # Capturer toutes les erreurs (par exemple, erreurs de base de données ou de rendu de template)
        flash(f"An error occurred while loading the user guide. Please try again later. Error: {str(e)}", "error")
        return redirect(url_for('error_page'))  # Rediriger vers une page d'erreur générique


    
        
    

# Lancement de l'application
if __name__ == "__main__":
    
    app.run(host='0.0.0.0', port=5000, debug=True)