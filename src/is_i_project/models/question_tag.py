from is_i_project.extensions import db


class QuestionTag(db.Model):
    __tablename__ = 'question_tag'

    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), primary_key=True)
