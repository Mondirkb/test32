import os

import cv2
import numpy as np
import face_recognition
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_user, LoginManager, login_required, current_user, logout_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, HiddenField
from wtforms.validators import DataRequired, Length
import pickle
import base64



app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'my-secrets')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:////app/instance/moundir.db')
# using for local file
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/moundir/PycharmProjects/Meeting_Web_App//moundir.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for Railway

db = SQLAlchemy(app)

# Login Manager
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# Database Model
class Register(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    face_encoding = db.Column(db.PickleType, nullable=True)  # Store face encoding

# Create Database
with app.app_context():
    db.create_all()

# Forms
class RegistrationForm(FlaskForm):
    email = EmailField(label='Email', validators=[DataRequired()])
    first_name = StringField(label="First Name", validators=[DataRequired()])
    last_name = StringField(label="Last Name", validators=[DataRequired()])
    username = StringField(label="Username", validators=[DataRequired(), Length(min=4, max=20)])
    photo_data = HiddenField(label="Photo Data", validators=[DataRequired()])

class LoginForm(FlaskForm):
    email = EmailField(label='Email', validators=[DataRequired()])
    photo_data = HiddenField(label="Photo Data", validators=[DataRequired()])

#  Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return Register.query.get(int(user_id))

# Routes
@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["POST", "GET"])
def login():
    form = LoginForm()
    if request.method == "POST":
        email = request.form.get('email')
        # Get photo data directly from request.form
        photo_data = request.form.get('photo_data')

        if not email:
            flash("Email is required.", "danger")
            return redirect(url_for("login"))

        if not photo_data:
            flash("No photo captured. Please take a photo.", "danger")
            return redirect(url_for("login"))

        user = Register.query.filter_by(email=email).first()

        if not user:
            flash("User not found. Please register first.", "danger")
            return redirect(url_for("register"))

        try:

            header, encoded = photo_data.split(",", 1)
            binary_data = base64.b64decode(encoded)
            image = np.frombuffer(binary_data, dtype=np.uint8)
            frame = cv2.imdecode(image, cv2.IMREAD_COLOR)


            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_encodings = face_recognition.face_encodings(rgb_frame)

            if not face_encodings:
                flash("No face detected. Please try again.", "danger")
                return redirect(url_for("login"))


            stored_encoding = pickle.loads(user.face_encoding) if user.face_encoding else None
            if stored_encoding is None:
                flash("No face data found for this user.", "danger")
                return redirect(url_for("login"))

            matches = face_recognition.compare_faces([stored_encoding], face_encodings[0], tolerance=0.6)
            if matches[0]:
                login_user(user)
                flash("Face authentication successful!", "success")
                return redirect(url_for("dashboard"))
            else:
                flash("Face authentication failed. Please try again.", "danger")
                return redirect(url_for("login"))

        except Exception as e:
            flash(f"Error processing image: {str(e)}", "danger")
            return redirect(url_for("login"))

    return render_template("login.html", form=form)


@app.route("/logout", methods=["GET"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully!", "info")
    return redirect(url_for("login"))

@app.route("/register", methods=["POST", "GET"])
def register():
    form = RegistrationForm()
    if request.method == "POST" and form.validate_on_submit():
        username = form.username.data
        email = form.email.data


        if Register.query.filter_by(email=email).first() or Register.query.filter_by(username=username).first():
            flash("Email or username already exists.", "danger")
            return redirect(url_for("register"))


        photo_data = form.photo_data.data
        if not photo_data:
            flash("No photo captured. Please take a photo.", "danger")
            return redirect(url_for("register"))

        try:

            header, encoded = photo_data.split(",", 1)
            binary_data = base64.b64decode(encoded)
            image = np.frombuffer(binary_data, dtype=np.uint8)
            frame = cv2.imdecode(image, cv2.IMREAD_COLOR)


            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_encodings = face_recognition.face_encodings(rgb_frame)

            if not face_encodings:
                flash("No face detected. Please try again.", "danger")
                return redirect(url_for("register"))


            face_encoding = pickle.dumps(face_encodings[0])

            new_user = Register(
                email=email,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                username=username,
                face_encoding=face_encoding
            )

            db.session.add(new_user)
            db.session.commit()

            flash("Registered successfully! Please log in.", "success")
            return redirect(url_for("login"))

        except Exception as e:
            flash(f"Error processing image: {str(e)}", "danger")
            return redirect(url_for("register"))

    return render_template("register.html", form=form)

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", first_name=current_user.first_name, last_name=current_user.last_name)

@app.route("/meeting")
@login_required
def meeting():
    room_id = request.args.get("roomID") or request.args.get("room_id")
    if not room_id:
        import random
        room_id = str(random.randint(100000, 999999))
    return render_template("meeting.html", username=current_user.username, room_id=room_id)

@app.route("/join", methods=["GET", "POST"])
@login_required
def join():
    if request.method == "POST":
        room_id = request.form.get("roomID")
        if room_id:
            return redirect(url_for("meeting", roomID=room_id))
        else:
            flash("Please enter a room ID", "danger")

    return render_template("join.html")

if __name__ == "__main__":
    print("Starting Flask app with HTTPS...")
    print("Make sure cert.pem and key.pem are in the same directory")
    
    # Run with HTTPS
    app.run(
        host="0.0.0.0", 
        port=5000, 
        debug=True, 
        ssl_context=("cert.pem", "key.pem")
    )