import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from quaternionspace import convert as cv
from quaternionspace.cli import app

FIXTURES = Path(__file__).parent / "fixtures"
runner = CliRunner()


@pytest.fixture
def site(tmp_path):
    shutil.copytree(FIXTURES, tmp_path / "site")
    return tmp_path / "site"


def test_convert_runs_and_reports(site):
    r = runner.invoke(app, ["convert", "-f", str(site / "zensical.toml"), "--images", "remote"])
    assert r.exit_code == 0, r.output
    assert "wrote 3 posts, 1 drafts, 1 pages" in r.output
    assert (site / "docs/projects/posts/cesar-and-ruben.md").exists()


def test_xml_and_project_prefix_flags(site):
    r = runner.invoke(app, ["convert", "-f", str(site / "zensical.toml"), "--images", "remote",
                            "--xml", str(site / "export.xml"), "--project-prefix", "/blog/"])
    assert r.exit_code == 0, r.output
    assert "wrote 1 posts, 0 drafts, 1 pages" in r.output  # only /blog/ items become posts


def test_image_host_flag_replaces_hosts(site, monkeypatch):
    calls = []
    monkeypatch.setattr(cv, "download_images", lambda items, dest: calls.append(list(items)) or (0, 0, []))
    r = runner.invoke(app, ["convert", "-f", str(site / "zensical.toml"), "--image-host", "other.example",
                                "--image-host", "more.example"])
    assert r.exit_code == 0, r.output
    assert calls == []  # the Squarespace host was replaced, so no images to localise
    assert "https://images.squarespace-cdn.com/" in (site / "docs/about.md").read_text(encoding="utf-8")


def test_bad_images_value_is_rejected(site):
    r = runner.invoke(app, ["convert", "-f", str(site / "zensical.toml"), "--images", "both"])
    assert r.exit_code == 2


def test_missing_config_is_rejected(tmp_path):
    r = runner.invoke(app, ["convert", "-f", str(tmp_path / "missing.toml")])
    assert r.exit_code == 2


def test_config_error_exits_1(tmp_path):
    (tmp_path / "zensical.toml").write_text('[quaternionspace]\nxml = "x"\nxlm = 1\n', encoding="utf-8")
    r = runner.invoke(app, ["convert", "-f", str(tmp_path / "zensical.toml")])
    assert r.exit_code == 1
    assert "error: unknown [quaternionspace] key(s): xlm" in r.output


def test_failed_image_exits_1(site, monkeypatch):
    monkeypatch.setattr(cv, "download_images",
                        lambda items, dest: (0, 0, ["https://cdn.example/a.jpg: boom"]))
    r = runner.invoke(app, ["convert", "-f", str(site / "zensical.toml")])
    assert r.exit_code == 1
    assert "FAIL https://cdn.example/a.jpg: boom" in r.output
