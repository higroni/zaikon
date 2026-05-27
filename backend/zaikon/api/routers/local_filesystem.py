"""Local filesystem browsing endpoints for the internal desktop UI."""

from pathlib import Path
import string

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field


router = APIRouter(prefix="/local-filesystem", tags=["local-filesystem"])


class LocalFilesystemEntry(BaseModel):
    name: str
    path: str
    is_dir: bool
    size_bytes: int | None = None


class LocalFilesystemBrowseResponse(BaseModel):
    current_path: str
    parent_path: str | None = None
    entries: list[LocalFilesystemEntry] = Field(default_factory=list)


@router.get("/browse", response_model=LocalFilesystemBrowseResponse)
def browse_local_filesystem(
    path: str | None = Query(default=None),
    mode: str = Query(default="folder", pattern="^(folder|file)$"),
) -> LocalFilesystemBrowseResponse:
    current = _default_path() if not path else Path(path).expanduser()
    current = current.resolve()
    if current.is_file():
        current = current.parent

    entries = []
    for child in _safe_iterdir(current):
        if not child.is_dir() and mode == "folder":
            continue
        entries.append(
            LocalFilesystemEntry(
                name=child.name,
                path=str(child),
                is_dir=child.is_dir(),
                size_bytes=None if child.is_dir() else _safe_size(child),
            )
        )

    entries.sort(key=lambda entry: (not entry.is_dir, entry.name.lower()))
    parent = current.parent if current.parent != current else None
    return LocalFilesystemBrowseResponse(
        current_path=str(current),
        parent_path=str(parent) if parent else None,
        entries=entries,
    )


@router.get("/roots", response_model=LocalFilesystemBrowseResponse)
def list_local_roots() -> LocalFilesystemBrowseResponse:
    entries = []
    for letter in string.ascii_uppercase:
        drive = Path(f"{letter}:/")
        if drive.exists():
            entries.append(
                LocalFilesystemEntry(name=f"{letter}:\\", path=str(drive), is_dir=True)
            )
    if not entries:
        entries.append(LocalFilesystemEntry(name="/", path="/", is_dir=True))
    home = Path.home()
    if home.exists():
        entries.insert(0, LocalFilesystemEntry(name="Home", path=str(home), is_dir=True))
    return LocalFilesystemBrowseResponse(current_path="", entries=entries)


def _default_path() -> Path:
    return Path.home() if Path.home().exists() else Path.cwd()


def _safe_iterdir(path: Path):
    try:
        return list(path.iterdir())
    except (FileNotFoundError, NotADirectoryError, PermissionError, OSError):
        return []


def _safe_size(path: Path) -> int | None:
    try:
        return path.stat().st_size
    except OSError:
        return None
