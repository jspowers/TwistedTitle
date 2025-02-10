import time
import logging
import ast
from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    get_flashed_messages,
    abort,
    session,
)
from flask_login import current_user, login_required
from pymongo import UpdateOne
from bson.objectid import ObjectId
from utilities.pymongo.collections.DimMovies import MDBDimMovies
from utilities.pymongo.collections.DimClues import MDBDimClues
from utilities.get_movie_neighbors import get_movie_neighbors
from utilities.chatGPT.gpt_requests import get_twisted_title_description
from utilities.validate_clue import validate_clue
from utilities.global_utils import remove_non_alpha_letters, get_max_string_key_value

# Create a Blueprint
admin_blueprint = Blueprint("admin", __name__)

# --------------- ROUTE UTILITIES --------------- #
def check_admin():
    if current_user.is_admin == False or current_user.is_admin == None:
        return redirect(url_for("auth.profile"))


def check_for_clue_errors(movie_id, twist_title, validation_errors):
    if len(validation_errors) > 0:
        errors = [x.message for x in validation_errors]
        logging.info(f"Clue validation errors: {errors}")
        flash((movie_id, twist_title, " | ".join(errors)), "clue_validation_error")
        abort(redirect(url_for("admin.create_clues")))
    return

def assign_filter(filter_set: str, field_name: str, session=session) -> None:
    """
    This function is used to assign a filter to the session object.
    """
    if request.form.get(field_name):
        session[filter_set][field_name] = request.form.get(field_name)
    else:
        session[filter_set].pop(field_name, None)
    return

# --------------- TEMPLATE FILTERS --------------- #
@admin_blueprint.app_template_filter('from_unix')
def convert_from_unix(s):
    """
    Convert a unix timestamp to a human readable time.
    """
    return datetime.fromtimestamp(s).strftime('%Y-%m-%d %H:%M:%S')

@admin_blueprint.app_template_filter('highlight_difference')
def highlight_difference(mod: str, orig: str, is_orig: bool) -> str:
    """
    Compare two strings and wrap the differing character in a <span> tag.
    """
    class_mod = "highlight-good" if is_orig else "highlight-bad"
    if len(orig) != len(mod):
        return mod 
    result = []
    for c1, c2 in zip(orig, mod):
        if c1 == c2:
            result.append(c2)
        else:
            result.append(f'<span class="{class_mod}">{c2}</span>')  # Wrap different character
    return ''.join(result)


# --------------- BLUEPRINT ROUTES --------------- #
@admin_blueprint.route("/create_clues", methods=["GET", "POST"])
@login_required
def create_clues(**kwargs):
    """
    This function is used to create clues for the movies.
    """

    check_admin()
    # Only generate the movie list if the on first load.
    # This makes sure that a reloaded page can keep current set of movies on the page.
    # Get all movies sorting by active clue count and vote count.
    # movie_db = MDBDimMovies()
    with MDBDimMovies() as movie_db:
        movie_list = dict({})
        movie_update_requests = []

        filters = session.get("movie_search_filters", dict({}))
        difficulties = [x for x in filters.pop("difficulty", [1, 2, 3]) if x is not None]
        max_movie_return = 12
        if len(difficulties) != 0:
            diff_batch_count = max_movie_return // len(difficulties)

            # Get 4 movies from each difficult
            for i in difficulties:
                filters['difficulty'] = i
                movies = movie_db.collection.find(
                    filter=filters,
                    sort={"admin_ind_has_clue": 1, "vote_count": -1},
                    limit=diff_batch_count,
                )

                if movies == None:
                    logging.warning("No movies found in mongo Response - Breaking")
                    break

                for m in movies:
                    # if the word neighbors are not in the movie record, get them, should only run first time
                    if m.get("word_neighbors") == None:
                        m["word_neighbors"] = dict()
                        for word in m["title"].split():
                            m["word_neighbors"][word] = get_movie_neighbors(word)
                        movie_update_requests.append(
                            UpdateOne(
                                {"id": m["id"]},
                                {"$set": {"word_neighbors": m["word_neighbors"]}},
                            )
                        )
                    movie_list[m["id"]] = m

        # reset difficulty filter
        filters['difficulty'] = difficulties

        # update mongoDB with any new word neighbors if necessary
        if len(movie_update_requests) > 0:
            logging.info(f"{len(movie_update_requests)} records to be updated in MongoDB.")
            update = movie_db.collection.bulk_write(movie_update_requests)
            logging.info(
                f"Updated with {update.modified_count} records with word neighbors."
            )

    gpt_response = get_flashed_messages(category_filter=["gpt_response"])
    if gpt_response:
        gpt_response = gpt_response[0]

    if gpt_response and gpt_response[0] in movie_list:
        logging.info(
            "Adding GPT response to the movie list to populate description text area."
        )
        movie_id = gpt_response[0]
        movie_list[movie_id]["gpt_response"] = gpt_response[2]
        movie_list[movie_id]["twist_clue_attempt"] = gpt_response[1]

    # page load errors
    clue_errors = get_flashed_messages(category_filter=["clue_validation_error"])
    if clue_errors and clue_errors[0] in movie_list:
        clue_errors = clue_errors[0]
        movie_id = clue_errors[0]
        movie_list[movie_id]["twist_clue_attempt"] = clue_errors[1]
        movie_list[movie_id]["clue_error"] = clue_errors[2]

    clue_proposal_success = get_flashed_messages(category_filter=["clue_proposal_success"])
    if clue_proposal_success and clue_proposal_success[0] in movie_list:
        clue_proposal_success = clue_proposal_success[0]
        movie_id = clue_proposal_success[0]
        movie_list[movie_id]["twist_clue_attempt"] = clue_proposal_success[1]
        movie_list[movie_id]["clue_proposal_success"] = clue_proposal_success[2]

    return render_template(
        "create_clues.html",
        current_user=current_user,
        movie_list=movie_list,
        filters=filters,
    )


@admin_blueprint.route("/update_movies", methods=["POST"])
@login_required
def update_movies():
    """
    This function is used to update the clue information in the database.
    """

    movie_id = int(request.form.get("movie_id"))
    original_title = request.form.get("movie_title")
    twist_title = request.form.get("twisted_title", "").upper()
    raw_twist_title = remove_non_alpha_letters(twist_title)

    # Check if submitted title is valid
    logging.info("Firing clue validation process")
    validation_errors = validate_clue(
        original_movie=original_title, modified_movie=twist_title
    )

    # Generate a chat GPT description
    if "generate_gpt_response" in request.form:
        filtered_errors = [
            x
            for x in validation_errors
            if "generate_gpt_response" in x.scope and x.action != "BLOCK"
        ]
        print(len(filtered_errors))
        check_for_clue_errors(movie_id, twist_title, filtered_errors)
        result = get_twisted_title_description(
            original_movie=original_title,
            modified_movie=twist_title,
        )
        # flash the result to the next response page
        flash((movie_id, twist_title, result), "gpt_response")
        redirect(url_for("admin.create_clues"))

    elif "save_movie_attr" in request.form:

        print(request.form)
        # Connect to the database
        with MDBDimMovies() as movie_db:

            # Get the update information
            deprioritize_flag = (
                True if request.form.get("deprioritize_flag") == "on" else False
            )

            # Send update commmand to Mongo DB
            result = movie_db.collection.update_one(
                {"id": movie_id},
                {"$set": {"admin_ind_twisted_depri": deprioritize_flag}},
            )
            if result.modified_count == 0:
                logging.warning(
                    f"Movie {movie_id} not updated - Records found in upated query: {result.matched_count}"
                )
            else:
                logging.info(
                    f"{result.matched_count} found: {result.modified_count} record updated. Movie {movie_id} modified."
                )

    elif "propose_clue" in request.form:

        # Check if submitted title is valid
        logging.info("Firing clue validation process")
        filtered_errors = []
        description_contains_title = False
        for x in validation_errors:
            filtered_errors.append(x)
            if x.code == "CLUE_HAS_TITLE":
                description_contains_title = True

        check_for_clue_errors(movie_id, twist_title, filtered_errors)

        # Connect to the database
        with MDBDimClues() as clues_db:

            # Send update commmand to Mongo DB
            result = clues_db.collection.find_one(
                filter={
                    "movie_id": movie_id,
                    "raw_twist_title": raw_twist_title,
                }
            )
            if result:
                flash(
                    (
                        movie_id,
                        twist_title,
                        f"Title '{twist_title}' already exists as a clue.",
                    ),
                    "clue_proposal_error",
                )

            else:
                result = clues_db.collection.insert_one(
                    document={
                        "movie_id": movie_id,
                        "original_title": original_title,
                        "twisted_title": twist_title,
                        "raw_twisted_title": raw_twist_title,
                        "description": request.form.get("twisted_description"),
                        "creator_id": current_user.id,
                        "admin_validated": False,
                        "admin_edited": False,
                        "edit_history": {'1': request.form.get("twisted_description")},
                        "description_contains_title": description_contains_title,
                        "created_unixtime": int(time.time()),
                    }
                )
                if result.inserted_id:
                    flash((movie_id, twist_title, 'Successfully Saved Clue'), "clue_proposal_success")
                    with MDBDimMovies() as movie_db:
                        result = movie_db.collection.update_one(
                            {"id": movie_id},
                            {"$set": {"admin_ind_has_clue": True}},
                        )
                        if result.modified_count == 0:
                            logging.warning(
                                f"Movie {movie_id} not updated - Records found in upated query: {result.matched_count}"
                            )
                        else:
                            logging.info(
                                f"{result.matched_count} found: {result.modified_count} record updated. Movie {movie_id} modified."
                            )

    return redirect(url_for("admin.create_clues"))


@admin_blueprint.route("/movie_search", methods=["POST"])
@login_required
def movie_search():
    """
    This function is used to filter the movie list based on the search criteria.
    """
    
    session['movie_search_filters'] = session.get('movie_search_filters', dict({}))
    
    if "movie_filter_submit" in request.form:
        # Hide deprioritized movies
        if request.form.get("toggle_depri", False):
            session['movie_search_filters']['admin_ind_twisted_depri'] = False
        else:
            session['movie_search_filters'].pop('admin_ind_twisted_depri', '')
        # Get difficulty array
        session['movie_search_filters']['difficulty'] = [
            1 if request.form.get("diff_easy") else None,
            2 if request.form.get("diff_med") else None,
            3 if request.form.get("diff_hard") else None,
            ]


    return redirect(url_for("admin.create_clues"))




@admin_blueprint.route("/manage_clues", methods=["GET", "POST"])  
@login_required
def manage_clues():
    """
    This function is used to manage the clues in the database.
    """
    check_admin()

    filters = dict({})
    # get any filters needed
    if request.method == "POST" and "clue_filter_submit" in request.form:
        assign_filter("clue_search_filters", "original_title")
        assign_filter("clue_search_filters", "twisted_title")
        assign_filter("clue_search_filters", "admin_validated")
        assign_filter("clue_search_filters", "admin_edited")
        assign_filter("clue_search_filters", "description_contains_title")

        filters = session.get("clue_search_filters", dict({}))

    clue_list = dict({})     
    with MDBDimClues() as clues_db:
        clues = clues_db.collection.find(
            filter=filters,
            sort={
                # "admin_validated": 1,
                "created_unixtime": -1,
                },
            limit=20,
        )
        if clues == None:
            logging.warning("No clues found in mongo Response - Breaking")
        for c in clues:
            clue_list[c["_id"]] = c

    return render_template(
        "manage_clues.html",
        current_user=current_user,
        clue_list=clue_list,
        filters=filters,
    )

@admin_blueprint.route("/update_clues", methods=["POST"])
@login_required
def update_clues():
    """
    This function is used to update the clue information in the database.
    """
    check_admin()

    clue_id = request.form.get("clue_id", "")

    # Adding clue version to clue data
    if request.method == "POST" and "add_clue_version" in request.form:

        # get clue information from the form submission
        new_clue_version = request.form.get("new_clue_version", "") 
        clue_history = ast.literal_eval(request.form.get("edit_history", None))
        recent_clue = get_max_string_key_value(clue_history)

        if new_clue_version == "":
            logging.warning("No new clue version provided.")
        elif remove_non_alpha_letters(new_clue_version) == remove_non_alpha_letters(recent_clue):
            logging.warning("New clue version is the same as the most recent version.")
        else:         
            # Determine the next key as the highest existing key + 1
            existing_keys = list(map(int, clue_history.keys()))  # Convert keys to integers
            next_key = str(max(existing_keys) + 1) if existing_keys else "1"  # Increment highest key

            # Update the document
            with MDBDimClues() as clue_db:
                result = clue_db.collection.update_one(
                    {"_id": ObjectId(clue_id)},
                    {"$set": {
                        f"edit_history.{next_key}": new_clue_version,
                        "admin_edited": True,
                        "admin_validated": False,
                        "description": new_clue_version,

                        }
                    }
                )
                if result.modified_count == 0:
                    logging.warning(f"Movie {clue_id} not updated - Records found in upated query: {result.matched_count}")
                else:
                    logging.info(f"{result.matched_count} found: {result.modified_count} record updated. Clue {clue_id} modified.")
    
    # Validate the clue
    if request.method == "POST" and "validate_clue" in request.form:
        # opent the database collection
        with MDBDimClues() as clue_db:
            result = clue_db.collection.update_one(
                {"_id": ObjectId(clue_id)},
                {"$set": {"admin_validated": True,}}
            )
            if result.modified_count == 0:
                logging.warning(f"Movie {clue_id} not updated - Records found in upated query: {result.matched_count}")
            else:
                logging.info(f"{result.matched_count} found: {result.modified_count} record updated. Clue {clue_id} modified.")

    return redirect(url_for("admin.manage_clues"))

@admin_blueprint.route("/assign_clues", methods=["GET"])  
@login_required
def assign_clues():
    """
    This function is used to manage the clues in the database.
    """
    check_admin()
    
    return 'hello'