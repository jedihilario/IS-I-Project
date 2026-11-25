from typing import ClassVar

from is_i_project.extensions import db
from is_i_project.models.author import Author
from is_i_project.models.types import Author_Type


class AI_Author(Author):
    id = db.Column(db.Integer, db.ForeignKey('author.id'), primary_key=True)
    modelName = db.Column(db.String(127), nullable=False)
    timeout = db.Column(db.Integer)

    __mapper_args__: ClassVar[dict[str, object]] = {
        'polymorphic_identity': Author_Type.LLM,
    }
