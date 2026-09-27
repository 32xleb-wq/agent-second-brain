"""Static definition of dashboard sections (nav + empty-state copy).

No data is fetched or invented here — v1 is a navigable skeleton only.
"""

from dataclasses import dataclass

# Minimal stroke-style icons (24x24, currentColor) — no external assets.
_ICONS = {
    "home": (
        '<path d="M4 11.5 12 4l8 7.5"/>'
        '<path d="M6 10v9a1 1 0 0 0 1 1h4v-6h2v6h4a1 1 0 0 0 1-1v-9"/>'
    ),
    "tasks": (
        '<rect x="4" y="4" width="16" height="16" rx="2"/>'
        '<path d="m8 12 2.5 2.5L16 9"/>'
    ),
    "defi": (
        '<circle cx="12" cy="12" r="8"/>'
        '<path d="M12 8v8M9.5 10.5a2.5 2 0 0 1 2.5-1.5c1.4 0 2.5.7 2.5 1.8 '
        's-1.1 1.7-2.5 1.7c-1.4 0-2.5.7-2.5 1.8s1.1 1.7 2.5 1.7a2.5 2 0 0 0 2.5-1.5"/>'
    ),
    "content": (
        '<path d="M7 3h8l4 4v14a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/>'
        '<path d="M15 3v4h4M9 12h6M9 16h6M9 8h2"/>'
    ),
    "health": (
        '<path d="M12 20s-7-4.35-9.5-9A5.5 5.5 0 0 1 12 6a5.5 5.5 0 0 1 9.5 5c-2.5 4.65-9.5 9-9.5 9z"/>'
        '<path d="M4 12h3l1.5-3L11 15l1.5-4H20"/>'
    ),
    "obsidian": (
        '<path d="M12 3 4 9l3 10h10l3-10z"/>'
        '<path d="M12 3v6M8 19l4-4 4 4"/>'
    ),
}


@dataclass(frozen=True)
class Section:
    key: str
    path: str
    label: str
    icon: str
    title: str
    lead: str
    body: str


SECTIONS: list[Section] = [
    Section(
        key="home",
        path="/",
        label="Главная",
        icon=_ICONS["home"],
        title="Главная",
        lead="Общий обзор второго мозга.",
        body="",
    ),
    Section(
        key="tasks",
        path="/tasks",
        label="Задачи",
        icon=_ICONS["tasks"],
        title="Задачи",
        lead="Здесь появятся ваши задачи.",
        body=(
            "В следующих версиях здесь будет список активных и выполненных "
            "задач с их статусами, синхронизированный с ботом и заметками "
            "в Obsidian. Пока раздел пуст — реальные задачи ещё не подключены."
        ),
    ),
    Section(
        key="defi",
        path="/defi",
        label="DeFi",
        icon=_ICONS["defi"],
        title="DeFi",
        lead="Здесь появится обзор DeFi-активности.",
        body=(
            "Раздел предназначен для обзора кошельков, позиций и балансов "
            "после подключения интеграций с блокчейн-сетями и биржами. "
            "Сейчас интеграции не настроены, поэтому данных нет."
        ),
    ),
    Section(
        key="content",
        path="/content",
        label="Контент",
        icon=_ICONS["content"],
        title="Контент",
        lead="Здесь появится обзор контента.",
        body=(
            "Здесь будет собран статус контента: черновики, публикации и "
            "идеи из заметок. Пока раздел не подключён к источникам данных."
        ),
    ),
    Section(
        key="health",
        path="/health",
        label="Здоровье",
        icon=_ICONS["health"],
        title="Здоровье",
        lead="Здесь появятся показатели здоровья.",
        body=(
            "В будущем здесь будут отображаться показатели здоровья и "
            "привычек после подключения источников данных. Реальных "
            "показателей пока нет."
        ),
    ),
    Section(
        key="obsidian",
        path="/obsidian",
        label="Obsidian",
        icon=_ICONS["obsidian"],
        title="Obsidian",
        lead="Здесь появится обзор хранилища заметок.",
        body=(
            "Раздел предназначен для просмотра заметок и связей из "
            "Obsidian-хранилища. Прямой доступ к файлам хранилища через "
            "веб-интерфейс не предоставляется; пока раздел пуст."
        ),
    ),
]

SECTIONS_BY_KEY = {s.key: s for s in SECTIONS}
NAV_SECTIONS = SECTIONS  # same order is used for both sidebar and bottom nav
