"""PMO Studio lightweight Web UI MVP.

Local-first stdlib HTTP app: upload/source form, run pipeline via internal CLI
functions, project list, and artifact download links.
"""
from __future__ import annotations

import argparse
import html
import shutil
import tempfile
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from pmo_studio.core.project import DEFAULT_ROOT
from pmo_studio.core.registry import list_projects, refresh_registry
from pmo_studio.cli import cmd_run_project


def run_web(root: Path = DEFAULT_ROOT, host: str = "127.0.0.1", port: int = 8765):
    root.mkdir(parents=True, exist_ok=True)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/":
                self._home(root)
            elif parsed.path == "/download":
                qs = urllib.parse.parse_qs(parsed.query)
                self._download(root, qs.get("path", [""])[0])
            else:
                self.send_error(404)

        def do_POST(self):
            if self.path != "/run":
                self.send_error(404); return
            length = int(self.headers.get("Content-Length", "0"))
            data = urllib.parse.parse_qs(self.rfile.read(length).decode("utf-8"))
            slug = _slug(data.get("slug", [""])[0])
            source_text = data.get("source_text", [""])[0]
            customer = data.get("customer", ["TBD"])[0]
            product = data.get("product", ["PMO Studio Project"])[0]
            if not slug or not source_text.strip():
                self._html("<h1>Missing slug or source text</h1><p><a href='/'>Back</a></p>", 400); return
            source = root / "_web_uploads" / f"{slug}-source.md"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text(source_text, encoding="utf-8")
            try:
                cmd_run_project(argparse.Namespace(root=str(root), slug=slug, source=str(source), customer=customer, product=product, brief="Generated from PMO Studio Web UI", domain_pack="generic", profile="customer", llm="noop", model="Tier2", refine=False, max_refine=0, signoff_final=False, by="Web UI", force=True))
            except Exception as exc:
                self._html(f"<h1>Run failed</h1><pre>{html.escape(type(exc).__name__ + ': ' + str(exc))}</pre><p><a href='/'>Back</a></p>", 500); return
            self.send_response(303); self.send_header("Location", f"/?created={urllib.parse.quote(slug)}"); self.end_headers()

        def _home(self, root: Path):
            refresh_registry(root)
            projects = list_projects(root, include_archived=False)
            rows = []
            for p in projects[:50]:
                proj_root = Path(p.root)
                links = []
                for rel, label in [("exports/customer/pmo-documentation-pack.docx", "DOCX"), ("exports/customer/pmo-documentation-pack.pdf", "PDF"), ("artifacts/ba/06-quotation.xlsx", "Quotation"), ("exports/customer/telegram-delivery.json", "Delivery")]:
                    fp = proj_root / rel
                    if fp.exists():
                        links.append(f"<a href='/download?path={urllib.parse.quote(str(fp))}'>{label}</a>")
                rows.append(f"<tr><td>{html.escape(p.slug)}</td><td>{html.escape(p.customer)}</td><td>{html.escape(p.lifecycle_state)}</td><td>{' | '.join(links)}</td></tr>")
            body = f"""
<h1>PMO Studio Web UI</h1>
<form method='post' action='/run'>
  <p><label>Slug<br><input name='slug' required></label></p>
  <p><label>Customer<br><input name='customer' value='TBD'></label></p>
  <p><label>Product<br><input name='product' value='PMO Studio Project'></label></p>
  <p><label>Source Markdown/Text<br><textarea name='source_text' rows='12' cols='100' required></textarea></label></p>
  <p><button type='submit'>Run PMO Pipeline</button></p>
</form>
<h2>Projects</h2><table><tr><th>Slug</th><th>Customer</th><th>State</th><th>Downloads</th></tr>{''.join(rows)}</table>
"""
            self._html(body)

        def _download(self, root: Path, raw: str):
            path = Path(raw).resolve()
            if not str(path).startswith(str(root.resolve())) or not path.exists() or not path.is_file():
                self.send_error(404); return
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", f"attachment; filename={path.name}")
            self.end_headers()
            with path.open("rb") as f:
                shutil.copyfileobj(f, self.wfile)

        def _html(self, body: str, status: int = 200):
            page = f"""<!doctype html><html><head><meta charset='utf-8'><title>PMO Studio</title>
<style>body{{font-family:Arial,sans-serif;margin:32px;max-width:1100px}} input,textarea{{width:100%;padding:8px}} table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:8px;text-align:left}}button{{padding:10px 16px}}</style></head><body>{body}</body></html>"""
            data = page.encode("utf-8")
            self.send_response(status); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"PMO Studio Web UI: http://{host}:{port} root={root}")
    server.serve_forever()


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in value.strip().lower()).strip("-")[:80]


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    run_web(Path(args.root), args.host, args.port)


if __name__ == "__main__":
    main()
