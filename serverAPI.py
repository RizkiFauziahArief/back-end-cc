from enum import unique
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from uuid import uuid4
from datetime import datetime, timedelta

import jwt
import secrets
import string

db = SQLAlchemy()

def CreateUUID():
    return uuid4().hex

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.String(32), unique=True, primary_key=True, default=CreateUUID)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(), nullable=False)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SECRET_KEY'] = 'secret'
db.init_app(app)

@app.route('/')
def hello():
    return 'successful'

@app.route("/register", methods=["POST"])
def RegisterUser():
    try:
        user_data = request.get_json()
        email = user_data["email"]
        password = user_data["password"]

        hashed_password = generate_password_hash(password)

        user = User(email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        return "done", 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/login", methods=["POST"])
def login():
    email = request.json["email"]
    password = request.json["password"]

    user = User.query.filter_by(email=email).first()

    if user is None:
        return jsonify({"error": "Invalid email"}), 401

    if not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid password"}), 401

    token = jwt.encode({
        'username': email,
        'exp': datetime.utcnow() + timedelta(minutes=30)
    }, app.config['SECRET_KEY'])

    return jsonify({'token': token}), 201

def generate_secret_key(length):
    characters = string.ascii_letters + string.digits + string.punctuation
    secret_key = ''.join(secrets.choice(characters) for _ in range(length))
    return secret_key

@app.route('/protected', methods=['GET'])
def protected():
    token = request.headers.get('Authorization')

    if not token:
        return jsonify({'error': 'Token is missing'}), 401

    try:
        decoded = jwt.decode(token, app.config['SECRET_KEY'])
        username = decoded['username']

        return jsonify({'message': f'Hello, {username}! This is protected data.'})

    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
