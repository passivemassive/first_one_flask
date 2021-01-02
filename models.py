from web_main import db, login_manager, app
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    items = db.relationship('Item', backref='item_owner_id', lazy =True)
    innates = db.relationship('Innate', backref='innate_owner_id', lazy=True)
    
    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s= Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"

class Item(db.Model):
    id = db.Column(db.Integer, primary_key= True)
    designation = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(40), nullable=False)
    i_owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Item('{self.designation}', '{self.location}')"

class Innate(db.Model):
    id = db.Column(db.Integer, primary_key= True)
    title = db.Column(db.String(100), nullable=False)
    innated = db.Column(db.Text, nullable=False)
    n_owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Content('{self.title}', '{self.n_owner_id}')"