from is_i_project.extensions import db

class Tag (db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(63), unique = True)
