from is_i_project.extensions import db

class User (db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(31), nullable = False)
    email = db.Column(db.String(127), nullable = False, unique = True)

    def __repr__(self) -> str:
        return f'<User {self.id}, {self.email}>'
