from is_i_project.extensions import db


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(63), unique=True)

    questions = db.relationship(
        'Question', secondary='question_tag', back_populates='tags'
    )
