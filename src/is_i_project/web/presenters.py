from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from flask import current_app
from sqlalchemy import func

from is_i_project.api.utils import (
    calculate_user_reputation,
    get_post_score,
    get_user_role_name,
    get_user_vote,
)
from is_i_project.extensions import db
from is_i_project.models import (
    AI_Author,
    Author,
    Category,
    Question,
    Response,
    Tag,
    User,
    Vote,
)
from is_i_project.models.types import Author_Type

MODEL_TO_PROVIDER = {
    "gpt-4o": "openai",
    "openai": "openai",
    "gemini": "gemini",
    "local": "local",
    "local llm": "local",
}


@dataclass
class UserVM:
    id: int
    name: str
    email: str
    role: str
    reputation: int
    questions_count: int
    answers_count: int
    avatar_url: str | None = None
    registered_at: date | None = None
    created_at: date | None = None
    type: str = "User"
    author_type: Author_Type = Author_Type.HUMAN


@dataclass
class AIAuthorVM:
    id: int
    modelName: str
    name: str = "AutorIA"
    type: str = "AI"
    author_type: Author_Type = Author_Type.LLM
    reputation: int = 0
    avatar_url: str | None = None


@dataclass
class QuestionVM:
    id: int
    title: str
    body: str
    category: str | None
    tags: list[str]
    score: int
    answers_count: int
    has_accepted: bool
    has_ai_response: bool
    post_date: date | None
    author: UserVM | None
    views: int = 0


@dataclass
class AnswerVM:
    id: int
    body: str
    score: int
    accepted: bool
    user_vote: int
    post_date: date | None
    author: UserVM | AIAuthorVM | None
    question: QuestionVM | None = None


@dataclass
class VotePostVM:
    id: int
    type: str
    title: str | None = None
    body: str = ""
    question_id: int | None = None


@dataclass
class VoteVM:
    id: int
    is_positive: bool
    date: date | None
    post: VotePostVM


@dataclass
class CategoryVM:
    id: int
    name: str
    description: str
    count: int
    answered_count: int


@dataclass
class TagVM:
    id: int
    name: str
    count: int


@dataclass
class AIConfigVM:
    provider: str = "openai"
    hours_threshold: int = 24
    timeout: int = 60
    enabled: bool = True


@dataclass
class SimplePagination:
    page: int
    per_page: int
    total: int
    pages: int = field(init=False)

    def __post_init__(self) -> None:
        self.pages = math.ceil(self.total / self.per_page) if self.total > 0 else 0

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    def iter_pages(self) -> list[int | None]:
        if self.pages <= 7:
            return list(range(1, self.pages + 1))
        result: list[int | None] = [1]
        start = max(2, self.page - 1)
        end = min(self.pages - 1, self.page + 1)
        if start > 2:
            result.append(None)
        result.extend(range(start, end + 1))
        if end < self.pages - 1:
            result.append(None)
        result.append(self.pages)
        return result


def build_user_vm(user: User | None) -> UserVM | None:
    if user is None:
        return None
    return UserVM(
        id=user.id,
        name=user.name,
        email=user.email,
        role=get_user_role_name(user),
        reputation=calculate_user_reputation(user),
        questions_count=len(user.questions),
        answers_count=len(user.responses),
    )


def build_author_vm(author: Author | None) -> UserVM | AIAuthorVM | None:
    if author is None:
        return None
    if isinstance(author, AI_Author):
        return AIAuthorVM(
            id=author.id,
            modelName=author.modelName,
        )
    if isinstance(author, User):
        return build_user_vm(author)
    return None


def build_question_vm(question: Question) -> QuestionVM:
    responses = question.responses
    return QuestionVM(
        id=question.id,
        title=question.title,
        body=question.body,
        category=question.category.name if question.category is not None else None,
        tags=sorted(tag.name for tag in question.tags if tag.name is not None),
        score=get_post_score(question),
        answers_count=len(responses),
        has_accepted=any(bool(r.accepted) for r in responses),
        has_ai_response=any(isinstance(r.author, AI_Author) for r in responses),
        post_date=question.post_date,
        author=build_user_vm(question.author),
    )


def build_answer_vm(
    response: Response,
    current_user_id: int | None = None,
    include_question: bool = False,
) -> AnswerVM:
    return AnswerVM(
        id=response.id,
        body=response.body,
        score=get_post_score(response),
        accepted=bool(response.accepted),
        user_vote=get_user_vote(response, current_user_id),
        post_date=response.post_date,
        author=build_author_vm(response.author),
        question=build_question_vm(response.question)
        if include_question and response.question is not None
        else None,
    )


def build_vote_vm(vote: Vote) -> VoteVM | None:
    if vote.post_id is None:
        return None

    question = db.session.get(Question, vote.post_id)
    if question is not None:
        return VoteVM(
            id=vote.id,
            is_positive=bool(vote.is_positive),
            date=vote.date,
            post=VotePostVM(
                id=question.id,
                type="question",
                title=question.title,
                body=question.body,
                question_id=question.id,
            ),
        )

    response = db.session.get(Response, vote.post_id)
    if response is not None:
        return VoteVM(
            id=vote.id,
            is_positive=bool(vote.is_positive),
            date=vote.date,
            post=VotePostVM(
                id=response.id,
                type="answer",
                title=None,
                body=response.body,
                question_id=response.question_id,
            ),
        )

    return None


def build_category_vm(category: Category) -> CategoryVM:
    questions = category.questions
    name = category.name or "Sin nombre"
    return CategoryVM(
        id=category.id,
        name=name,
        description=f"Preguntas relacionadas con {name}",
        count=len(questions),
        answered_count=sum(1 for q in questions if q.responses),
    )


def build_tag_vm(tag: Tag) -> TagVM:
    return TagVM(
        id=tag.id,
        name=tag.name or "",
        count=len(tag.questions),
    )


def count_unanswered_questions() -> int:
    return (
        db.session.execute(
            db.select(func.count(Question.id)).where(~Question.responses.any())
        ).scalar()
        or 0
    )


def build_global_stats() -> dict[str, Any]:
    week_ago = date.today() - timedelta(days=7)

    total_users = db.session.execute(db.select(func.count(User.id))).scalar() or 0
    total_questions = (
        db.session.execute(db.select(func.count(Question.id))).scalar() or 0
    )
    total_answers = (
        db.session.execute(db.select(func.count(Response.id))).scalar() or 0
    )
    ai_answers = (
        db.session.execute(
            db.select(func.count(Response.id)).where(
                Response.author.has(Author.author_type == Author_Type.LLM)
            )
        ).scalar()
        or 0
    )
    new_questions_week = (
        db.session.execute(
            db.select(func.count(Question.id)).where(Question.post_date >= week_ago)
        ).scalar()
        or 0
    )
    new_answers_week = (
        db.session.execute(
            db.select(func.count(Response.id)).where(Response.post_date >= week_ago)
        ).scalar()
        or 0
    )
    pct_ia = round((ai_answers / total_answers) * 100) if total_answers > 0 else 0

    return {
        "total_users": total_users,
        "total_questions": total_questions,
        "total_answers": total_answers,
        "ai_answers": ai_answers,
        "new_users_week": 0,
        "new_questions_week": new_questions_week,
        "new_answers_week": new_answers_week,
        "pct_ia": pct_ia,
    }


def get_ai_config() -> AIConfigVM:
    cfg = current_app.config.get("AI_CONFIG", {})
    ai_author = db.session.execute(
        db.select(AI_Author).order_by(AI_Author.id.asc())
    ).scalars().first()

    provider = cfg.get("provider", "openai")
    timeout = cfg.get("timeout", 60)

    if ai_author is not None:
        provider = MODEL_TO_PROVIDER.get(
            (ai_author.modelName or "").strip().lower(), provider
        )
        if ai_author.timeout is not None:
            timeout = ai_author.timeout

    return AIConfigVM(
        provider=provider,
        hours_threshold=int(cfg.get("hours_threshold", 24)),
        timeout=int(timeout),
        enabled=bool(cfg.get("enabled", True)),
    )
