from is_i_project.extensions import db
from is_i_project.models.question import Question
from is_i_project.models.tag import Tag

class QuestionTag (db.Model):
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'))

    db.PrimaryKeyConstraint(question_id, tag_id)