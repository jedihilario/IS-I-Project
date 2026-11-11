from is_i_project.extensions import db
from is_i_project.models.author import Author
from is_i_project.models.role import Role

class User (Author):
    id = db.Column(db.Integer, db.ForeignKey('author.id'), primary_key = True)
    name = db.Column(db.String(31), nullable = False)
    password = db.Column(db.String(127), nullable = False)
    email = db.Column(db.String(127), nullable = False, unique = True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

    def __repr__(self) -> str:
        return f'<User {self.id}, {self.email}>'
