# This file handles everything for the point 3 of part 1 of the project:
# 3. An endpoint for admins to add a new movie to the database

from flask import Blueprint, request, jsonify
from models import Movie, db
from flask_jwt_extended import jwt_required, get_jwt_identity

movie_bp = Blueprint('movie', __name__)

# Admin endpoint to add a new movie
@movie_bp.route('/add', methods=['POST'])
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
