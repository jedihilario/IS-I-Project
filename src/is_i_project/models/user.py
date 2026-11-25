from typing import ClassVar

from is_i_project.extensions import db
from is_i_project.models.author import Author
from is_i_project.models.types import Author_Type


class User(Author):
    id = db.Column(db.Integer, db.ForeignKey('author.id'), primary_key=True)
    name = db.Column(db.String(31), nullable=False)
    password = db.Column(db.String(127), nullable=False)
    email = db.Column(db.String(127), nullable=False, unique=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

    questions = db.relationship(
        'Question',
        back_populates='author',
        foreign_keys='Question.author_id',
        cascade='all, delete-orphan',
    )
    votes = db.relationship(
        'Vote',
        back_populates='user',
        foreign_keys='Vote.user_id',
        cascade='all, delete-orphan',
    )

    __mapper_args__: ClassVar[dict[str, object]] = {
        'polymorphic_identity': Author_Type.HUMAN,
    }

    def __repr__(self) -> str:
        return f'<User {self.id}, {self.email}>'
