from is_i_project.extensions import db


class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    is_positive = db.Column(db.Boolean, nullable=False)
    date = db.Column(db.Date)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    post = db.relationship('Post', back_populates='votes', foreign_keys=[post_id])
    user = db.relationship('User', back_populates='votes', foreign_keys=[user_id])
