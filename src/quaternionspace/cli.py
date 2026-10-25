"""Command line: ``qspace convert``."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from enum import Enum
from pathlib import Path
from typing import Annotated

import typer

from .config import ConfigError
from .convert import convert_site

app = typer.Typer(help="Convert WordPress / Squarespace XML exports into Zensical sites.",
                  no_args_is_help=True)


class ImageMode(str, Enum):
    local = "local"
    remote = "remote"


@app.callback()
def cli() -> None:
    """Convert WordPress / Squarespace XML exports into Zensical sites."""


@app.command()
def convert(
    config: Annotated[Path, typer.Option(
        "--config", "-f", exists=True, dir_okay=False,
        help="Zensical config file with a [quaternionspace] table.")] = Path("zensical.toml"),
    xml: Annotated[Path | None, typer.Option(
        exists=True, dir_okay=False, help="WXR export. Overrides xml in the config.")] = None,
    images: Annotated[ImageMode | None, typer.Option(
        help="local: download images and link them; remote: keep the CDN URLs.")] = None,
    image_host: Annotated[list[str] | None, typer.Option(
        "--image-host", help="Image host to localise. Repeat for several; replaces image_hosts.")] = None,
    project_prefix: Annotated[str | None, typer.Option(
        help="Link prefix that marks project posts.")] = None,
    published_status: Annotated[str | None, typer.Option(
        help="wp:status that is published. Other project posts become drafts.")] = None,
) -> None:
    """Convert the XML export into the Zensical docs, then download its images (local mode)."""
    try:
        res = convert_site(
            config, xml=xml, images=images.value if images else None,
            image_hosts=image_host, project_prefix=project_prefix,
            published_status=published_status)
    except (ConfigError, OSError, ET.ParseError) as e:
        typer.echo(f"error: {e}", err=True)
        raise typer.Exit(1)

    typer.echo(f"wrote {res.posts} posts, {res.drafts} drafts, {res.pages} pages")
    if res.images_ok or res.images_skipped or res.image_errors:
        typer.echo(f"images: ok={res.images_ok}, skipped={res.images_skipped}, "
                   f"failed={len(res.image_errors)}")
    for err in res.image_errors:
        typer.echo(f"FAIL {err}", err=True)
    if res.image_errors:
        raise typer.Exit(1)
