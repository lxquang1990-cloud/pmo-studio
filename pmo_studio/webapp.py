"""PMO Studio lightweight Web UI.

Local-first stdlib HTTP app: source form/file upload, run pipeline via internal
CLI functions, project dashboard pages, and artifact download links.
"""
from __future__ import annotations

import argparse
import html
import json
import mimetypes
import shutil
import traceback
import urllib.parse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from pmo_studio.cli import cmd_run_project
from pmo_studio.core.lifecycle import summarize_project
from pmo_studio.core.project import DEFAULT_ROOT, Project
from pmo_studio.core.registry import list_projects, refresh_registry
from pmo_studio.integrations.telegram_workflow import build_delivery_manifest
from pmo_studio.quality.intelligence import write_quality_intelligence
from pmo_studio.domain.manager import export_domain, import_domain, inspect_domain, list_domains, scaffold_domain, update_domain, validate_domain


@dataclass
class WebRunStatus:
    schema: str
    slug: str
    status: str
    created_at: str
    updated_at: str
    source_path: str | None = None
    error_type: str | None = None
    error_message: str | None = None
    traceback_tail: str | None = None


def run_web(root: Path = DEFAULT_ROOT, host: str = "127.0.0.1", port: int = 8765):
    root.mkdir(parents=True, exist_ok=True)
    if host not in {"127.0.0.1", "localhost", "::1"}:
        print(f"WARNING: PMO Studio Web UI bound to non-local host {host}. Use Tailscale/auth reverse proxy before exposing publicly.")

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            if parsed.path == "/":
                self._home(root)
            elif parsed.path.startswith("/project/"):
                self._project(root, urllib.parse.unquote(parsed.path.removeprefix("/project/")))
            elif parsed.path == "/download":
                self._download(root, qs.get("path", [""])[0])
            elif parsed.path == "/domains":
                self._domains(root, qs.get("selected", [""])[0])
            elif parsed.path == "/status":
                self._status(root, qs.get("slug", [""])[0])
            else:
                self.send_error(404)

        def do_POST(self):
            if self.path == "/domains/scaffold":
                self._domain_scaffold(root); return
            if self.path == "/domains/update":
                self._domain_update(root); return
            if self.path == "/domains/import":
                self._domain_import(root); return
            if self.path != "/run":
                self.send_error(404); return
            try:
                data, files = _parse_post(self)
                slug = _slug(data.get("slug", ""))
                customer = data.get("customer", "TBD") or "TBD"
                product = data.get("product", "PMO Studio Project") or "PMO Studio Project"
                source_text = data.get("source_text", "")
                if not slug:
                    self._html("<h1>Missing slug</h1><p><a href='/'>Back</a></p>", 400); return
                source = _write_source(root, slug, source_text, files.get("source_file"))
                if not source:
                    self._html("<h1>Missing source</h1><p>Paste text or upload a .md/.txt/.docx/.pdf source file.</p><p><a href='/'>Back</a></p>", 400); return
                _write_status(root, WebRunStatus("pmo.web_run_status.v1", slug, "running", _now(), _now(), str(source)))
                try:
                    cmd_run_project(argparse.Namespace(root=str(root), slug=slug, source=str(source), customer=customer, product=product, brief="Generated from PMO Studio Web UI", domain_pack="generic", profile="customer", llm="noop", model="Tier2", refine=False, max_refine=0, signoff_final=False, by="Web UI", force=True))
                    project = Project.load(slug, root_base=root)
                    write_quality_intelligence(project.root)
                    build_delivery_manifest(project.root)
                    _write_status(root, WebRunStatus("pmo.web_run_status.v1", slug, "done", _now(), _now(), str(source)))
                except Exception as exc:
                    _write_status(root, WebRunStatus("pmo.web_run_status.v1", slug, "error", _now(), _now(), str(source), type(exc).__name__, str(exc), traceback.format_exc()[-4000:]))
                    raise
            except Exception as exc:
                self._html(_error_page(exc, slug if 'slug' in locals() else None), 500); return
            self.send_response(303); self.send_header("Location", f"/project/{urllib.parse.quote(slug)}"); self.end_headers()

        def _home(self, root: Path):
            refresh_registry(root)
            projects = list_projects(root, include_archived=False)
            rows = []
            for p in projects[:50]:
                status = _read_status(root, p.slug).get("status", "")
                rows.append(f"<tr><td><a href='/project/{urllib.parse.quote(p.slug)}'>{html.escape(p.slug)}</a></td><td>{html.escape(p.customer)}</td><td>{html.escape(p.lifecycle_state)}</td><td>{html.escape(status)}</td><td>{html.escape(p.updated_at)}</td></tr>")
            body = f"""
<h1>PMO Studio Web UI</h1><p><a href='/domains'>Domain Pack Studio</a></p>
<p class='muted'>Local-first PMO documentation operating system. Default LLM mode: noop/offline.</p>
<form method='post' action='/run' enctype='multipart/form-data'>
  <p><label>Slug<br><input name='slug' required></label></p>
  <p><label>Customer<br><input name='customer' value='TBD'></label></p>
  <p><label>Product<br><input name='product' value='PMO Studio Project'></label></p>
  <p><label>Source file (.md/.txt/.docx/.pdf)<br><input type='file' name='source_file'></label></p>
  <p><label>Or paste Source Markdown/Text<br><textarea name='source_text' rows='12' cols='100'></textarea></label></p>
  <p><button type='submit'>Run PMO Pipeline</button></p>
</form>
<h2>Projects</h2><table><tr><th>Slug</th><th>Customer</th><th>Lifecycle</th><th>Run</th><th>Updated</th></tr>{''.join(rows)}</table>
"""
            self._html(body)

        def _project(self, root: Path, slug: str):
            try:
                project = Project.load(slug, root_base=root)
                summary = summarize_project(project)
            except Exception as exc:
                self._html(_error_page(exc, slug), 404); return
            status = _read_status(root, slug)
            files = _download_files(project.root)
            links = "".join(f"<li><a href='/download?path={urllib.parse.quote(str(path))}'>{html.escape(label)}</a> <span class='muted'>{path.stat().st_size} bytes</span></li>" for label, path in files)
            body = f"""
<p><a href='/'>← Projects</a></p>
<h1>{html.escape(slug)}</h1>
<div class='cards'>
  <div><b>Customer</b><br>{html.escape(summary.customer)}</div>
  <div><b>Lifecycle</b><br>{html.escape(summary.state)}</div>
  <div><b>Quality</b><br>{summary.gate_passed}/{summary.gate_total} passed, failed={summary.gate_failed}</div>
  <div><b>Traceability</b><br>{_trace_label(summary)}</div>
  <div><b>Artifacts</b><br>{summary.artifact_count}</div>
  <div><b>Run Status</b><br>{html.escape(status.get('status', 'unknown'))}</div>
</div>
<h2>Downloads</h2><ul>{links or '<li>No exports yet</li>'}</ul>
<h2>Run status JSON</h2><pre>{html.escape(json.dumps(status, ensure_ascii=False, indent=2))}</pre>
<h2>Project root</h2><pre>{html.escape(str(project.root))}</pre>
"""
            self._html(body)

        def _domains(self, root: Path, selected: str = ""):
            rows = []
            for row in list_domains():
                did = row['id']
                rows.append(f"<tr><td><a href='/domains?selected={urllib.parse.quote(did)}'>{html.escape(did)}</a></td><td>{html.escape(row['label'])}</td><td>{row['pack_version']}</td><td>{row['keywords']}</td><td>{row['modules']}</td></tr>")
            detail = ""
            if selected:
                try:
                    data = inspect_domain(selected)
                    validation = validate_domain(selected)
                    export_path = export_domain(selected, root / '_domain_exports')
                    detail = f"""<h2>Inspect: {html.escape(selected)}</h2>
<p>Validation: <b>{'PASS' if validation['passed'] else 'FAIL'}</b> | <a href='/download?path={urllib.parse.quote(str(export_path))}'>Export YAML</a></p>
<pre>{html.escape(json.dumps(data, ensure_ascii=False, indent=2))}</pre>
<h3>Append field values</h3>
<form method='post' action='/domains/update'>
<input type='hidden' name='domain_id' value='{html.escape(selected)}'>
<p><label>Field<br><select name='field'><option>keywords</option><option>modules</option><option>workflows</option><option>reports</option><option>integrations</option><option>risk_factors</option><option>acceptance_presets</option></select></label></p>
<p><label>Values (comma-separated)<br><input name='values'></label></p>
<p><button type='submit'>Append</button></p>
</form>"""
                except Exception as exc:
                    detail = _error_page(exc, selected)
            body = f"""<p><a href='/'>← Projects</a></p><h1>Domain Pack Studio</h1>
<h2>Scaffold domain</h2><form method='post' action='/domains/scaffold'><p><label>ID<br><input name='domain_id' required></label></p><p><label>Label<br><input name='label' required></label></p><p><label><input type='checkbox' name='force' value='1'> overwrite</label></p><p><button type='submit'>Scaffold</button></p></form>
<h2>Import YAML</h2><form method='post' action='/domains/import' enctype='multipart/form-data'><p><input type='file' name='domain_file' required></p><p><label><input type='checkbox' name='force' value='1'> overwrite</label></p><p><button type='submit'>Import</button></p></form>
<h2>Domain packs</h2><table><tr><th>ID</th><th>Label</th><th>Version</th><th>Keywords</th><th>Modules</th></tr>{''.join(rows)}</table>{detail}"""
            self._html(body)

        def _domain_scaffold(self, root: Path):
            data, _ = _parse_post(self)
            scaffold_domain(_slug(data.get('domain_id', '')), data.get('label', ''), force=data.get('force') == '1')
            self.send_response(303); self.send_header('Location', '/domains'); self.end_headers()

        def _domain_update(self, root: Path):
            data, _ = _parse_post(self)
            domain_id = data.get('domain_id', '')
            update_domain(domain_id, {data.get('field', ''): data.get('values', '')})
            self.send_response(303); self.send_header('Location', f"/domains?selected={urllib.parse.quote(domain_id)}"); self.end_headers()

        def _domain_import(self, root: Path):
            data, files = _parse_post(self)
            upload = files.get('domain_file')
            if not upload:
                self._html('<h1>Missing domain file</h1>', 400); return
            src = root / '_domain_imports' / Path(upload[0]).name
            src.parent.mkdir(parents=True, exist_ok=True); src.write_bytes(upload[1])
            dest = import_domain(src, force=data.get('force') == '1')
            self.send_response(303); self.send_header('Location', f"/domains?selected={urllib.parse.quote(dest.stem)}"); self.end_headers()

        def _status(self, root: Path, slug: str):
            data = json.dumps(_read_status(root, slug), ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(200); self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)

        def _download(self, root: Path, raw: str):
            path = Path(raw).resolve()
            if not str(path).startswith(str(root.resolve())) or not path.exists() or not path.is_file():
                self.send_error(404); return
            self.send_response(200)
            self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
            self.send_header("Content-Disposition", f"attachment; filename={path.name}")
            self.end_headers()
            with path.open("rb") as f:
                shutil.copyfileobj(f, self.wfile)

        def _html(self, body: str, status: int = 200):
            page = f"""<!doctype html><html><head><meta charset='utf-8'><title>PMO Studio</title>
<style>body{{font-family:Arial,sans-serif;margin:32px;max-width:1100px}} input,textarea{{width:100%;padding:8px}} table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:8px;text-align:left}}button{{padding:10px 16px}} .muted{{color:#666}} .cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}} .cards div{{border:1px solid #ddd;border-radius:8px;padding:12px;background:#fafafa}} pre{{white-space:pre-wrap;background:#f6f8fa;padding:12px;border-radius:8px}}</style></head><body>{body}</body></html>"""
            data = page.encode("utf-8")
            self.send_response(status); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"PMO Studio Web UI: http://{host}:{port} root={root}")
    server.serve_forever()


def _parse_post(handler: BaseHTTPRequestHandler) -> tuple[dict[str, str], dict[str, tuple[str, bytes]]]:
    content_type = handler.headers.get("Content-Type", "")
    length = int(handler.headers.get("Content-Length", "0"))
    body = handler.rfile.read(length)
    if content_type.startswith("multipart/form-data"):
        boundary = _multipart_boundary(content_type)
        if not boundary:
            return {}, {}
        return _parse_multipart(body, boundary)
    data = urllib.parse.parse_qs(body.decode("utf-8"))
    return {k: v[0] for k, v in data.items()}, {}


def _multipart_boundary(content_type: str) -> bytes | None:
    for part in content_type.split(";"):
        part = part.strip()
        if part.startswith("boundary="):
            value = part.split("=", 1)[1].strip().strip('"')
            return value.encode("utf-8")
    return None


def _parse_multipart(body: bytes, boundary: bytes) -> tuple[dict[str, str], dict[str, tuple[str, bytes]]]:
    data: dict[str, str] = {}
    files: dict[str, tuple[str, bytes]] = {}
    marker = b"--" + boundary
    for raw_part in body.split(marker):
        part = raw_part.strip(b"\r\n")
        if not part or part == b"--":
            continue
        header_blob, sep, content = part.partition(b"\r\n\r\n")
        if not sep:
            continue
        headers = header_blob.decode("utf-8", errors="replace").split("\r\n")
        disposition = next((h for h in headers if h.lower().startswith("content-disposition:")), "")
        attrs = _parse_disposition_attrs(disposition)
        name = attrs.get("name")
        if not name:
            continue
        if content.endswith(b"\r\n"):
            content = content[:-2]
        if "filename" in attrs and attrs["filename"]:
            files[name] = (Path(attrs["filename"]).name, content)
        else:
            data[name] = content.decode("utf-8", errors="replace")
    return data, files


def _parse_disposition_attrs(disposition: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for part in disposition.split(";")[1:]:
        if "=" in part:
            key, value = part.strip().split("=", 1)
            attrs[key.lower()] = value.strip().strip('"')
    return attrs


def _write_source(root: Path, slug: str, source_text: str, upload: tuple[str, bytes] | None) -> Path | None:
    source_dir = root / "_web_uploads"
    source_dir.mkdir(parents=True, exist_ok=True)
    if upload and upload[1]:
        filename, content = upload
        suffix = Path(filename).suffix.lower() or ".bin"
        path = source_dir / f"{slug}-source{suffix}"
        path.write_bytes(content)
        return path
    if source_text.strip():
        path = source_dir / f"{slug}-source.md"
        path.write_text(source_text, encoding="utf-8")
        return path
    return None


def _download_files(project_root: Path) -> list[tuple[str, Path]]:
    candidates = [("DOCX documentation pack", "exports/customer/pmo-documentation-pack.docx"), ("PDF documentation pack", "exports/customer/pmo-documentation-pack.pdf"), ("Quotation workbook", "artifacts/ba/06-quotation.xlsx"), ("Quality intelligence", "quality/intelligence.md"), ("Project bundle", f"exports/customer/{project_root.name}-pmo-bundle.zip"), ("Dashboard HTML", "exports/management/index.html"), ("Telegram delivery manifest", "exports/customer/telegram-delivery.json"), ("Artifact manifest", "artifacts/manifest.json")]
    return [(label, project_root / rel) for label, rel in candidates if (project_root / rel).exists()]


def _status_path(root: Path, slug: str) -> Path:
    return root / slug / "metrics" / "web-run-status.json"


def _write_status(root: Path, status: WebRunStatus) -> Path:
    path = _status_path(root, status.slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(status), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _read_status(root: Path, slug: str) -> dict[str, Any]:
    path = _status_path(root, slug)
    if not path.exists():
        return {"schema": "pmo.web_run_status.v1", "slug": slug, "status": "unknown"}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"schema": "pmo.web_run_status.v1", "slug": slug, "status": "invalid", "error": str(exc)}


def _trace_label(summary) -> str:
    if summary.trace_passed is None:
        return "not run"
    return f"{'PASS' if summary.trace_passed else 'WARN'} ({summary.trace_nodes} nodes/{summary.trace_edges} edges)"


def _error_page(exc: Exception, slug: str | None = None) -> str:
    return f"""
<h1>Run failed</h1>
<p><b>{html.escape(type(exc).__name__)}</b>: {html.escape(str(exc))}</p>
<p>Retry from CLI for full logs:</p>
<pre>pmo summary {html.escape(slug or '<slug>')}</pre>
<details><summary>Traceback tail</summary><pre>{html.escape(traceback.format_exc()[-4000:])}</pre></details>
<p><a href='/'>Back</a></p>
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
