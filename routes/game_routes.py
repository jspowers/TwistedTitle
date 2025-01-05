from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import current_user
from assets.title_prompts import title_prompts

MAX_ATTEMPTS = 3

# Create a Blueprint
game_blueprint = Blueprint("game", __name__)

@game_blueprint.route("/", methods=["GET", "POST"])
def index():

    clue = title_prompts[1]

    if "attempts" not in session:
        session["attempts"] = 0
        session["game_over"] = False

    # check the user answer
    if request.method == "POST":

        # if session has hit max attempts to answer
        if session["game_over"]:
            # redirect to home page with 
            return redirect(url_for("game.index"))

        # if session has hit max attempts to answer
        user_answer = request.form.get("answer", "").strip().lower()
        session["attempts"] += 1

        # if the user answer is correct
        if user_answer == clue.twisted_title:
            session["message"] = "Correct! You solved the riddle!"
            session['correct_response'] = session['attempts']
            session["game_over"] = True
        
        # if the page loads and the max attempts are reached
        elif session["attempts"] >= MAX_ATTEMPTS:
            session["message"] = f"Game Over! The correct answer was '{clue.twisted_title}'."
            session["game_over"] = True
        else:
            session["message"] = f"Incorrect! You have {MAX_ATTEMPTS - session['attempts']} attempts left."

        return redirect(url_for("game.index"))
    
    return render_template(
        "index.html", 
        current_user=current_user,
        clue=clue.prompt, 
        message=session.get("message", ""),
        attempts=session.get("attempts", ""),
        correct_attempt=session.get("correct_response", None),
        )

@game_blueprint.route("/reset")
def reset():
    session["attempts"] = 0
    session["game_over"] = False
    session['correct_response'] = None
    return redirect(url_for("game.index"))

@game_blueprint.route("/about")
def about():
    return render_template("about.html", current_user=current_user) 