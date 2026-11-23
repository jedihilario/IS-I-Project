from is_i_project.extensions import db

class Post (db.Model):
    id = db.Column(db.Integer, primary_key = True)
    body = db.Column(db.String(255), nullable = False)
    post_date = db.Column(db.Date, nullable = False)
