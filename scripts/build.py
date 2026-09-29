#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "jinja2>=3.1,<4",
#   "markdown>=3.7,<4",
#   "pyyaml>=6,<7",
# ]
# ///
"""Render content/ + templates/ into the static site at the repo root.

The generated HTML/XML/JSON is committed and deployed as-is (Cloudflare
serves the repo root with no build step), so this only runs locally:

    just build     # write the site
    just check     # includes `build.py --check`: fails if output is stale

URL scheme matches the old Jekyll site so no redirects are needed: posts are
written to YYYY/MM/DD/<slug>.html and linked extensionless (Cloudflare serves
/foo from foo.html and redirects /foo.html to /foo).
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"

POST_FILENAME = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(.+)\.md$")
FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
# Top-level output directories owned entirely by the build (one per post
# year); they are wiped and rewritten so deleted/renamed posts leave nothing
# behind.
YEAR_DIR = re.compile(r"^\d{4}$")

WORDS_PER_MINUTE = 180
EXCERPT_CHARS = 300


@dataclass(frozen=True)
class Post:
    source: Path
    title: str
    date: dt.date
    slug: str
    description: str
    image: str
    tags: list[str]
    html: str
    text: str

    @property
    def url(self) -> str:
        """Site-relative, extensionless URL (the canonical form)."""
        return f"/{self.date:%Y/%m/%d}/{self.slug}"

    @property
    def output(self) -> str:
        return f"{self.date:%Y/%m/%d}/{self.slug}.html"

    @property
    def excerpt(self) -> str:
        return truncate(self.text, EXCERPT_CHARS)

    @property
    def summary(self) -> str:
        """Description when the post has one, otherwise the excerpt."""
        return self.description or self.excerpt

    @property
    def minutes(self) -> int:
        return max(1, len(self.text.split()) // WORDS_PER_MINUTE)


def truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0]
    return cut.rstrip(" ,;:.-—") + "…"


def plain_text(rendered: str) -> str:
    # Block tags become word breaks; inline tags vanish so "<em>x</em>." stays "x.".
    text = re.sub(r"</?(?:p|li|ul|ol|h[1-6]|blockquote|br|hr|div|pre|table|tr|td|th)\b[^>]*>", " ", rendered)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def load_yaml(path: Path):
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_posts() -> list[Post]:
    # Posts were written for Jekyll's kramdown; "extra" + "smarty" + "toc"
    # cover the features they use (tables, footnotes, typographic quotes,
    # heading ids).
    md = markdown.Markdown(
        extensions=["extra", "smarty", "toc", "sane_lists"],
        output_format="html",
    )
    # kramdown treats \< as an escape; Python-Markdown doesn't by default.
    md.ESCAPED_CHARS.append("<")
    posts = []
    for path in sorted((CONTENT / "posts").glob("*.md")):
        name = POST_FILENAME.match(path.name)
        if not name:
            sys.exit(f"{path.relative_to(ROOT)}: expected YYYY-MM-DD-slug.md")
        raw = path.read_text(encoding="utf-8")
        fm = FRONT_MATTER.match(raw)
        if not fm:
            sys.exit(f"{path.relative_to(ROOT)}: missing --- front matter ---")
        meta = yaml.safe_load(fm.group(1)) or {}
        if meta.get("published") is False:
            continue
        for key in ("title", "post-image"):
            if not meta.get(key):
                sys.exit(f"{path.relative_to(ROOT)}: front matter needs `{key}`")
        year, month, day, slug = name.groups()
        body = md.reset().convert(raw[fm.end() :])
        posts.append(
            Post(
                source=path,
                title=str(meta["title"]).strip(),
                date=dt.date(int(year), int(month), int(day)),
                slug=slug,
                description=str(meta.get("description") or "").strip(),
                image=meta["post-image"],
                tags=[str(t) for t in meta.get("tags") or []],
                html=body,
                text=plain_text(body),
            )
        )
    posts.sort(key=lambda p: (p.date, p.slug), reverse=True)
    return posts


def asset_url(path: str) -> str:
    """Cache-busting URL: /styles/main.css -> /styles/main.css?v=<hash>.
    _headers gives CSS/JS a short max-age; the token makes changes land
    immediately anyway."""
    digest = hashlib.sha256((ROOT / path.lstrip("/")).read_bytes()).hexdigest()
    return f"{path}?v={digest[:10]}"


def render_site() -> dict[str, str]:
    site = load_yaml(CONTENT / "site.yml")
    projects = load_yaml(CONTENT / "projects.yml")
    posts = load_posts()
    if not posts:
        sys.exit("no published posts in content/posts/")

    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        autoescape=select_autoescape(["html", "xml"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters["absolute"] = lambda path: site["url"] + path
    env.filters["longdate"] = lambda d: f"{d:%B} {d.day}, {d.year}"
    # Derived from content rather than today's date so output (and --check)
    # only changes when content does.
    first, latest = posts[-1].date, posts[0].date
    env.globals.update(
        site=site,
        asset=asset_url,
        copyright_years=f"{first.year}–{latest.year}" if first.year != latest.year else str(latest.year),
    )

    def page(template: str, **ctx) -> str:
        return env.get_template(template).render(**ctx)

    out = {
        "index.html": page("home.html", path="/"),
        "blog.html": page("blog.html", path="/blog", posts=posts),
        "projects.html": page("projects.html", path="/projects", projects=projects),
        "404.html": page("404.html", path="/404"),
        "feed.xml": page("feed.xml", posts=posts, updated=latest),
        "sitemap.xml": page("sitemap.xml", posts=posts, latest=latest),
        "llms.txt": page("llms.txt", posts=posts),
    }
    for post in posts:
        out[post.output] = page("post.html", path=post.url, post=post)

    out["search.json"] = (
        json.dumps(
            [
                {
                    "url": p.url,
                    "title": p.title,
                    "description": p.description,
                    "tags": p.tags,
                    "text": p.text,
                }
                for p in posts
            ],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n"
    )
    return out


def owned_files() -> set[str]:
    """Files currently on disk under build-owned year directories."""
    found = set()
    for d in ROOT.iterdir():
        if d.is_dir() and YEAR_DIR.match(d.name):
            found.update(str(p.relative_to(ROOT)) for p in d.rglob("*") if p.is_file())
    return found


def check(out: dict[str, str]) -> int:
    stale = sorted(
        rel
        for rel, content in out.items()
        if not (ROOT / rel).is_file() or (ROOT / rel).read_text(encoding="utf-8") != content
    )
    extra = sorted(owned_files() - out.keys())
    if not stale and not extra:
        print(f"OK: {len(out)} generated file(s) match content/ and templates/.")
        return 0
    print("Generated site is out of date; run `just build`.", file=sys.stderr)
    for rel in stale:
        print(f"  stale:   {rel}", file=sys.stderr)
    for rel in extra:
        print(f"  orphan:  {rel}", file=sys.stderr)
    return 1


def write(out: dict[str, str]) -> None:
    for d in ROOT.iterdir():
        if d.is_dir() and YEAR_DIR.match(d.name):
            shutil.rmtree(d)
    for rel, content in out.items():
        target = ROOT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    print(f"Wrote {len(out)} file(s).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="verify committed output is current; write nothing")
    args = parser.parse_args()
    out = render_site()
    if args.check:
        sys.exit(check(out))
    write(out)


if __name__ == "__main__":
    main()
