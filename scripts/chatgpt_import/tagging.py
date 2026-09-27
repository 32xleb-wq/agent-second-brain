"""Deterministic, keyword-based thematic tagging — no model calls per item
(the import must be able to run unattended, and must not spend API budget).

Taxonomy follows the plan already recorded in vault/MEMORY.md before this
import ("держать 5-7 верхнеуровневых тегов... не создавать новые узкие
теги под каждую мысль"), extended with a couple of buckets that the actual
export data turned out to need (a lot of it is AI-tooling/automation and
business chatter, not covered by the original 6).

Classification looks only at the conversation title + the first user
message (cheap, and avoids overfitting on verbose assistant replies). If
nothing matches confidently, the note gets "general" and is flagged
tag_confidence=preliminary — per the task's "неуверенную классификацию
отмечай как предварительную".
"""

from __future__ import annotations

import re

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "health": [
        "здоровь", "врач", "клиник", "анализ", "тестостерон", "гзт", "простат",
        "узи", "фгдс", "колоноскоп", "горло", "вес", "похуде", "сон", "диета",
        "тренировк", "холестерин", "health", "doctor", "medical",
    ],
    "content": [
        "видео", "рилс", "reels", "youtube", "сценар", "хук", "блог", "съём",
        "монтаж", "контент-план", "content plan", "подкаст", "script", "тикток",
        "tiktok", "инстаграм", "instagram", "подписчик",
    ],
    "relationships": [
        "отношени", "друзья", "дружб", "одиночеств", "девушк", "семь", "любов",
        "социализац", "партнёр", "партнер", "family",
    ],
    "defi": [
        "defi", "крипт", "стейкинг", "staking", "кошелек", "кошелёк", "токен",
        "usdt", "солана", "solana", "pendle", "morpho", "okex", "avax", "апы",
        "apy", "leverage", "плечо",
    ],
    "growth": [
        "психолог", "матрица судьбы", "human design", "дизайн человека",
        "эзотерик", "саморазвит", "медитац", "смысл жизни", "личностный рост",
        "цели", "привычк",
    ],
    "ai-tools": [
        "ии", "нейросет", "gpt", "chatgpt", "openai", "midjourney",
        "ai", "промт", "промпт", "prompt", "автоматизац", "make.com",
        "flux", "модел", "искусственный интеллект", "робот",
    ],
    "business": [
        "бизнес", "стартап", "инвест", "компани", "маркетинг", "продаж",
        "клиент", "business", "startup", "seo",
    ],
}

TAG_ORDER = list(TOPIC_KEYWORDS.keys()) + ["general"]

_word_re = re.compile(r"[a-zа-яё0-9]+", re.IGNORECASE)


def _leading_boundary_count(haystack: str, kw: str) -> int:
    # Leading \b only (not trailing): lets short roots like "вес" still
    # match inflections ("весом", "веса"), while still rejecting them as
    # a same-word fragment inside an unrelated word ("извес[тно]" has no
    # boundary right before "вес", so it's correctly excluded).
    return len(re.findall(r"\b" + re.escape(kw), haystack))


def classify(title: str, first_user_text: str) -> tuple[list[str], str]:
    """Return (tags, confidence). confidence is 'matched' or 'preliminary'."""
    haystack = f"{title}\n{first_user_text}".lower()
    scores: dict[str, int] = {}
    for tag, keywords in TOPIC_KEYWORDS.items():
        hits = sum(_leading_boundary_count(haystack, kw) for kw in keywords)
        if hits:
            scores[tag] = hits

    if not scores:
        return ["general"], "preliminary"

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top_tags = [t for t, _ in ranked[:3]]
    # A single weak hit (score 1) on an otherwise empty title is still a
    # guess, not a confident match — flag it so a human can double-check.
    confidence = "matched" if ranked[0][1] >= 2 or len(title.strip()) >= 8 else "preliminary"
    return top_tags, confidence
