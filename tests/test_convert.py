import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from quaternionspace import convert as cv
from quaternionspace.convert import ImageRegistry, convert_site, embed, to_markdown

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def site(tmp_path):
    shutil.copytree(FIXTURES, tmp_path / "site")
    return tmp_path / "site"


@pytest.fixture
def fake_download(monkeypatch):
    """Record what would be downloaded; no network."""
    calls = []

    def fake(items, dest):
        items = list(items)
        calls.append((items, dest))
        return len(items), 0, []

    monkeypatch.setattr(cv, "download_images", fake)
    return calls


def posts(site):
    return sorted(p.name for p in (site / "docs/projects/posts").iterdir())


def test_slashed_post_names_become_flat_slugs(site):
    convert_site(site / "zensical.toml", images="remote")
    assert posts(site) == ["1776-projection-designs.md", "cesar-and-ruben.md",
                           "dellarte-productions.md", "st-albans-country-day-school.md"]


def test_counts_and_draft_front_matter(site):
    res = convert_site(site / "zensical.toml", images="remote")
    assert (res.posts, res.drafts, res.pages) == (3, 1, 1)
    assert "draft: true" in (site / "docs/projects/posts/1776-projection-designs.md").read_text()
    assert "draft" not in (site / "docs/projects/posts/cesar-and-ruben.md").read_text()


def test_unpublished_pages_are_not_written(site):
    convert_site(site / "zensical.toml", images="remote")
    assert (site / "docs/about.md").exists()
    assert not (site / "docs/contact.md").exists()


def test_title_is_json_quoted(site):
    convert_site(site / "zensical.toml", images="remote")
    text = (site / "docs/projects/posts/st-albans-country-day-school.md").read_text(encoding="utf-8")
    line = next(ln for ln in text.splitlines() if ln.startswith("title: "))
    assert json.loads(line[len("title: "):]) == 'St. Alban\'s "Country Day" School'


def test_slug_override_and_tags(site):
    convert_site(site / "zensical.toml", images="remote")
    text = (site / "docs/projects/posts/dellarte-productions.md").read_text(encoding="utf-8")
    assert "tags:\n  - theater" in text
    assert not (site / "docs/projects/posts/s2ig08ghl4kngswm15jdotj0z8eq9g.md").exists()


def test_remote_keeps_cdn_urls_and_downloads_nothing(site, fake_download):
    convert_site(site / "zensical.toml", images="remote")
    text = (site / "docs/projects/posts/cesar-and-ruben.md").read_text(encoding="utf-8")
    assert "https://images.squarespace-cdn.com/" in text
    assert fake_download == []
    assert not (site / "docs/assets").exists()


def test_local_images_are_relative_to_each_page(site, fake_download):
    convert_site(site / "zensical.toml")
    post = (site / "docs/projects/posts/cesar-and-ruben.md").read_text(encoding="utf-8")
    assert "../../assets/c_r-poster.jpg" in post
    assert "](../../assets/c_r-poster-" in post  # the second, different CDN id gets a suffix
    about = (site / "docs/about.md").read_text(encoding="utf-8")
    assert "](assets/african_dream_poster.jpg)" in about
    names = sorted(name for _, name in fake_download[0][0])
    assert names[0] == "african_dream_poster.jpg" and names[2] == "c_r-poster.jpg"
    assert names[1].startswith("c_r-poster-")


def test_youtube_embed_survives_conversion(site):
    convert_site(site / "zensical.toml", images="remote")
    text = (site / "docs/projects/posts/cesar-and-ruben.md").read_text(encoding="utf-8")
    assert '<iframe src="https://www.youtube.com/embed/5jf_kaAtWB4"' in text


def test_collision_names_do_not_depend_on_hash_seed():
    code = ("from quaternionspace.convert import ImageRegistry as R; r = R(('h.example',));"
            "print(r.name('https://h.example/a/c%26r-poster.jpg?x'), r.name('https://h.example/b/c%26r-poster.jpg'))")
    outs = {subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True,
                           env={**os.environ, "PYTHONHASHSEED": seed}).stdout
            for seed in ("1", "2")}
    assert len(outs) == 1
    first, second = outs.pop().split()
    assert first == "c_r-poster.jpg" and second.startswith("c_r-poster-") and second.endswith(".jpg")


def test_query_string_is_dropped_from_image_name():
    reg = ImageRegistry(("h.example",))
    assert reg.name("https://h.example/a/x.jpg?format=original") == reg.name("https://h.example/a/x.jpg") == "x.jpg"


@pytest.mark.parametrize("iframe, expected", [
    ('<iframe src="//www.youtube.com/embed/5jf_kaAtWB4?wmode=opaque" frameborder="0"></iframe>',
     '<div class="video"><iframe src="https://www.youtube.com/embed/5jf_kaAtWB4" frameborder="0" allowfullscreen></iframe></div>'),
    ('<iframe src="https://player.vimeo.com/video/12345?h=abc"></iframe>',
     '<div class="video"><iframe src="https://player.vimeo.com/video/12345" frameborder="0" allowfullscreen></iframe></div>'),
    ('<iframe src="https://w.soundcloud.com/player/?url=x" title="Track"></iframe>',
     "[♪ Listen on SoundCloud](https://w.soundcloud.com/player/?url=x)"),
    ('<iframe src="https://www.youtube.com/playlist?list=PL123"></iframe>',
     "[▶ Watch on YouTube](https://www.youtube.com/playlist?list=PL123)"),
])
def test_embed(iframe, expected):
    assert embed(iframe) == expected


def test_to_markdown_keeps_embed_and_localises_image():
    reg = ImageRegistry(("img.example",))
    body = to_markdown('<p>Hi</p><img src="https://img.example/a.png"><iframe src="https://vimeo.com/7"></iframe>',
                       reg, "../assets")
    assert "Hi" in body and "![](../assets/a.png)" in body
    assert 'player.vimeo.com/video/7' in body
