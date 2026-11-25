from is_i_project.extensions import db
from is_i_project.models.post import Post


class Question(Post):
    id = db.Column(db.Integer, db.ForeignKey('post.id'), primary_key=True)
    title = db.Column(db.String(63), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    author = db.relationship(
        'User', back_populates='questions', foreign_keys=[author_id]
    )
    category = db.relationship(
        'Category', back_populates='questions', foreign_keys=[category_id]
    )
    responses = db.relationship(
        'Response',
        back_populates='question',
        foreign_keys='Response.question_id',
        cascade='all, delete-orphan',
    )
    tags = db.relationship(
        'Tag', secondary='question_tag', back_populates='questions'
    )
