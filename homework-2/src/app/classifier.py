"""Rule-based ticket classifier.

Deterministic and explainable: keyword dictionaries score each category
(subject matches count double), ordered keyword rules pick the priority,
and the confidence reflects both how dominant the winning category is and
how many distinct keywords supported it.
"""

import logging
import re
from dataclasses import dataclass

from app.schemas import Category, Priority

logger = logging.getLogger("app.classifier")

SUBJECT_WEIGHT = 2.0
NO_MATCH_CONFIDENCE = 0.3
MAX_CONFIDENCE = 0.95

# keyword -> weight; higher weight = stronger signal for the category
CATEGORY_KEYWORDS: dict[Category, dict[str, float]] = {
    Category.account_access: {
        "login": 2, "log in": 2, "logged out": 2, "sign in": 2, "signin": 2,
        "password": 2, "2fa": 3, "two-factor": 3, "mfa": 3, "otp": 2,
        "authentication": 2, "locked out": 3, "account locked": 3,
        "credentials": 2, "access my account": 3, "access denied": 2,
        "session expired": 2, "verification code": 2,
    },
    Category.billing_question: {
        "billing": 3, "invoice": 3, "payment": 3, "refund": 3, "charge": 2,
        "charged": 2, "subscription": 2, "credit card": 2, "pricing": 2,
        "price": 1, "receipt": 2, "overcharged": 3, "renewal": 2, "plan": 1,
    },
    # bug_report = defect with reproduction details; repro signals carry the
    # highest weights so they outrank plain technical_issue keywords
    Category.bug_report: {
        "steps to reproduce": 4, "reproduce": 3, "reproduction": 3,
        "expected behavior": 4, "expected behaviour": 4,
        "actual behavior": 4, "actual behaviour": 4,
        "expected result": 3, "actual result": 3,
        "stack trace": 3, "regression": 3, "defect": 3,
    },
    Category.technical_issue: {
        "error": 2, "bug": 2, "crash": 3, "crashes": 3, "crashed": 3,
        "broken": 2, "not working": 2, "doesn't work": 2, "does not work": 2,
        "fails": 2, "failure": 2, "exception": 2, "timeout": 2,
        "freezes": 2, "glitch": 2, "slow": 1, "500": 2,
    },
    Category.feature_request: {
        "feature request": 4, "feature": 2, "enhancement": 3,
        "improvement": 2, "would be nice": 3, "would love": 2,
        "please add": 3, "add support": 3, "suggestion": 2, "suggest": 2,
        "wish": 1, "idea": 1,
    },
}

# extra bug_report signal: a numbered step list in the description
NUMBERED_STEPS_RE = re.compile(r"(?m)^\s*\d+[.)]\s")
NUMBERED_STEPS_LABEL = "numbered step list"
NUMBERED_STEPS_WEIGHT = 3.0

# checked in order; first priority with a hit wins, otherwise medium
PRIORITY_RULES: list[tuple[Priority, tuple[str, ...]]] = [
    (Priority.urgent, (
        "can't access", "cannot access", "can not access", "critical",
        "production down", "production is down", "security", "urgent", "emergency",
    )),
    (Priority.high, ("important", "blocking", "blocked", "asap", "as soon as possible")),
    (Priority.low, ("minor", "cosmetic", "suggestion", "nice to have", "typo")),
]


@dataclass
class Classification:
    category: Category
    priority: Priority
    confidence: float
    reasoning: str
    keywords_found: list[str]


def _matches(text: str, keyword: str) -> bool:
    return re.search(rf"\b{re.escape(keyword)}\b", text) is not None


def classify(subject: str, description: str) -> Classification:
    subject_l = subject.lower()
    description_l = description.lower()

    scores: dict[Category, float] = {}
    matched: dict[Category, list[str]] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0.0
        hits: list[str] = []
        for keyword, weight in keywords.items():
            keyword_score = 0.0
            if _matches(subject_l, keyword):
                keyword_score += weight * SUBJECT_WEIGHT
            if _matches(description_l, keyword):
                keyword_score += weight
            if keyword_score:
                score += keyword_score
                hits.append(keyword)
        if category is Category.bug_report and NUMBERED_STEPS_RE.search(description):
            score += NUMBERED_STEPS_WEIGHT
            hits.append(NUMBERED_STEPS_LABEL)
        if score:
            scores[category] = score
            matched[category] = hits

    priority, priority_keywords = _classify_priority(subject_l, description_l)

    if not scores:
        category = Category.other
        confidence = NO_MATCH_CONFIDENCE
        category_reason = "No category keywords matched; defaulting to 'other'."
        keywords_found = []
    else:
        category = max(scores, key=scores.get)
        keywords_found = matched[category]
        total = sum(scores.values())
        dominance = scores[category] / total
        saturation = 1 - 0.6 ** len(keywords_found)
        confidence = min(MAX_CONFIDENCE, round(0.3 + 0.65 * dominance * saturation, 2))
        category_reason = (
            f"Category '{category.value}' matched keywords: {', '.join(keywords_found)} "
            f"(score {scores[category]:g} of {total:g} across all categories)."
        )

    if priority_keywords:
        priority_reason = (
            f"Priority '{priority.value}' matched keywords: {', '.join(priority_keywords)}."
        )
    else:
        priority_reason = "No priority keywords matched; defaulting to 'medium'."

    result = Classification(
        category=category,
        priority=priority,
        confidence=confidence,
        reasoning=f"{category_reason} {priority_reason}",
        keywords_found=keywords_found + priority_keywords,
    )
    logger.info(
        "Classified ticket subject=%r -> category=%s priority=%s confidence=%.2f keywords=%s",
        subject, result.category.value, result.priority.value, result.confidence,
        result.keywords_found,
    )
    return result


def _classify_priority(subject_l: str, description_l: str) -> tuple[Priority, list[str]]:
    for priority, keywords in PRIORITY_RULES:
        hits = [
            kw for kw in keywords
            if _matches(subject_l, kw) or _matches(description_l, kw)
        ]
        if hits:
            return priority, hits
    return Priority.medium, []
