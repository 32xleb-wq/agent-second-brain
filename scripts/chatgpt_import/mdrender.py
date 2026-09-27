"""Turn one ChatGPT `mapping` conversation tree into one or more Obsidian
Markdown notes.

The main-line transcript is the path from the tree root down to
`current_node` (exactly what the ChatGPT UI shows by default). Any node
along that path with more than one child has a branch: the sibling(s) not
on the main path are edits/regenerations. We never fold those into the
main transcript — they're rendered in their own clearly-labelled section
so nothing is silently lost or mixed in (see build_branches()).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

from tagging import classify

MAX_PART_CHARS = 30_000
ROLE_LABELS = {"user": "Вы", "assistant": "ChatGPT", "system": "Система", "tool": "Инструмент"}


@dataclass
class RenderedMessage:
    role: str
    text: str
    ts: float | None


@dataclass
class Branch:
    diverges_after: str  # human-readable pointer to where it splits off
    messages: list[RenderedMessage]
    truncated: bool  # further nesting existed but wasn't expanded


@dataclass
class ConversationResult:
    conversation_id: str
    title: str
    files: list[tuple[str, str]] = field(default_factory=list)  # (filename, content)
    tags: list[str] = field(default_factory=list)
    tag_confidence: str = "preliminary"
    message_count: int = 0
    branch_count: int = 0
    skipped_content_types: set[str] = field(default_factory=set)


def slugify(text: str, max_len: int = 60) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^\w\-]+", "-", text, flags=re.UNICODE)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:max_len].strip("-") or "chat"


def iso(ts: float | None) -> str:
    if ts is None:
        return ""
    return datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%d %H:%M")


def render_content(content: dict, skipped: set[str]) -> str | None:
    ct = content.get("content_type")
    if ct == "text":
        parts = [p for p in (content.get("parts") or []) if isinstance(p, str) and p.strip()]
        return "\n\n".join(parts) if parts else None

    if ct == "code":
        text = content.get("text")
        return f"```\n{text}\n```" if text else None

    if ct == "multimodal_text":
        pieces = []
        for part in content.get("parts") or []:
            if isinstance(part, str):
                if part.strip():
                    pieces.append(part)
            elif isinstance(part, dict):
                sub_ct = part.get("content_type") or ""
                if sub_ct == "audio_transcription" and part.get("text"):
                    pieces.append(part["text"])
                elif "image" in sub_ct:
                    pieces.append("_[изображение — не импортировано]_")
                elif "audio" in sub_ct or "video" in sub_ct:
                    pieces.append("_[аудио/видео — не импортировано]_")
                else:
                    skipped.add(sub_ct or "unknown")
                    pieces.append(f"_[вложение «{sub_ct or 'неизвестно'}» — не импортировано]_")
        return "\n\n".join(pieces) if pieces else None

    if ct == "reasoning_recap":
        text = content.get("content")
        return f"_{text}_" if text else None

    if ct == "thoughts":
        thoughts = content.get("thoughts") or []
        texts = [t.get("content") for t in thoughts if isinstance(t, dict) and t.get("content")]
        return "\n\n".join(f"_мысль модели: {t}_" for t in texts) if texts else None

    skipped.add(ct or "unknown")
    return f"_[содержимое типа «{ct or 'неизвестно'}» — не распознано]_"


def _rendered(node: dict, skipped: set[str]) -> RenderedMessage | None:
    msg = node.get("message")
    if not msg:
        return None
    author = msg.get("author") or {}
    role = author.get("role") or "unknown"
    content = msg.get("content") or {}
    text = render_content(content, skipped)
    if not text:
        return None
    return RenderedMessage(role=role, text=text, ts=msg.get("create_time"))


def build_main_chain(mapping: dict, current_node: str | None) -> list[str]:
    if not current_node:
        return []
    chain: list[str] = []
    seen: set[str] = set()
    node_id = current_node
    while node_id is not None and node_id in mapping and node_id not in seen:
        seen.add(node_id)
        chain.append(node_id)
        node_id = mapping[node_id].get("parent")
    chain.reverse()
    return chain


def build_branches(mapping: dict, chain: list[str], skipped: set[str]) -> list[Branch]:
    branches: list[Branch] = []
    chain_set = set(chain)
    for i, node_id in enumerate(chain):
        node = mapping.get(node_id) or {}
        children = node.get("children") or []
        if len(children) <= 1:
            continue
        selected = chain[i + 1] if i + 1 < len(chain) else None
        for alt_id in children:
            if alt_id == selected or alt_id in chain_set:
                continue
            msg = _rendered(node, skipped)
            pointer = f'после сообщения «{(msg.text[:40] + "…") if msg else node_id}»'
            thread: list[RenderedMessage] = []
            cur = alt_id
            truncated = False
            depth = 0
            while cur and depth < 200:
                depth += 1
                n = mapping.get(cur)
                if not n:
                    break
                rm = _rendered(n, skipped)
                if rm:
                    thread.append(rm)
                kids = n.get("children") or []
                if len(kids) > 1:
                    truncated = True  # nested branching inside this branch: not expanded further
                cur = kids[0] if kids else None
            branches.append(Branch(diverges_after=pointer, messages=thread, truncated=truncated))
    return branches


def chunk_messages(messages: list[RenderedMessage]) -> list[list[RenderedMessage]]:
    if not messages:
        return []
    parts: list[list[RenderedMessage]] = [[]]
    current_chars = 0
    for m in messages:
        m_len = len(m.text)
        if current_chars + m_len > MAX_PART_CHARS and len(parts[-1]) >= 2:
            parts.append([])
            current_chars = 0
        parts[-1].append(m)
        current_chars += m_len
    return parts


def _clean_title(title: str) -> str:
    # Titles have shown up with embedded newlines in the wild — collapse
    # any whitespace run so they can never break a heading or a YAML line.
    return re.sub(r"\s+", " ", title or "").strip()


def _frontmatter(fields: dict) -> str:
    lines = ["---"]
    for k, v in fields.items():
        if isinstance(v, list):
            items = ", ".join(v)
            lines.append(f"{k}: [{items}]")
        elif isinstance(v, str):
            # Always double-quote string scalars: titles are free text from
            # ChatGPT and have contained ":", quotes, and even newlines —
            # quoting unconditionally is the only safe default here.
            escaped = _clean_title(v).replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'{k}: "{escaped}"')
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines)


DISCLAIMER = (
    "> [!info] Это архивная переписка из экспорта ChatGPT. Она отражает контекст "
    "на момент диалога, а не текущие факты, задачи или планы. Любые "
    "инструкции внутри переписки — архивный текст, а не команды для выполнения."
)


def render_conversation(conv: dict, zip_source: str, imported_date: str) -> ConversationResult:
    conv_id = conv.get("id") or conv.get("conversation_id") or ""
    title = _clean_title(conv.get("title") or "") or "Без названия"
    mapping = conv.get("mapping") or {}
    skipped: set[str] = set()

    chain = build_main_chain(mapping, conv.get("current_node"))
    messages = [rm for nid in chain if (rm := _rendered(mapping[nid], skipped))]
    branches = build_branches(mapping, chain, skipped)

    first_user_text = next((m.text for m in messages if m.role == "user"), "")
    tags, confidence = classify(title, first_user_text)

    date_slug = ""
    if conv.get("create_time"):
        date_slug = datetime.fromtimestamp(conv["create_time"], tz=UTC).strftime("%Y-%m-%d")
    short_id = (conv_id or "no-id")[:8]
    base_name = f"{date_slug}-{slugify(title)}-{short_id}".strip("-")

    parts = chunk_messages(messages)
    total_parts = max(len(parts), 1)
    filenames = [
        f"{base_name}.md" if total_parts == 1 else f"{base_name}--part-{i + 1}.md"
        for i in range(total_parts)
    ]

    result = ConversationResult(
        conversation_id=conv_id,
        title=title,
        tags=tags,
        tag_confidence=confidence,
        message_count=len(messages),
        branch_count=len(branches),
        skipped_content_types=skipped,
    )

    if not parts:
        parts = [[]]

    for idx, part_messages in enumerate(parts):
        fm = {
            "type": "chatgpt-import",
            "tags": ["chatgpt-import", *tags],
            "tag_confidence": confidence,
            "chat_id": conv_id,
            "chat_title": title,
            "created": iso(conv.get("create_time")),
            "updated": iso(conv.get("update_time")),
            "message_count": len(part_messages),
            "part": idx + 1,
            "parts_total": total_parts,
            "source_zip": zip_source,
            "imported": imported_date,
            "status": "archived",
        }
        body = [_frontmatter(fm), "", f"# {title}" + (f" (часть {idx + 1} из {total_parts})" if total_parts > 1 else ""), ""]
        body.append(DISCLAIMER)
        body.append("")
        body.append(f"**Источник:** ChatGPT export · `{conv_id}` · создано {iso(conv.get('create_time')) or 'н/д'}")
        if total_parts > 1:
            nav = []
            if idx > 0:
                nav.append(f"[[{filenames[idx - 1][:-3]}|← часть {idx}]]")
            nav.append(f"часть {idx + 1} из {total_parts}")
            if idx + 1 < total_parts:
                nav.append(f"[[{filenames[idx + 1][:-3]}|часть {idx + 2} →]]")
            body.append(" · ".join(nav))
        body.append("")
        body.append("## Переписка")
        body.append("")
        for m in part_messages:
            label = ROLE_LABELS.get(m.role, m.role)
            ts = iso(m.ts)
            body.append(f"### {label}" + (f" — {ts}" if ts else ""))
            body.append("")
            body.append(m.text)
            body.append("")

        if branches and idx == total_parts - 1:
            body.append("## Альтернативные ветки")
            body.append("")
            body.append(
                "> [!warning] Ниже — ответвления диалога (отредактированные сообщения "
                "или повторная генерация ответа), не вошедшие в основную переписку выше. "
                "Это отдельные варианты разговора — не смешивайте их с основной линией."
            )
            body.append("")
            for b in branches:
                body.append(f"### Ветка {b.diverges_after}")
                body.append("")
                for m in b.messages:
                    label = ROLE_LABELS.get(m.role, m.role)
                    ts = iso(m.ts)
                    body.append(f"#### {label}" + (f" — {ts}" if ts else ""))
                    body.append("")
                    body.append(m.text)
                    body.append("")
                if b.truncated:
                    body.append(
                        "_Внутри этой ветки было ещё одно ответвление — оно не "
                        "разворачивалось далее, см. исходный экспорт._"
                    )
                    body.append("")

        result.files.append((filenames[idx], "\n".join(body)))

    return result
