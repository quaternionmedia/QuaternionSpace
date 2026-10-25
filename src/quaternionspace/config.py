"""Read a Zensical config file: its docs/blog settings and the [quaternionspace] table."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

IMAGE_MODES = ("local", "remote")
DEFAULT_IMAGE_HOSTS = ["images.squarespace-cdn.com"]
KEYS = ("xml", "images", "image_hosts", "project_prefix", "published_status",
        "slug_overrides", "pages", "tags")


class ConfigError(Exception):
    """A config file or option that cannot be used. The message is shown to the user."""


@dataclass(frozen=True)
class SiteConfig:
    xml: Path
    docs_dir: Path  # absolute
    post_dir: str  # relative to docs_dir, e.g. "projects/posts"
    images: str
    image_hosts: tuple[str, ...]
    project_prefix: str
    published_status: str
    slug_overrides: dict[str, str] = field(default_factory=dict)
    pages: dict[str, str] = field(default_factory=dict)  # WXR page name -> path under docs_dir
    tags: dict[str, list[str]] = field(default_factory=dict)  # project slug -> tags


def _check(name: str, value: Any, kind: type) -> Any:
    if not isinstance(value, kind):
        raise ConfigError(f"{name} must be a {kind.__name__}, got {value!r}")
    return value


def load_config(path: str | Path, **overrides: Any) -> SiteConfig:
    """Load a Zensical config. Overrides (None ignored) > [quaternionspace] > defaults.

    Relative ``xml`` in the TOML resolves from the config file's folder;
    an ``xml`` override is used as given (relative to the current directory).
    """
    path = Path(path)
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise ConfigError(f"config file not found: {path}") from e
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"{path}: {e}") from e

    project = data.get("project", {})
    blog = project.get("plugins", {}).get("blog", {})
    table = data.get("quaternionspace", {})
    overrides = {k: v for k, v in overrides.items() if v is not None}

    unknown = (set(table) | set(overrides)) - set(KEYS)
    if unknown:
        raise ConfigError(f"unknown [quaternionspace] key(s): {', '.join(sorted(unknown))}")
    settings = {**table, **overrides}

    if "xml" not in settings:
        raise ConfigError(f"no XML export set: add xml to [quaternionspace] in {path} or pass --xml")
    xml = Path(overrides["xml"]) if "xml" in overrides else path.parent / _check("xml", settings["xml"], str)

    images = _check("images", settings.get("images", "local"), str)
    if images not in IMAGE_MODES:
        raise ConfigError(f"images must be one of {', '.join(IMAGE_MODES)}, got {images!r}")
    hosts = settings.get("image_hosts", DEFAULT_IMAGE_HOSTS)
    if not isinstance(hosts, list) or not all(isinstance(h, str) for h in hosts):
        raise ConfigError(f"image_hosts must be a list of strings, got {hosts!r}")
    published = _check("published_status", settings.get("published_status", "publish"), str)
    if not published:
        raise ConfigError("published_status must not be empty")

    blog_dir = _check("blog_dir", blog.get("blog_dir", "blog"), str)
    return SiteConfig(
        xml=xml,
        docs_dir=path.parent / _check("docs_dir", project.get("docs_dir", "docs"), str),
        post_dir=_check("post_dir", blog.get("post_dir", "{blog}/posts"), str).replace("{blog}", blog_dir),
        images=images,
        image_hosts=tuple(hosts),
        project_prefix=_check("project_prefix", settings.get("project_prefix", "/projects/"), str),
        published_status=published,
        slug_overrides=_check("slug_overrides", settings.get("slug_overrides", {}), dict),
        pages=_check("pages", settings.get("pages", {}), dict),
        tags=_check("tags", settings.get("tags", {}), dict),
    )
