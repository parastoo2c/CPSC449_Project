# This file handles everything for the point 5 of part 1 of the project:
# 5. An endpoint to retrieve a list of existing user ratings for all the movies

from flask import Blueprint, jsonify
from models import Movie, Rating, db

rating_bp = Blueprint('rating', __name__)

# Retrieve all ratings for movies
@rating_bp.route('/list', methods=['GET'])
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
