from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from flask_bcrypt import Bcrypt
from datetime import datetime
import datetime as dt
import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
import requests

app = Flask(__name__, static_folder="static", template_folder="templates")
bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = 'supersecretkey'

# Variables d'environnement pour la BD
db_server = os.environ.get('DB_SERVER', '')
db_name = os.environ.get('DB_NAME', '')
db_user = os.environ.get('DB_USER', '')
db_password = os.environ.get('DB_PASSWORD', '')

# Chaîne de connexion ODBC pour MSSQL via pyodbc
# Note: Assurez-vous que le driver "ODBC Driver 18 for SQL Server" est installé (msodbcsql18)
connection_string = f"mssql+pyodbc://{db_user}:{db_password}@{db_server}:1433/{db_name}?driver=ODBC+Driver+18+for+SQL+Server"

engine = create_engine(connection_string, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Room(Base):
    __tablename__ = 'rooms'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=False)
    description = Column(String(255))

class Reservation(Base):
    __tablename__ = 'reservations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, nullable=False)
    user_name = Column(String(100), nullable=False)
    timeslot = Column(String(50), nullable=False)
    date = Column(String(10), nullable=False)  # format YYYY-MM-DD

with engine.begin() as conn:
    Base.metadata.create_all(conn)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

TIMESLOTS = [
    "09:00 - 10:00",
    "10:00 - 11:00",
    "11:00 - 12:00",
    "13:00 - 14:00",
    "14:00 - 15:00",
    "15:00 - 16:00"
]

users = {"admin": bcrypt.generate_password_hash("admin123").decode("utf-8")}

def is_timeslot_available(db_session, room_id, date_str, timeslot, exclude_res_id=None):
    q = db_session.query(Reservation).filter(
        Reservation.room_id == room_id,
        Reservation.date == date_str,
        Reservation.timeslot == timeslot
    )
    if exclude_res_id:
        q = q.filter(Reservation.id != exclude_res_id)
    return q.count() == 0

def get_available_timeslots(db_session, room_id, date_str, exclude_res_id=None):
    date_obj = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
    # Pas de réservation le week-end
    if date_obj.weekday() in [5, 6]:
        return []
    return [t for t in TIMESLOTS if is_timeslot_available(db_session, room_id, date_str, t, exclude_res_id)]

# URL de la Logic App
logic_app_url = "https://prod-06.francecentral.logic.azure.com:443/workflows/c8e527309843410a81aee00d47fa7b69/triggers/When_a_HTTP_request_is_received/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2FWhen_a_HTTP_request_is_received%2Frun&sv=1.0&sig=yy0b8s34T4HBtIfhewBeRutPSqsMeweHhdKJDzlT3iM"

def send_email_to_logic_app(user_name, room_name, date_str, timeslot, email):
    data = {
        "user_name": user_name,
        "room_name": room_name,
        "date": date_str,
        "timeslot": timeslot,
        "email": email
    }

    response = requests.post(logic_app_url, json=data)
    if response.status_code == 202:
        print("E-mail envoyé avec succès.")
    else:
        print(f"Erreur lors de l'envoi de l'e-mail : {response.text}")
@app.route('/')
def home():
    return render_template("index.html", year=datetime.now().year)

@app.route('/rooms-page')
def rooms_page():
    db_session = next(get_db())
    rooms = db_session.query(Room).all()
    return render_template("rooms.html", rooms=rooms, year=datetime.now().year)

@app.route('/rooms', methods=['GET'])
def get_rooms_endpoint():
    db_session = next(get_db())
    all_rooms = db_session.query(Room).all()
    data = [{"id": r.id, "name": r.name, "capacity": r.capacity, "description": r.description} for r in all_rooms]
    return jsonify(data)

@app.route('/rooms/<int:room_id>', methods=['GET'])
def get_room_details(room_id):
    db_session = next(get_db())
    room = db_session.query(Room).filter_by(id=room_id).first()
    if room:
        return render_template("room_details.html", room=room, year=datetime.now().year)
    else:
        return render_template("404.html", year=datetime.now().year), 404

@app.route('/available_timeslots', methods=['GET'])
def available_timeslots_endpoint():
    room_id = request.args.get("room_id", type=int)
    date_str = request.args.get("date", type=str)
    if not room_id or not date_str:
        return jsonify([])
    db_session = next(get_db())
    slots = get_available_timeslots(db_session, room_id, date_str)
    return jsonify(slots)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and bcrypt.check_password_hash(users[username], password):
            session['user'] = username
            flash("Connexion réussie !", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Identifiants invalides", "danger")
    return render_template('login.html', year=datetime.now().year)

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Déconnexion réussie !", "info")
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash("Veuillez vous connecter en tant qu'admin pour accéder au tableau de bord", "warning")
        return redirect(url_for('login'))
    db_session = next(get_db())
    reservations = db_session.query(Reservation).all()
    rooms = db_session.query(Room).all()
    return render_template('dashboard.html', reservations=reservations, rooms=rooms, year=datetime.now().year)

@app.route('/book-room', methods=['GET', 'POST'])
def book_room():
    db_session = next(get_db())
    rooms = db_session.query(Room).all()
    if request.method == 'POST':
        room_id = request.form.get("room_id")
        user_name = request.form.get("user_name")
        timeslot = request.form.get("timeslot")
        date_str = request.form.get("date")
        email = request.form.get("email")

        if not (room_id and user_name and timeslot and date_str):
            flash("Tous les champs sont obligatoires", "danger")
            return redirect(url_for("book_room"))

        room_id = int(room_id)
        date_obj = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
        if date_obj.weekday() in [5,6]:
            flash("Impossible de réserver le week-end.", "danger")
            return redirect(url_for("book_room"))

        if not is_timeslot_available(db_session, room_id, date_str, timeslot):
            flash("Ce créneau n'est plus disponible pour cette salle.", "danger")
            return redirect(url_for("book_room"))

        new_res = Reservation(room_id=room_id, user_name=user_name, timeslot=timeslot, date=date_str)
        db_session.add(new_res)
        db_session.commit()

        room = db_session.query(Room).filter_by(id=room_id).first()

        # Appeler la Logic App
        send_email_to_logic_app(user_name, room.name, date_str, timeslot, email)


        flash(f"La salle {room.name} a été réservée par {user_name} le {date_str} sur le créneau {timeslot}.", "success")
        return redirect(url_for('home'))

    return render_template("book_room.html", rooms=rooms, year=datetime.now().year)

@app.route('/delete-reservation/<int:res_id>', methods=['POST'])
def delete_reservation(res_id):
    if 'user' not in session:
        flash("Accès interdit", "danger")
        return redirect(url_for('login'))
    db_session = next(get_db())
    res = db_session.query(Reservation).filter_by(id=res_id).first()
    if res:
        db_session.delete(res)
        db_session.commit()
        flash("Réservation supprimée avec succès.", "info")
    else:
        flash("Réservation introuvable.", "danger")
    return redirect(url_for('dashboard'))

@app.route('/edit-reservation/<int:res_id>', methods=['GET', 'POST'])
def edit_reservation(res_id):
    if 'user' not in session:
        flash("Accès interdit", "danger")
        return redirect(url_for('login'))

    db_session = next(get_db())
    reservation = db_session.query(Reservation).filter_by(id=res_id).first()
    if not reservation:
        flash("Réservation introuvable.", "danger")
        return redirect(url_for('dashboard'))

    rooms = db_session.query(Room).all()

    if request.method == 'POST':
        new_room_id = int(request.form.get("room_id"))
        new_timeslot = request.form.get("timeslot")
        new_date_str = request.form.get("date")

        if not (new_room_id and new_timeslot and new_date_str):
            flash("Tous les champs sont obligatoires", "danger")
            return redirect(url_for('edit_reservation', res_id=res_id))

        date_obj = dt.datetime.strptime(new_date_str, "%Y-%m-%d").date()
        if date_obj.weekday() in [5, 6]:
            flash("Impossible de réserver le week-end.", "danger")
            return redirect(url_for('edit_reservation', res_id=res_id))

        if not is_timeslot_available(db_session, new_room_id, new_date_str, new_timeslot, exclude_res_id=res_id):
            flash("Ce créneau n'est pas disponible pour cette salle.", "danger")
            return redirect(url_for('edit_reservation', res_id=res_id))

        reservation.room_id = new_room_id
        reservation.timeslot = new_timeslot
        reservation.date = new_date_str
        db_session.commit()
        flash("Réservation mise à jour avec succès.", "success")
        return redirect(url_for('dashboard'))

    return render_template("edit_reservation.html",
                           reservation=reservation,
                           rooms=rooms,
                           timeslots=TIMESLOTS,  # Ajout de cette ligne
                           year=datetime.now().year)


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", year=datetime.now().year), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
