# JustinPease.com

Personal blog, served as static files from the repo root by Cloudflare (no
build step at deploy time).

## Layout

- `content/posts/YYYY-MM-DD-slug.md` — posts (Markdown with YAML front matter:
  `title`, `post-image`, optional `description`, `tags`, `published: false`)
- `content/site.yml`, `content/projects.yml` — site settings, nav, projects
- `templates/` — Jinja templates for every generated page and feed
- `styles/`, `assets/` — hand-maintained CSS, fonts, images, and search JS
- `scripts/build.py` — renders the above into the repo root
  (`index.html`, `blog.html`, `projects.html`, `404.html`,
  `YYYY/MM/DD/slug.html`, `feed.xml`, `sitemap.xml`, `search.json`,
  `llms.txt`). Generated files are committed; edit the sources, not them.

## Workflow

Requires [uv](https://docs.astral.sh/uv/) and [just](https://just.systems/).

```sh
just build     # regenerate the site after editing content/ or templates/
just preview   # Cloudflare-accurate local preview (wrangler dev)
just check     # output is current, links resolve, sitemap is consistent
```

Post URLs are `/YYYY/MM/DD/slug`, the same scheme the previous Jekyll site
used, so existing links keep working without redirects.

All content, including posts and photos, is Copyright &copy; Justin Pease.
All rights reserved.
