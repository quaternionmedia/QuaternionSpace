# QuaternionSpace

A WordPress / Squarespace XML conversion tool for Zensical. It turns a WXR export into Markdown pages, downloads their images, and leaves you with a site that `zensical build` can render.

## Quick start

```bash
uv sync
```

Add a `[quaternionspace]` table to your site's `zensical.toml`, next to its `[project]` table:

```toml
[quaternionspace]
xml = "export.xml"
```

Then convert and build:

```bash
uv run qspace convert -f zensical.toml
uv run zensical build
```

The full documentation is in [`docs/`](docs/index.md): [configuration](docs/configuration.md), [cookbook](docs/cookbook.md), and [about](docs/about.md). A complete example is in [`examples/qm/`](examples/qm/zensical.toml); it needs its own export, which is not in this repository.

## Development

```bash
uv run pytest
uv run ruff check
```
