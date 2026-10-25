# QuaternionSpace

QuaternionSpace converts a WordPress or Squarespace WXR export into Markdown for a Zensical site. Each project post becomes one Markdown file, with its images downloaded next to the site and its YouTube or Vimeo players kept as embeds.

## Install

QuaternionSpace is not on PyPI yet. Clone the repository and sync its environment:

```bash
git clone https://github.com/quaternionmedia/QuaternionSpace
cd QuaternionSpace
uv sync
```

The examples below run `qspace`. Either activate the environment (`source .venv/bin/activate`) or prefix each command with `uv run --project /path/to/QuaternionSpace`.

## Quick start

1. Export your site as WXR XML from WordPress or Squarespace.
2. Put the converter settings in your site's `zensical.toml`:

    ```toml
    [project]
    site_name = "My Projects"

    [project.plugins.blog]
    blog_dir = "projects"

    [quaternionspace]
    xml = "export.xml"
    ```

3. Convert the export:

    ```bash
    qspace convert -f zensical.toml
    ```

4. Build the site, or preview it while you edit:

    ```bash
    zensical build
    zensical serve
    ```

The [configuration reference](configuration.md) lists every setting, and the [cookbook](cookbook.md) has recipes for common jobs.
