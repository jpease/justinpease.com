# justinpease.com Justfile
# Command runner for building, checking, and previewing the site.
#
# Quick Start:
#   just             # Show available commands
#   just build       # Render content/ + templates/ into the site
#   just check       # Full verification gate
#
# Use `just --list` to see all available commands

# Show available commands (default recipe)
default:
    @just --list

# Render content/ and templates/ into the committed site at the repo root
build:
    @uv run --script scripts/build.py

# python's http.server doesn't map /foo to foo.html the way Cloudflare does,
# so extensionless links (/blog, post URLs) 404 here; use `just preview`.
#
# Build, then serve with python at http://localhost:PORT (no extensionless URLs)
serve PORT="8000": build
    @python3 -m http.server "{{PORT}}"

# Preview with Cloudflare's asset handling (wrangler.jsonc: extensionless URLs, 404 page, _headers)
preview PORT="8787": build
    @npx --yes wrangler dev --port "{{PORT}}"

# Catches typo'd paths and assets that got renamed or deleted.
#
# Fast checks: internal links/assets resolve
check-fast:
    @python3 scripts/check_site.py

# Runs check-fast, sitemap.xml/robots.txt consistency, and verifies the
# committed output matches content/ + templates/ (i.e. `just build` was run).
#
# Full verification gate
check:
    @uv run --script scripts/build.py --check
    @python3 scripts/check_site.py --full
