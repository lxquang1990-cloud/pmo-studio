"""Tests for lifecycle module."""
import tempfile
from pathlib import Path
from pmo_studio.core.project import Project
from pmo_studio.core.lifecycle import (
    infer_lifecycle, summarize_project, summary_markdown,
    sync_lifecycle, archive_project, clone_project,
)

def make_project(slug="lc-test", **kwargs):
    with tempfile.TemporaryDirectory() as tmp:
        p = Project.create(slug, customer="Test", root_base=Path(tmp), **kwargs)
        yield p

def test_infer_lifecycle_state_initiated():
    with tempfile.TemporaryDirectory() as tmp:
        p = Project.create("infer-test", customer="Test", root_base=Path(tmp))
        state = infer_lifecycle(p)
        assert state in ("INITIATED", "GENERATED")

def test_summarize_project():
    with tempfile.TemporaryDirectory() as tmp:
        p = Project.create("sum-test", customer="Test KH", root_base=Path(tmp))
        s = summarize_project(p)
        assert s.slug == "sum-test"
        assert s.customer == "Test KH"
        assert s.state in ("INITIATED", "GENERATED")

def test_summary_markdown():
    with tempfile.TemporaryDirectory() as tmp:
        p = Project.create("md-test", customer="Test", root_base=Path(tmp))
        md = summary_markdown(summarize_project(p))
        assert "md-test" in md
        assert "Test" in md

def test_sync_lifecycle():
    with tempfile.TemporaryDirectory() as tmp:
        p = Project.create("sync-test", customer="Test", root_base=Path(tmp))
        state = sync_lifecycle(p)
        assert state in ("INITIATED", "GENERATED")
        assert p.state.lifecycle_state == state

def test_archive_project():
    with tempfile.TemporaryDirectory() as tmp:
        p = Project.create("arch-test", customer="Test", root_base=Path(tmp))
        dest = archive_project(p, reason="Done", move=False)
        assert "archived" in str(dest) or "ARCHIVED" in p.state.lifecycle_state

def test_clone_project():
    with tempfile.TemporaryDirectory() as tmp:
        p = Project.create("source-lc", customer="Source", root_base=Path(tmp))
        cloned = clone_project(p, "clone-lc", customer="Clone KH")
        assert cloned.config.project_slug == "clone-lc"
        assert cloned.config.customer == "Clone KH"
        assert cloned.root.exists()
        assert (cloned.root / "config.json").exists()
