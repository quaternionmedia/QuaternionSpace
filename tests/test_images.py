import io
import urllib.error

from quaternionspace import images


def test_download_writes_and_skips_existing(tmp_path, monkeypatch):
    monkeypatch.setattr(images.urllib.request, "urlopen", lambda url, timeout: io.BytesIO(b"pixels"))
    (tmp_path / "old.jpg").write_bytes(b"kept")
    ok, skipped, errors = images.download_images(
        [("https://cdn.example/a.jpg", "a.jpg"), ("https://cdn.example/old.jpg", "old.jpg")], tmp_path)
    assert (ok, skipped, errors) == (1, 1, [])
    assert (tmp_path / "a.jpg").read_bytes() == b"pixels"
    assert (tmp_path / "old.jpg").read_bytes() == b"kept"


def test_timeout_is_passed(tmp_path, monkeypatch):
    seen = {}

    def fake(url, timeout):
        seen["timeout"] = timeout
        return io.BytesIO(b"x")

    monkeypatch.setattr(images.urllib.request, "urlopen", fake)
    images.download_images([("https://cdn.example/a.jpg", "a.jpg")], tmp_path)
    assert seen["timeout"] == images.TIMEOUT


def test_failed_transfer_leaves_no_file(tmp_path, monkeypatch):
    def fake(url, timeout):
        raise urllib.error.URLError("boom")

    monkeypatch.setattr(images.urllib.request, "urlopen", fake)
    ok, skipped, errors = images.download_images([("https://cdn.example/a.jpg", "a.jpg")], tmp_path)
    assert (ok, skipped) == (0, 0)
    assert errors == ["https://cdn.example/a.jpg: <urlopen error boom>"]
    assert list(tmp_path.iterdir()) == []


def test_interrupted_transfer_leaves_no_part_file(tmp_path, monkeypatch):
    class Cut(io.BytesIO):
        def read(self, *args):
            raise ConnectionResetError("cut")

    monkeypatch.setattr(images.urllib.request, "urlopen", lambda url, timeout: Cut(b"half"))
    ok, _, errors = images.download_images([("https://cdn.example/a.jpg", "a.jpg")], tmp_path)
    assert ok == 0 and len(errors) == 1
    assert list(tmp_path.iterdir()) == []  # neither a.jpg nor a.jpg.part, so the next run retries
