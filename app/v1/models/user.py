from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column('id', db.Integer, primary_key=True)
    username = db.Column('username', db.String(50), unique=True, nullable=False)
    email = db.Column('email', db.String(100), unique=True, nullable=False)
    password_hash = db.Column('password_hash', db.String(255), nullable=False)
    fullname = db.Column('fullname', db.String(100))
    bio = db.Column('bio', db.Text)
    profile_picture = db.Column('profile_picture', db.String(255), default='default.jpg')
    created_at = db.Column(
        'created_at', 
        db.Integer, 
        default=lambda: int(datetime.now().timestamp())
    )
    updated_at = db.Column(
        'updated_at', 
        db.Integer, 
        default=lambda: int(datetime.now().timestamp()),
        onupdate=lambda: int(datetime.now().timestamp())
    )
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'fullname': self.fullname,
            'bio': self.bio,
            'profile_picture': self.profile_picture,
            'created_at': self.created_at,
        }
