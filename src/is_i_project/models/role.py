from is_i_project.extensions import db

class Role (db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(31), nullable = False, unique = True)
