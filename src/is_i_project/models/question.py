from is_i_project.extensions import db
from is_i_project.models.post import Post
from sqlalchemy.orm import relationship

class Question (Post):
    id = db.Column(db.Integer, db.ForeignKey('post.id'), primary_key = True)
    title = db.Column(db.String(63), nullable = False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    # author = relationship(back_populates = 'questions')
    # category = relationship(back_populates = 'questions')
