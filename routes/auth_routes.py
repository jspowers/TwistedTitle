import logging
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import login_user, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import User
from extensions import twisted_db

# Create a Blueprint
auth_blueprint = Blueprint("auth", __name__)

@auth_blueprint.route('/profile')
def profile():
    return "Lol fuck you"



@auth_blueprint.route('/', methods=['POST', 'GET'])
def login():
    error = None
    if current_user.is_authenticated:
        return redirect(url_for('game.index'))
    
    form_username = request.form.get('username')
    form_password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = twisted_db.session.execute(
        twisted_db.select(User).filter_by(username = form_username)
        ).scalar_one_or_none()
    
    if request.method == 'POST':
        if not user: 
            logging.warning('user attempted username does not exist in database.')
            error = 'No matching accounts with given username. Please try again.'
        elif check_password_hash(user.password, form_password):
            logging.info('User successfully logged into account.')
            login_user(user, remember=remember)
            return redirect(url_for('home.home_profile'))
        elif check_password_hash(user.password, form_password) == False:
            logging.warning('user attempted username/password combo does not match.')
            error = 'Invalid credentials. Please try again.'
    if error:
        flash(error)
    # return render_template('login.html')
    return 'lol you logged in, idiot'

@auth_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    
    if request.method == 'GET':
        # check to see if current user is authenticated
        if current_user.is_authenticated:
            return redirect(url_for('game.index'))
        return render_template('register.html') 
    
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    first_name = request.form.get('first_name')

    # User Registration form validation
    errors = []
    
    user_username = twisted_db.session.execute(
        twisted_db.select(User).filter_by(username = username)
        ).scalar_one_or_none()
    
    if user_username:
        errors.append('Username already registered with another accounts.')
    if password != confirm_password:
        errors.append('Passwords do not match, pease try again.')
    
    if len(errors) == 0:
        new_user = User(
            username=username,
            password = generate_password_hash(password, method='scrypt'),
            first_name = first_name,
            )
        twisted_db.session.add(new_user)
        twisted_db.session.commit()
        user = twisted_db.session.execute(
            twisted_db.select(User).filter_by(username = username)
            ).scalar_one_or_none()
        login_user(user, remember=False)
        return redirect(url_for('game.index'))
    else:
        for error in errors:
            flash(error)
        return render_template('register.html')



@auth_blueprint.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
        return "lol you logged out"
    else:
        return render_template(
            'index.html',
            current_user_authenticated = current_user.is_authenticated,
            user_username = current_user.username,
        )