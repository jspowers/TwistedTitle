import time
import logging
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
from utilities.pymongo.collections.DimMovies import MDBDimMovies
from utilities.pymongo.collections.DimClues import MDBDimClues
from utilities.get_movie_neighbors import get_movie_neighbors
from utilities.chatGPT.gpt_requests import get_twisted_title_description
from utilities.validate_clue import validate_clue
from utilities.global_utils import remove_non_alpha_letters

# Create a Blueprint
admin_blueprint = Blueprint("admin", __name__)


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


@admin_blueprint.route("/create_clues", methods=["GET", "POST"])
@login_required
def create_clues(**kwargs):
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


@admin_blueprint.route("/update_clue", methods=["POST"])
@login_required
def update_clue():

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