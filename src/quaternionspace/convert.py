"""Convert a WordPress / Squarespace WXR export into Zensical Markdown pages."""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from markdownify import markdownify as md

from .config import SiteConfig, load_config
from .images import download_images

NS = {
    "wp": "http://wordpress.org/export/1.2/",
    "content": "http://purl.org/rss/1.0/modules/content/",
}


class ImageRegistry:
    """Maps image URLs (query string dropped) to unique local filenames."""

    def __init__(self, hosts: tuple[str, ...]) -> None:
        alt = "|".join(re.escape(h) for h in hosts)
        self.pattern = re.compile(rf"https?://(?:{alt})[^\s\"')]+")
        self.files: dict[str, str] = {}  # url -> filename
        self._used: dict[str, str] = {}  # filename -> url

    def name(self, match: str) -> str:
        url = match.split("?")[0]
        if url not in self.files:
            name = urllib.parse.unquote(os.path.basename(url))
            name = re.sub(r"[^A-Za-z0-9._-]", "_", name) or "image"
            if name in self._used:  # same name, different URL: add a stable suffix
                stem, ext = os.path.splitext(name)
                name = f"{stem}-{hashlib.sha1(url.encode()).hexdigest()[:6]}{ext}"
            self._used[name] = url
            self.files[url] = name
        return self.files[url]


def embed(iframe: str) -> str:
    """Turn an <iframe> into a Markdown embed/link."""
    m = re.search(r'src="([^"]+)"', iframe)
    if not m:
        return ""
    src = html.unescape(m.group(1))  # attribute text may hold &amp;
    if src.startswith("//"):
        src = "https:" + src
    title_m = re.search(r'title="([^"]*)"', iframe)
    title = html.unescape(title_m.group(1)) if title_m else ""

    # embedly wrapper: real target is the `url` query param.
    if "embedly" in src:
        q = urllib.parse.urlparse(src).query
        params = urllib.parse.parse_qs(q)
        src = params.get("url", params.get("src", [src]))[0]

    yt = re.search(r"(?:youtube\.com|youtu\.be).*?[?&/](?:v=|embed/|watch\?v=)?([\w-]{11})", src)
    is_playlist = "list=" in src and "watch?v=" not in src and "/embed/" not in src
    if "youtube" in src and yt and not is_playlist:
        vid = yt.group(1)
        return (f'<div class="video"><iframe src="https://www.youtube.com/embed/{vid}"'
                f' frameborder="0" allowfullscreen></iframe></div>')
    vim = re.search(r"vimeo\.com/(?:video/)?(\d+)", src)
    if vim:
        return (f'<div class="video"><iframe src="https://player.vimeo.com/video/{vim.group(1)}"'
                f' frameborder="0" allowfullscreen></iframe></div>')
    label = title or ("YouTube playlist" if is_playlist else "Open media")
    if "youtube" in src:
        label = title if title and title != "YouTube embed" else "▶ Watch on YouTube"
    elif "soundcloud" in src:
        label = "♪ Listen on SoundCloud"
    return f"[{label}]({src})"


def preprocess(content: str) -> tuple[str, list[str]]:
    """Swap iframes for placeholders and strip [caption] shortcodes.

    markdownify would drop the embed HTML, so embeds go back in after conversion.
    """
    embeds: list[str] = []

    def hold(m: re.Match) -> str:
        embeds.append(embed(m.group(0)))
        return f"<p>QSPACEEMBED{len(embeds) - 1}END</p>"

    content = re.sub(r"<iframe\b.*?</iframe>", hold, content, flags=re.DOTALL)
    content = re.sub(r"\[caption[^\]]*\]", "", content)
    content = content.replace("[/caption]", "")
    return content, embeds


def to_markdown(content: str, images: ImageRegistry | None = None, assets: str = "assets") -> str:
    """HTML body -> Markdown. With ``images``, CDN image URLs become ``<assets>/<file>`` links."""
    html_in, embeds = preprocess(content)
    body = md(html_in, heading_style="ATX", bullets="-", strip=["style"])
    if images is not None:
        body = images.pattern.sub(lambda m: f"{assets}/{images.name(m.group(0))}", body)
    for i, e in enumerate(embeds):
        body = body.replace(f"QSPACEEMBED{i}END", e)
    return re.sub(r"\n{3,}", "\n\n", body).strip()


def frontmatter(title: str, date: str = "", tags: list[str] | None = None, draft: bool = False) -> str:
    lines = ["---", f"title: {json.dumps(title, ensure_ascii=False)}"]  # JSON strings are valid YAML
    if date:
        lines.append(f"date: {date[:10]}")
    if tags:
        lines.append("tags:")
        lines += [f"  - {t}" for t in tags]
    if draft:
        lines.append("draft: true")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


@dataclass
class ConvertResult:
    posts: int = 0  # published project posts written
    drafts: int = 0  # project posts written with draft: true
    pages: int = 0
    images_ok: int = 0
    images_skipped: int = 0
    image_errors: list[str] = field(default_factory=list)  # "url: reason"


def convert_site(config_path: str | Path, **overrides: object) -> ConvertResult:
    """Read the config and its XML export, write the Markdown, and download images (local mode)."""
    return convert_export(load_config(config_path, **overrides))


def convert_export(cfg: SiteConfig) -> ConvertResult:
    tree = ET.parse(cfg.xml)
    images = ImageRegistry(cfg.image_hosts) if cfg.images == "local" else None
    assets_dir = cfg.docs_dir / "assets"
    res = ConvertResult()

    for it in tree.getroot().iter("item"):
        pt = it.findtext("wp:post_type", "", NS)
        name = it.findtext("wp:post_name", "", NS)
        link = it.findtext("link", "") or ""
        status = it.findtext("wp:status", "", NS)
        title = html.unescape(it.findtext("title", "") or "")
        content = it.findtext("content:encoded", "", NS) or ""
        date = it.findtext("wp:post_date", "", NS) or ""

        if pt == "post" and link.startswith(cfg.project_prefix):
            slug = PurePosixPath(name).name
            slug = cfg.slug_overrides.get(slug, slug)
            draft = status != cfg.published_status
            out = cfg.docs_dir / cfg.post_dir / f"{slug}.md"
            fm = frontmatter(title, date, cfg.tags.get(slug), draft)
        elif pt == "page" and name in cfg.pages and status == cfg.published_status:
            draft = False  # Zensical has no per-page draft for docs pages, so unpublished pages are skipped
            out = cfg.docs_dir / cfg.pages[name]
            fm = frontmatter(title)
        else:
            continue  # placeholders, home, attachments, unpublished pages

        # Relative from the page's own folder: Zensical rewrites links from the source path.
        rel = Path(os.path.relpath(assets_dir, out.parent)).as_posix()
        body = to_markdown(content, images, rel)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(fm + body + "\n", encoding="utf-8")
        if pt == "page":
            res.pages += 1
        elif draft:
            res.drafts += 1
        else:
            res.posts += 1

    if images is not None and images.files:
        res.images_ok, res.images_skipped, res.image_errors = download_images(
            images.files.items(), assets_dir)
    return res
