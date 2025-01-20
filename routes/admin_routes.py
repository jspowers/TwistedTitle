import logging
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import login_user, current_user, logout_user, login_required
from utilities.pymongo.collections.DimMovies import MDBDimMovies
from utilities.get_movie_neighbors import get_movie_neighbors

from extensions import twisted_db

# Create a Blueprint
admin_blueprint = Blueprint("admin", __name__)

def check_admin():
    if current_user.is_admin == False or current_user.is_admin == None:
        return redirect(url_for('auth.profile'))

@admin_blueprint.route('/create_clues')
@login_required
def create_clues(**kwargs):
    check_admin()
    
    # Only generate the movie list if the on first load.
    # This makes sure that a reloaded page can keep current set of movies on the page.
    # Get all movies sorting by active clue count and vote count.
    movie_db = MDBDimMovies()

    movie_list = []

    # Get 4 movies from each difficult
    for i in range(1, 4):
        movies = movie_db.get_db_movie(
            filter={"difficulty": i},
            sort={"admin_ind_has_clue": 1, "vote_count": -1},
            limit=4,
            )
        
        if movies == None: 
            logging.warning("No movies found in mongo Response - Breaking")
            break    
        for m in movies:
            m['word_neighbors']=dict()
            for word in m['title'].split():
                m['word_neighbors'][word] = get_movie_neighbors(word)
            movie_list.append(m)
    

    return render_template(
        'create_clues.html',
        current_user=current_user,
        movie_list=movie_list,
        )


@admin_blueprint.route('/update_clue', methods=['POST'])
@login_required
def update_clue():
    
    # Connect to the database
    movie_db = MDBDimMovies()
    
    # Get the update information
    movie_id = int(request.form.get('movie_id'))
    deprioritize_flag = True if request.form.get('deprioritize_flag') == "on" else False

    # Send update commmand to Mongo DB
    result = movie_db.collection.update_one({'id': movie_id}, {'$set': {'admin_ind_twisted_depri': deprioritize_flag}})
    if result.modified_count == 0:
        logging.warning(f"Movie {movie_id} not updated - Records found in upated query: {result.matched_count}")
    else:
        logging.info(f"{result.matched_count} found: {result.modified_count} record updated. Movie {movie_id} modified.")
    
    return redirect(url_for('admin.create_clues'))



@admin_blueprint.route('/validate_clues')
@login_required
def validate_clues():
    if current_user.is_admin == False:
        return redirect(url_for('auth.profile'))
    return render_template(
        'validate_clues.html',
        current_user=current_user,
        )


