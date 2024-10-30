from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:example@127.0.0.1:5000/movie_ratings'
app.config['JWT_SECRET_KEY'] = 'your_secret_key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=1)
app.config['UPLOAD_FOLDER'] = 'uploads'  # Folder for storing uploaded files
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpeg', 'gif'}  # Set allowed extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Ensure the upload folder exists, and create it if not
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Helper function to check file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Update the User model to match the database schema
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Movie(db.Model):
    __tablename__ = 'movies'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    release_year = db.Column(db.Integer, nullable=True)

class Rating(db.Model):
    __tablename__ = 'ratings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id', ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        db.CheckConstraint('rating BETWEEN 1 AND 10', name='ratings_chk_1'),
    )

# Register endpoint (for both users and admins)
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # Check if the user already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'User already exists!'}), 400

    # Hash the password and create a new user
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    new_user = User(username=data['username'], password=hashed_password, is_admin=data.get('is_admin', False))

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully!'}), 201
    except Exception as e:
        return jsonify({'message': 'User registration failed.', 'error': str(e)}), 400

# Login endpoint (JWT authentication)
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    # Check if the user exists and the password matches
    user = User.query.filter_by(username=data['username']).first()
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Invalid credentials!'}), 401

    # Generate a JWT access token
    access_token = create_access_token(identity={'username': user.username, 'is_admin': user.is_admin})
    return jsonify({'access_token': access_token}), 200

# File upload endpoint
@app.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    # Check if a file is part of the request
    if 'file' not in request.files:
        return jsonify({'message': 'No file part in the request'}), 400
    file = request.files['file']

    # Check if the file has a valid filename and allowed extension
    if file.filename == '':
        return jsonify({'message': 'No file selected for uploading'}), 400
    if file and allowed_file(file.filename):
        # Secure the filename and save the file to the specified folder
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({'message': 'File successfully uploaded', 'filename': filename}), 201
    else:
        return jsonify({'message': 'File type is not allowed'}), 400

# Endpoint for users to submit their ratings for movies
@app.route('/movies/<int:movie_id>/rating', methods=['POST'])
@jwt_required()
def submit_rating(movie_id):
    user_identity = get_jwt_identity()
    user = User.query.filter_by(username=user_identity['username']).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # admins cannot submit a rating, only users
    if user.is_admin:
        return jsonify({'message': 'Admins cannot submit ratings'}), 403

    data = request.get_json()
    rating_value = data.get('rating')
    if not (1 <= rating_value <= 10):
        return jsonify({'message': 'Rating must be between 1 and 10'}), 400

    # Check if movie exists
    movie = Movie.query.get(movie_id)
    if not movie:
        return jsonify({'message': 'Movie not found'}), 404

    # Check if user has already rated this movie
    existing_rating = Rating.query.filter_by(user_id=user.id, movie_id=movie_id).first()
    if existing_rating:
        existing_rating.rating = rating_value
    else:
        new_rating = Rating(user_id=user.id, movie_id=movie_id, rating=rating_value)
        db.session.add(new_rating)

    db.session.commit()
    return jsonify({'message': 'Rating submitted successfully'}), 200

# Endpoint to fetch details for a specific movie, including its user ratings
@app.route('/movies/<int:movie_id>', methods=['GET'])
def get_movie_details(movie_id):
    movie = Movie.query.get(movie_id)
    if not movie:
        return jsonify({'message': 'Movie not found'}), 404

    # Fetch all ratings for the movie
    ratings = Rating.query.filter_by(movie_id=movie_id).all()
    ratings_list = [{'user_id': rating.user_id, 'rating': rating.rating} for rating in ratings]

    movie_details = {
        'id': movie.id,
        'title': movie.title,
        'description': movie.description,
        'release_year': movie.release_year,
        'ratings': ratings_list
    }

    return jsonify(movie_details), 200

# Endpoint that allows users to update their own movie ratings
@app.route('/movies/<int:movie_id>/rating', methods=['PUT'])
@jwt_required()
def update_rating(movie_id):
    user_identity = get_jwt_identity()
    user = User.query.filter_by(username=user_identity['username']).first()

    if not user:
        return jsonify({'message': 'User not found'}), 404

    if user.is_admin:
        return jsonify({'message': 'Admins cannot update ratings'}), 403

    data = request.get_json()
    rating_value = data.get('rating')

    if not (1 <= rating_value <= 10):
        return jsonify({'message': 'Rating must be between 1 and 10'}), 400

    existing_rating = Rating.query.filter_by(user_id=user.id, movie_id=movie_id).first()
    if not existing_rating:
        return jsonify({'message': 'Rating not found'}), 404

    existing_rating.rating = rating_value
    db.session.commit()

    return jsonify({'message': 'Rating updated successfully'}), 200

# [Admin-only] Endpoint to delete any movie's user rating from the database
@app.route('/admin/ratings/<int:rating_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_rating(rating_id):
    user_identity = get_jwt_identity()
    username = user_identity['username'] if isinstance(user_identity, dict) else user_identity
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.is_admin:
        return jsonify({'message': 'Unauthorized access'}), 403

    rating = Rating.query.get(rating_id)
    if not rating:
        return jsonify({'message': 'Rating not found'}), 404

    db.session.delete(rating)
    db.session.commit()

    return jsonify({'message': 'Rating deleted successfully'}), 200

# Endpoint for users to delete their own ratings
@app.route('/movies/<int:movie_id>/rating', methods=['DELETE'])
@jwt_required()
def delete_own_rating(movie_id):
    user_identity = get_jwt_identity()
    username = user_identity['username'] if isinstance(user_identity, dict) else user_identity
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return jsonify({'message': 'User not found'}), 404

    if user.is_admin:
        return jsonify({'message': 'Admins cannot delete ratings'}), 403

    existing_rating = Rating.query.filter_by(user_id=user.id, movie_id=movie_id).first()
    if not existing_rating:
        return jsonify({'message': 'Rating not found'}), 404

    db.session.delete(existing_rating)
    db.session.commit()

    return jsonify({'message': 'Rating deleted successfully'}), 200

# Retrieve all ratings for movies
@app.route('/ratings/list', methods=['GET'])
def get_ratings():
    movies = Movie.query.all()
    movies_data = []
    for movie in movies:
        ratings = Rating.query.filter_by(movie_id=movie.id).all()
        movie_ratings = [rating.rating for rating in ratings]
        movies_data.append({
            'id': movie.id,
            'title': movie.title,
            'release_year': movie.release_year,
            'ratings': movie_ratings
        })

    return jsonify(movies_data), 200

# Admin endpoint to add a new movie
@app.route('/movies/add', methods=['POST'])
@jwt_required()
def add_movie():
    current_user = get_jwt_identity()
    if not current_user.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    release_year = data.get('release_year')

    if not title or not release_year:
        return jsonify({'error': 'Title and Release Year are required'}), 400

    new_movie = Movie(title=title, description=description, release_year=release_year)
    db.session.add(new_movie)
    db.session.commit()

    return jsonify({'message': 'Movie added successfully', 'movie': new_movie.id}), 201


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
