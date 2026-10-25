# About

QuaternionSpace is made by [Quaternion Media, LLC](https://www.quaternion.media). It was written to move the Quaternion Media site from WordPress and Squarespace to a Zensical site, and it is shared in case another site needs the same move.

## What it does

- Reads a WXR export (WordPress eXtended RSS), the format WordPress and Squarespace both write.
- Writes project posts and listed pages as Markdown with front matter (title, date, tags, and `draft` where needed).
- Downloads the images those posts use, or keeps their original URLs.
- Turns YouTube and Vimeo videos into embeds. Other media, such as playlists and SoundCloud, become links.

## Scope and limits

- Only WXR input. Other export formats are not read.
- Only `post` and `page` items are converted. Attachments, menus, and custom post types are skipped. Comments are not converted.
- Images are found in the HTML of converted posts and pages, and only the hosts in `image_hosts` are downloaded.
- An image that fails to download is still linked, so the page shows a broken image until you convert again. The command exits with code 1 and prints the failed URLs.
- Project posts are matched by link prefix (`project_prefix`). A site with a different structure needs that prefix set.
- The test suite uses short excerpts of the real export. The full export is not in the repository.

## Origin

The first version was two scripts for one site, `scripts/convert.py` and `scripts/download_images.py`. They hard-coded that site's page names, slugs, and tags. The package keeps the same conversion but reads those choices from a config file, so the same tool can convert another site.
