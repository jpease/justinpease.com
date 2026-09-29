# JustinPease.com

Personal blog, served as static files from the repo root by a Cloudflare
Worker (static assets only, no build step at deploy time). Pushing to `main`
deploys; other branches get preview URLs.

## Layout

- `content/posts/YYYY-MM-DD-slug.md` — posts (Markdown with YAML front matter:
  `title`, `post-image`, optional `description`, `tags`, `published: false`)
- `content/site.yml`, `content/projects.yml` — site settings, nav, projects
- `templates/` — Jinja templates for every generated page and feed
- `styles/`, `assets/` — hand-maintained CSS, fonts, images, and search JS
- `scripts/build.py` — renders the above into the repo root
  (`index.html` — the blog listing, `projects.html`, `404.html`,
  `YYYY/MM/DD/slug.html`, `feed.xml`, `sitemap.xml`, `search.json`,
  `llms.txt`). Generated files are committed; edit the sources, not them.
- `wrangler.jsonc` — Worker config: serve the repo root, `/foo` → `foo.html`,
  `404.html` for misses. `.assetsignore` keeps sources/tooling unpublished.
- `_headers`, `_redirects` — Cloudflare response headers and redirects
  (`/blog` → `/`)

## Tooling

Requires [uv](https://docs.astral.sh/uv/) and [just](https://just.systems/);
`just preview` also needs Node (runs `wrangler` via `npx`).

```sh
just build     # regenerate the site after editing content/ or templates/
just preview   # Cloudflare-accurate local preview at http://localhost:8787
just check     # output is current, links resolve, sitemap is consistent
```

## Writing a post

1. Create `content/posts/YYYY-MM-DD-your-slug.md`. The filename sets the date
   and the URL: `/YYYY/MM/DD/your-slug`.
2. Add front matter:

   ```yaml
   ---
   title: "Your Title"                          # required
   post-image: /assets/images/your-image.jpeg   # required; add the file to assets/images/
   description: One-line summary                # optional; else the opening text is used
   tags:                                        # optional; searchable, linked from the post
   - engineering management
   published: false                             # draft: excluded from the build
   ---
   ```

3. Write Markdown (tables, footnotes, and smart quotes/dashes are supported).
   Link other posts by extensionless URL, e.g. `/2023/12/28/pointless-velocity`.
4. Preview: set `published: true`, run `just preview`. Or push a branch and use
   its Cloudflare preview URL.
5. Publish: `published: true` (or remove the line), then `just build`,
   `just check`, and commit the post **and** the regenerated files (post page,
   `index.html`, `feed.xml`, `sitemap.xml`, `search.json`, `llms.txt`). Push
   to `main`.

Drafts are safe to commit: `content/` is never served.

Post URLs use the same scheme as the previous Jekyll site, so existing links
keep working; Cloudflare redirects the old `.html` forms to the clean URLs.

All content, including posts and photos, is Copyright &copy; Justin Pease.
All rights reserved.
