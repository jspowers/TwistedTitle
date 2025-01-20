from extensions import twisted_db as db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    username = db.Column(db.String(124), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_demo = db.Column(db.Boolean, default=False)
    is_god = db.Column(db.Boolean, default=False)
    created_unixtime = db.Column(db.Integer, nullable=True)
    
    def __repr__(self):
        return '<User {}>'.format(self.username)
    
    def set_password(self, password):
        self.password = password