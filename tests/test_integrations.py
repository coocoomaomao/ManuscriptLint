from pathlib import Path

import manuscriptlint.integrations as integrations
from manuscriptlint.models import Severity


def test_missing_integration_is_warning(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(integrations.shutil, "which", lambda _tool: None)
    findings = integrations.run_integration("figurelint", tmp_path)
    assert findings[0].code == "FIGURELINT_NOT_INSTALLED"
    assert findings[0].severity is Severity.WARNING
