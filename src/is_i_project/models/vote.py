from is_i_project.extensions import db
from sqlalchemy.orm import relationship

class Vote (db.Model):
    id = db.Column(db.Integer, primary_key = True)
    is_positive = db.Column(db.Boolean, nullable = False)
    date = db.Column(db.Date)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # post = relationship(back_populates = 'votes')
