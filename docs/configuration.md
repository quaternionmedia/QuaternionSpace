# Configuration

QuaternionSpace reads the `zensical.toml` file that Zensical builds from. It uses one `[quaternionspace]` table for its own settings, and two Zensical settings for the output folders.

## `[quaternionspace]` keys

| Key | Type | Default | Meaning |
|---|---|---|---|
| `xml` | string | none (required unless `--xml`) | Path to the WXR export. A relative path resolves from the folder of the config file. |
| `images` | `"local"` or `"remote"` | `"local"` | `local` downloads each image into `docs/assets/` and links to it. `remote` keeps the original CDN URLs and downloads nothing. |
| `image_hosts` | list of strings | `["images.squarespace-cdn.com"]` | Image hosts to download. Used only in `local` mode. |
| `project_prefix` | string | `"/projects/"` | A post whose link starts with this prefix is a project post. |
| `published_status` | string | `"publish"` | The `wp:status` of a published item. Project posts with any other status are written with `draft: true`. Pages with any other status are not written. |
| `slug_overrides` | table | `{}` | Replaces a project's slug. The key is the last part of its WordPress name; the value is the new slug. |
| `pages` | table | `{}` | Maps a WordPress page name to a file under `docs/`, for example `about = "about.md"`. Only listed pages are written. |
| `[quaternionspace.tags]` | table of lists | `{}` | Tags for each project slug, after any slug override. Written as `tags:` front matter. |

Example:

```toml
[quaternionspace]
xml = "export.xml"
images = "local"
image_hosts = ["images.squarespace-cdn.com"]
project_prefix = "/projects/"
published_status = "publish"
slug_overrides = { s2ig08ghl4kngswm15jdotj0z8eq9g = "dellarte-productions" }
pages = { about = "about.md" }

[quaternionspace.tags]
dellarte-productions = ["theater"]
```

## Zensical settings the converter reads

These live in Zensical's own tables, not in `[quaternionspace]`.

| Setting | Default | Meaning |
|---|---|---|
| `[project].docs_dir` | `"docs"` | Output root. Pages and `assets/` are written under it. |
| `[project.plugins.blog].blog_dir` | `"blog"` | Blog folder name. |
| `[project.plugins.blog].post_dir` | `"{blog}/posts"` | Post folder under `docs_dir`. `{blog}` is replaced by `blog_dir`. |

With `blog_dir = "projects"`, project posts go to `docs/projects/posts/<slug>.md`.

## Precedence

Command-line flags override the `[quaternionspace]` table, which overrides the defaults above. A flag that is not given leaves the TOML value in place.

## Command-line flags

`qspace convert` takes these flags. Each one overrides the matching key.

| Flag | Overrides | Meaning |
|---|---|---|
| `-f`, `--config PATH` | (none) | Zensical config file to read. Default: `zensical.toml`. |
| `--xml PATH` | `xml` | WXR export. Used as given, relative to the current directory. |
| `--images {local,remote}` | `images` | Download and link images, or keep CDN URLs. |
| `--image-host HOST` | `image_hosts` | Image host to download. Repeat for several. Replaces the whole list. |
| `--project-prefix TEXT` | `project_prefix` | Link prefix that marks project posts. |
| `--published-status TEXT` | `published_status` | `wp:status` that counts as published. |
| `--help` | (none) | Show usage and exit. |

Flags for `slug_overrides`, `pages`, and tags are not provided; set them in the TOML file. `docs_dir` and `blog_dir` are also TOML-only, so the converter and `zensical build` always agree on the output folder.

## Output and exit codes

On success, `qspace convert` prints one line with the counts:

```text
wrote 24 posts, 0 drafts, 0 pages
images: ok=22, skipped=0, failed=0
```

- `ok` images were downloaded; `skipped` images already existed in `docs/assets/`.
- Each failed download prints a `FAIL <url>: <reason>` line on stderr.
- Exit code `0`: success.
- Exit code `1`: a config or XML error (printed as `error: ...`), or at least one image download failed.
- Exit code `2`: a bad flag value, such as `--images both`, or a `--config` or `--xml` file that does not exist.

If an image download fails, the Markdown still links to its file under `assets/`. The file is missing until you convert again.
