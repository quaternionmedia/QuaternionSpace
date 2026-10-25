# Cookbook

Each recipe starts from the Quick start site. The commands assume you are in the folder that holds its `zensical.toml`. The real example for these recipes is [`examples/qm`](https://github.com/quaternionmedia/QuaternionSpace/tree/main/examples/qm).

## Convert an export into a blog

Project posts become blog posts. Set the blog folder in Zensical's blog plugin, then convert:

```toml
[project.plugins.blog]
blog_dir = "projects"

[quaternionspace]
xml = "export.xml"
```

```bash
qspace convert -f zensical.toml
zensical build
```

Posts land in `docs/projects/posts/<slug>.md`. The slug is the last part of the WordPress path, so `/projects/2018/7/24/cesar-and-ruben` becomes `cesar-and-ruben`.

## Keep images on their CDN

Use `remote` to keep the original image URLs and skip the download. This is quicker, and it suits a site that serves its images from a public CDN.

```bash
qspace convert -f zensical.toml --images remote
```

To set it once, write `images = "remote"` in the `[quaternionspace]` table.

## Download images from a different host

`image_hosts` lists the hosts to download. Replace the list with `--image-host`, once per host:

```bash
qspace convert -f zensical.toml --image-host images.example.com --image-host cdn.example.net
```

Images from hosts not in the list stay as they are.

## Map WordPress pages to docs pages

Pages are written only when they are listed in `pages` and published:

```toml
[quaternionspace]
pages = { about = "about.md", contact = "contact/index.md" }
```

The key is the WordPress page name, and the value is the file under `docs/`. The folder is created if it does not exist.

## Fix a slug

A WordPress slug can be a long hash. `slug_overrides` renames the file and its URL:

```toml
[quaternionspace]
slug_overrides = { s2ig08ghl4kngswm15jdotj0z8eq9g = "dellarte-productions" }
```

The key is the last part of the post's WordPress name. Any tags you give that post must use the new slug.

## Add tags

Tags go in their own table, keyed by slug (after any override):

```toml
[quaternionspace.tags]
cesar-and-ruben = ["music"]
dellarte-productions = ["theater", "lighting"]
```

Each project post gets a `tags:` list in its front matter. Posts without an entry get no tags.

## Drafts

A project post whose `wp:status` is not `published_status` is written with `draft: true`. With the blog plugin, Zensical leaves drafts out of `zensical build`, and `zensical serve` still shows them.

```bash
zensical build                 # drafts are not in the site
zensical serve                 # drafts are shown
```

To treat another status as published, pass it with the flag:

```bash
qspace convert -f zensical.toml --published-status live
```

## Preview while you edit

```bash
zensical serve
```

Open the address it prints. To see the result of a new conversion, run `qspace convert` again, then reload the page.

## Use the library from Python

`convert_site` takes the same settings as the flags and returns the counts:

```python
from quaternionspace import convert_site

result = convert_site("zensical.toml", images="remote")
print(result.posts, result.drafts, result.pages)
print(result.images_ok, result.images_skipped, result.image_errors)
```

Keyword arguments use the key names from the [configuration reference](configuration.md): `xml`, `images`, `image_hosts`, `project_prefix`, and `published_status`. `None` leaves the TOML value in place. A bad config raises `quaternionspace.ConfigError`.
