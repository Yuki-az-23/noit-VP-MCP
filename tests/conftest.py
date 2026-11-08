import sys
from pathlib import Path

import pytest

from noit_documenting_data_flow import cli


@pytest.fixture
def project(tmp_path, monkeypatch):
    """A fresh `noit-diagram-rollup init` project as the working directory."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["noit-diagram-rollup", "init"])
    assert cli.main() == 0
    return tmp_path


@pytest.fixture
def diagrams_dir(project) -> Path:
    return project / "docs" / "architecture" / "diagrams"
