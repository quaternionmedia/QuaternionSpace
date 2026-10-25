"""Full run on the local qm export. Skipped when the XML is absent (it is not committed)."""
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from quaternionspace import convert as cv
from quaternionspace.convert import convert_site

ROOT = Path(__file__).resolve().parent.parent
QM_XML = ROOT / "qm-projects-10-25-2026.xml"
NS = {"wp": "http://wordpress.org/export/1.2/", "content": "http://purl.org/rss/1.0/modules/content/"}

pytestmark = pytest.mark.skipif(not QM_XML.exists(), reason="qm export not present")


def test_qm_projects_convert(tmp_path, monkeypatch):
    shutil.copy(ROOT / "examples/qm/zensical.toml", tmp_path / "zensical.toml")
    downloads = []

    def fake(items, dest):  # record instead of fetching
        downloads.append(list(items))
        return len(downloads[-1]), 0, []

    monkeypatch.setattr(cv, "download_images", fake)
    res = convert_site(tmp_path / "zensical.toml", xml=QM_XML)

    # Independent count from the raw XML: published /projects/ posts and unique CDN bases.
    root = ET.parse(QM_XML).getroot()
    expected_urls = set()
    expected_posts = 0
    for it in root.iter("item"):
        if (it.findtext("wp:post_type", "", NS) == "post"
                and (it.findtext("link", "") or "").startswith("/projects/")
                and it.findtext("wp:status", "", NS) == "publish"):
            expected_posts += 1
            content = it.findtext("content:encoded", "", NS) or ""
            expected_urls |= {u.split("?")[0] for u in
                              re.findall(r"https?://images\.squarespace-cdn\.com[^\s\"')]+", content)}

    out = sorted((tmp_path / "docs/projects/posts").glob("*.md"))
    assert len(out) == expected_posts == res.posts == 24
    assert res.drafts == 0 and res.pages == 0
    assert "/" not in "".join(p.name for p in out)
    assert len(downloads) == 1 and len(downloads[0]) == len(expected_urls)
