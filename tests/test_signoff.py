from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from pmo_studio.core.project import Project, ProjectConfig
from pmo_studio.core.signoff import update_signoff, load_signoff, assert_export_allowed


def test_final_signoff_locks_export_unless_forced():
    with TemporaryDirectory() as td:
        p = Project(Path(td) / "signed", ProjectConfig(project_slug="signed", customer="Demo"))
        p.ensure_layout(); p.save()
        update_signoff(p, "BA", "approved", approved_by="QA")
        assert load_signoff(p)["locked"] is False
        update_signoff(p, "Final", "approved", approved_by="Snail", note="Ready")
        assert load_signoff(p)["locked"] is True
        with pytest.raises(RuntimeError):
            assert_export_allowed(p.root)
        assert_export_allowed(p.root, force=True)
