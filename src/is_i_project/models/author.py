from is_i_project.extensions import db
from is_i_project.models.types import Author_Type

class Author (db.Model):
    __tablename__ = 'author'

    id = db.Column(db.Integer, primary_key = True)
    author_type = db.Column(db.Enum(Author_Type), nullable = False, default = Author_Type.HUMAN)
