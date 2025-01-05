from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import current_user
from assets.title_prompts import title_prompts

MAX_ATTEMPTS = 3

# Create a Blueprint
game_blueprint = Blueprint("game", __name__)

@game_blueprint.route("/", methods=["GET", "POST"])
def index():

    clue = title_prompts[1]

    if "attempt" not in session:
        session["attempt_list"] = {i:{"answer":None,"correct":None} for i in range(1,MAX_ATTEMPTS+1)}
        session["attempt"] = 0
        session["game_over"] = False
        
    # check the user answer
    if request.method == "POST":

        # if session has hit max attempts to answer
        if session["game_over"]:
            # redirect to home page with 
            return redirect(url_for("game.index"))

        # if session has hit max attempts to answer
        user_answer = request.form.get("answer", "").strip().upper()
        session["attempt"] += 1
        attempt = str(session["attempt"])
        session["attempt_list"][attempt]['answer'] = user_answer
        
        # if the user answer is correct
        if user_answer == clue.twisted_title.upper():
            session["attempt_list"][attempt]['correct'] = True
            session["game_over"] = True
        

        # if the page loads and the max attempts are reached
        elif session["attempt"] >= MAX_ATTEMPTS:    
            session["attempt_list"][attempt]['correct'] = False
            session["message"] = f"Game Over! The correct answer was '{clue.twisted_title.upper()}'."
            session["game_over"] = True
        
        else:
            session["attempt_list"][attempt]['correct'] = False
        # else:
        #     session["message"] = f"Incorrect! You have {MAX_ATTEMPTS - session['attempt']} attempts left."

        return redirect(url_for("game.index"))
    
    return render_template(
        "index.html", 
        current_user=current_user,
        clue=clue.prompt, 
        message=session.get("message", ""),
        attempt_list=session.get("attempt_list", dict()),
        correct_attempt=session.get("correct_response", None),
        )

@game_blueprint.route("/reset")
def reset():
    session.pop("attempt", None)
    session["game_over"] = False
    session['correct_response'] = None
    session.pop("message", None)
    return redirect(url_for("game.index"))

@game_blueprint.route("/about")
def about():
    return render_template("about.html", current_user=current_user) 