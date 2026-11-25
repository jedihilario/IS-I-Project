from is_i_project.extensions import db
from is_i_project.models.post import Post


class Response(Post):
    id = db.Column(db.Integer, db.ForeignKey('post.id'), primary_key=True)
    accepted = db.Column(db.Boolean, default=False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)

    author = db.relationship(
        'Author', back_populates='responses', foreign_keys=[author_id]
    )
    question = db.relationship(
        'Question', back_populates='responses', foreign_keys=[question_id]
    )
