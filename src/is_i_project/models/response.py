from is_i_project.extensions import db
from is_i_project.models.post import Post
from sqlalchemy.orm import relationship

class Response (Post):
    id = db.Column(db.Integer, db.ForeignKey('post.id'), primary_key = True)
    accepted = db.Column(db.Boolean, default = False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'))

    # author = relationship(back_populates = 'questions')
