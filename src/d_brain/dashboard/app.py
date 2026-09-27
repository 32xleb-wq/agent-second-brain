"""FastAPI app for the Second Brain Dashboard.

Reads live from the configured Obsidian vault on every request (see
vault_reader.py) — nothing here caches or hardcodes the user's notes.
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from d_brain.dashboard import vault_reader as vr
from d_brain.dashboard.sections import NAV_SECTIONS, SECTIONS_BY_KEY

_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(_DIR / "templates"))


def create_app() -> FastAPI:
    app = FastAPI(title="Second Brain Dashboard", docs_url=None, redoc_url=None)

    # Only this dashboard's own static assets are served — never the vault,
    # .env, or import directories.
    app.mount("/static", StaticFiles(directory=str(_DIR / "static")), name="static")

    def render_empty_section(request: Request, key: str) -> HTMLResponse:
        section = SECTIONS_BY_KEY[key]
        return templates.TemplateResponse(
            request,
            "section.html",
            {"nav": NAV_SECTIONS, "active": key, "section": section},
        )

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request) -> HTMLResponse:
        summary = vr.get_home_summary()
        return templates.TemplateResponse(
            request,
            "home.html",
            {
                "nav": NAV_SECTIONS,
                "active": "home",
                "cards": NAV_SECTIONS[1:],
                "summary": summary,
            },
        )

    @app.get("/tasks", response_class=HTMLResponse)
    def tasks(request: Request) -> HTMLResponse:
        data = vr.get_tasks()
        return templates.TemplateResponse(
            request,
            "tasks.html",
            {"nav": NAV_SECTIONS, "active": "tasks", **data},
        )

    @app.get("/defi", response_class=HTMLResponse)
    def defi(request: Request) -> HTMLResponse:
        data = vr.get_defi()
        return templates.TemplateResponse(
            request,
            "defi.html",
            {"nav": NAV_SECTIONS, "active": "defi", **data},
        )

    @app.get("/content", response_class=HTMLResponse)
    def content(request: Request) -> HTMLResponse:
        data = vr.get_content()
        return templates.TemplateResponse(
            request,
            "content.html",
            {"nav": NAV_SECTIONS, "active": "content", **data},
        )

    @app.get("/health", response_class=HTMLResponse)
    def health(request: Request) -> HTMLResponse:
        return render_empty_section(request, "health")

    @app.get("/obsidian", response_class=HTMLResponse)
    def obsidian(request: Request) -> HTMLResponse:
        data = vr.get_obsidian_overview()
        return templates.TemplateResponse(
            request,
            "obsidian.html",
            {"nav": NAV_SECTIONS, "active": "obsidian", **data},
        )

    @app.get("/obsidian/note", response_class=HTMLResponse)
    def note(request: Request, path: str, back: str = "/obsidian") -> HTMLResponse:
        try:
            note_data = vr.read_note(path)
            error = None
        except vr.VaultPathError:
            return PlainTextResponse("Заметка не найдена или недоступна.", status_code=404)
        except OSError as exc:
            note_data = None
            error = str(exc)
        return templates.TemplateResponse(
            request,
            "note.html",
            {
                "nav": NAV_SECTIONS,
                "active": "obsidian",
                "rel_path": path,
                "back": back,
                "note": note_data,
                "error": error,
            },
        )

    return app


app = create_app()
