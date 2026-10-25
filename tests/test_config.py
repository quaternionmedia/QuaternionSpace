from pathlib import Path

import pytest

from quaternionspace.config import ConfigError, load_config


def write(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "zensical.toml"
    p.write_text(text, encoding="utf-8")
    return p


def test_defaults(tmp_path):
    c = load_config(write(tmp_path, '[quaternionspace]\nxml = "export.xml"\n'))
    assert c.docs_dir == tmp_path / "docs"
    assert c.post_dir == "blog/posts"
    assert c.xml == tmp_path / "export.xml"
    assert (c.images, c.image_hosts, c.project_prefix, c.published_status) == (
        "local", ("images.squarespace-cdn.com",), "/projects/", "publish")


def test_blog_post_dir_and_docs_dir_come_from_zensical(tmp_path):
    p = write(tmp_path, '[project]\ndocs_dir = "site"\n[project.plugins.blog]\n'
                        'blog_dir = "projects"\npost_dir = "{blog}/articles"\n'
                        '[quaternionspace]\nxml = "x.xml"\n')
    c = load_config(p)
    assert c.docs_dir == tmp_path / "site"
    assert c.post_dir == "projects/articles"


def test_overrides_beat_toml_and_none_is_ignored(tmp_path):
    p = write(tmp_path, '[quaternionspace]\nxml = "x.xml"\nimages = "remote"\n')
    assert load_config(p).images == "remote"
    assert load_config(p, images="local").images == "local"
    assert load_config(p, images=None).images == "remote"


def test_xml_override_is_used_as_given(tmp_path):
    p = write(tmp_path, '[quaternionspace]\nxml = "x.xml"\n')
    assert load_config(p, xml="elsewhere/e.xml").xml == Path("elsewhere/e.xml")


@pytest.mark.parametrize("text, message", [
    ('[quaternionspace]\nxml = "x"\nimages = "both"\n', "images must be one of"),
    ('[quaternionspace]\nimages = "local"\n', "no XML export set"),
    ('[quaternionspace]\nxml = "x"\nxlm = "typo"\n', "unknown"),
    ('[quaternionspace]\nxml = "x"\nimage_hosts = "a.example"\n', "image_hosts must be a list"),
    ('[quaternionspace]\nxml = "x"\npublished_status = ""\n', "must not be empty"),
])
def test_invalid_settings_raise(tmp_path, text, message):
    with pytest.raises(ConfigError, match=message):
        load_config(write(tmp_path, text))


def test_unknown_override_raises(tmp_path):
    with pytest.raises(ConfigError, match="unknown"):
        load_config(write(tmp_path, '[quaternionspace]\nxml = "x"\n'), bogus=1)


def test_missing_and_malformed_files_raise(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "nope.toml")
    with pytest.raises(ConfigError, match="zensical.toml"):
        load_config(write(tmp_path, "[quaternionspace\n"))
