import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, get_flashed_messages
from flask_login import current_user, login_required
from pymongo import UpdateOne
from utilities.pymongo.collections.DimMovies import MDBDimMovies
from utilities.get_movie_neighbors import get_movie_neighbors
from utilities.chatGPT.gpt_requests import get_twisted_title_description
from utilities.validate_clue import validate_clue

# Create a Blueprint
admin_blueprint = Blueprint("admin", __name__)

def check_admin():
    if current_user.is_admin == False or current_user.is_admin == None:
        return redirect(url_for('auth.profile'))

@admin_blueprint.route('/create_clues', methods=["GET", "POST"])
@login_required
def create_clues(**kwargs):
    check_admin()
    
    # Only generate the movie list if the on first load.
    # This makes sure that a reloaded page can keep current set of movies on the page.
    # Get all movies sorting by active clue count and vote count.
    movie_db = MDBDimMovies()

    
    movie_list = dict({})
    movie_update_requests = []

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
            # if the word neighbors are not in the movie record, get them, should only run first time
            if m.get('word_neighbors') == None:
                m['word_neighbors']=dict()
                for word in m['title'].split():
                    m['word_neighbors'][word] = get_movie_neighbors(word)
                movie_update_requests.append(
                    UpdateOne({'id': m['id']}, {'$set': {'word_neighbors': m['word_neighbors']}})
                    )
            movie_list[m['id']] = m

    #check if gpt_response movie id in movie list and add to movie_list object
    
    gpt_response = get_flashed_messages(category_filter=["gpt_response"])
    if gpt_response:
        gpt_response = gpt_response[0]

    if gpt_response and gpt_response[0] in movie_list:
        logging.info("Adding GPT response to the movie list to populate description text area.")
        movie_id = gpt_response[0]
        movie_list[movie_id]['gpt_response'] = gpt_response[2]
        movie_list[movie_id]['twist_clue_attempt'] = gpt_response[1]
    
    # page load errors
    clue_errors = get_flashed_messages(category_filter=["clue_validation_error"])
    if clue_errors:
        clue_errors = clue_errors[0]
        movie_id = clue_errors[0]
        movie_list[movie_id]['twist_clue_attempt'] = clue_errors[1]
        movie_list[movie_id]['clue_error'] = clue_errors[2]
        print(movie_list[movie_id]['clue_error'])
        
    

    # update mongoDB with any new word neighbors if necessary
    if len(movie_update_requests) > 0:
        logging.info(f"{len(movie_update_requests)} records to be updated in MongoDB.")
        update = movie_db.collection.bulk_write(movie_update_requests)
        logging.info(f"Updated with {update.modified_count} records with word neighbors.")

    return render_template(
        'create_clues.html',
        current_user=current_user,
        movie_list=movie_list,
        )


@admin_blueprint.route('/update_clue', methods=['POST'])
@login_required
def update_clue():
    
    movie_id = int(request.form.get('movie_id'))
    original_title = request.form.get("movie_title")
    twist_title = request.form.get("twisted_title", '')
    # Check if submitted title is valid
    logging.info('Firing clue validation process')
    validation_errors = validate_clue(original_movie=original_title, modified_movie=twist_title)


    # Generate a chat GPT description
    if "generate" in request.form:
        if request.method == 'POST':
            # Check if 'Generate GPT Response' button was clicked
            if "generate" in request.form:  
                # look for clue validation errors
                if len(validation_errors) > 0:
                    errors = [x.message for x in validation_errors]
                    logging.info(f"Clue validation errors: {errors}")
                    flash((movie_id, twist_title, " | ".join(errors)), "clue_validation_error")
                    return redirect(url_for('admin.create_clues'))
                else: 
                    result = get_twisted_title_description(
                            original_movie=original_title,
                            modified_movie=twist_title,
                            )
                    # flash the result to the next response page
                    flash((movie_id, twist_title, result), "gpt_response")
                    
    elif "save_movie_clue" in request.form:

        # Connect to the database
        movie_db = MDBDimMovies()
        
        # Get the update information
        deprioritize_flag = True if request.form.get('deprioritize_flag') == "on" else False

        # Send update commmand to Mongo DB
        result = movie_db.collection.update_one(
            {'id': movie_id},
            {'$set': {'admin_ind_twisted_depri': deprioritize_flag}}
            )
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


