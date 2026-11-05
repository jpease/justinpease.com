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
from dataclasses import dataclass, field
from pathlib import Path

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"

POST_FILENAME = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(.+)\.md$")
FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
# Top-level output directories owned entirely by the build: one per post year
# plus handbook/. They are wiped and rewritten so deleted/renamed content
# leaves nothing behind.
YEAR_DIR = re.compile(r"^\d{4}$")
HANDBOOK_DIR = "handbook"

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


@dataclass(eq=False)
class Page:
    """An undated handbook page. Pages form a tree; URLs are independent of it."""

    source: Path
    slug: str  # path under content/handbook, no extension; "" for the root; an index.md takes its directory's path
    is_index: bool
    title: str
    order: int
    parent_slug: str | None
    html: str
    text: str
    parent: Page | None = None
    children: list[Page] = field(default_factory=list)

    @property
    def url(self) -> str:
        """Site-relative canonical URL: section indexes end in "/", leaf pages do not."""
        if self.is_index:
            return f"/{HANDBOOK_DIR}/{self.slug}/" if self.slug else f"/{HANDBOOK_DIR}/"
        return f"/{HANDBOOK_DIR}/{self.slug}"

    @property
    def output(self) -> str:
        if self.is_index:
            return f"{HANDBOOK_DIR}/{self.slug}/index.html" if self.slug else f"{HANDBOOK_DIR}/index.html"
        return f"{HANDBOOK_DIR}/{self.slug}.html"

    @property
    def summary(self) -> str:
        return truncate(self.text, EXCERPT_CHARS)

    @property
    def ancestors(self) -> list[Page]:
        """Root first, excluding self."""
        chain = []
        node = self.parent
        while node:
            chain.append(node)
            node = node.parent
        return chain[::-1]


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
    md = new_markdown()
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


def new_markdown() -> markdown.Markdown:
    # Content was written for Jekyll's kramdown; "extra" + "smarty" + "toc"
    # cover the features it uses (tables, footnotes, typographic quotes,
    # heading ids), and "admonition" renders the handbook's callouts
    # (`!!! tip`).
    md = markdown.Markdown(
        extensions=["extra", "smarty", "toc", "sane_lists", "admonition"],
        output_format="html",
    )
    # kramdown treats \< as an escape; Python-Markdown doesn't by default.
    md.ESCAPED_CHARS.append("<")
    return md


def load_handbook() -> list[Page]:
    """Parse content/handbook/**/*.md into a tree; return pages in reading
    (depth-first, `order` then title) order, root first.

    A page's parent is its directory's index.md (the root index.md for
    top-level files) unless front matter sets `parent: <slug>`; that lets a
    page nest under a sibling without changing its URL."""
    md = new_markdown()
    base = CONTENT / HANDBOOK_DIR
    pages: dict[str, Page] = {}
    for path in sorted(base.rglob("*.md")):
        rel = path.relative_to(base).with_suffix("")
        is_index = rel.name == "index"
        slug = "/".join(rel.parent.parts if is_index else rel.parts)
        where = path.relative_to(ROOT)
        raw = path.read_text(encoding="utf-8")
        fm = FRONT_MATTER.match(raw)
        if not fm:
            sys.exit(f"{where}: missing --- front matter ---")
        meta = yaml.safe_load(fm.group(1)) or {}
        if not meta.get("title"):
            sys.exit(f"{where}: front matter needs `title`")
        if not isinstance(meta.get("order"), int):
            sys.exit(f"{where}: front matter needs integer `order`")
        if slug in pages:
            sys.exit(f"{where}: slug {slug!r} collides with {pages[slug].source.relative_to(ROOT)}")
        default_parent = None if not slug else slug.rsplit("/", 1)[0] if "/" in slug else ""
        body = md.reset().convert(raw[fm.end() :])
        pages[slug] = Page(
            source=path,
            slug=slug,
            is_index=is_index,
            title=str(meta["title"]).strip(),
            order=meta["order"],
            parent_slug=str(meta["parent"]) if "parent" in meta else default_parent,
            html=body,
            text=plain_text(body),
        )
    if "" not in pages:
        sys.exit("content/handbook/index.md is required (the handbook root)")
    for p in pages.values():
        if p.parent_slug is None:
            continue
        parent = pages.get(p.parent_slug)
        if parent is None:
            sys.exit(f"{p.source.relative_to(ROOT)}: parent {p.parent_slug!r} does not exist")
        p.parent = parent
        parent.children.append(p)
    for p in pages.values():
        p.children.sort(key=lambda c: (c.order, c.title))

    ordered: list[Page] = []

    def walk(p: Page) -> None:
        ordered.append(p)
        for c in p.children:
            walk(c)

    walk(pages[""])
    lost = sorted(p.source.relative_to(ROOT).as_posix() for p in pages.values() if p not in ordered)
    if lost:
        sys.exit(f"handbook pages unreachable from the root (parent cycle?): {', '.join(lost)}")
    return ordered


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
    handbook = load_handbook()

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
        "index.html": page("blog.html", path="/", posts=posts),
        "projects.html": page("projects.html", path="/projects", projects=projects),
        "404.html": page("404.html", path="/404"),
        "feed.xml": page("feed.xml", posts=posts, updated=latest),
        "sitemap.xml": page("sitemap.xml", posts=posts, handbook=handbook, latest=latest),
        "llms.txt": page("llms.txt", posts=posts, handbook=handbook),
    }
    for post in posts:
        out[post.output] = page("post.html", path=post.url, post=post)
    for i, doc in enumerate(handbook):
        out[doc.output] = page(
            "handbook.html",
            path=doc.url,
            doc=doc,
            prev_doc=handbook[i - 1] if i else None,
            next_doc=handbook[i + 1] if i + 1 < len(handbook) else None,
        )

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


def is_owned_dir(d: Path) -> bool:
    return d.is_dir() and (YEAR_DIR.match(d.name) is not None or d.name == HANDBOOK_DIR)


def owned_files() -> set[str]:
    """Files currently on disk under build-owned directories."""
    found = set()
    for d in ROOT.iterdir():
        if is_owned_dir(d):
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
        if is_owned_dir(d):
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
