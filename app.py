from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/movie_ratings'
app.config['JWT_SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Update the User model to match the database schema
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
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
    user = User.query.filter_by(username=user_identity).first()
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
    user = User.query.filter_by(username=user_identity).first()
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
    user = User.query.filter_by(username=user_identity).first()
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

if __name__ == '__main__':
    app.run(debug=True)
