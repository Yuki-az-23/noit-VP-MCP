import sys

from noit_documenting_data_flow import cli


def run(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["noit-diagram-rollup", *args])
    return cli.main()


def test_init_creates_the_documented_files(project):
    for rel in [
        "docs/architecture/diagrams/00-template.md",
        "docs/architecture/diagrams/rollup.manifest.yml",
        "docs/architecture/diagrams/.pages",
        "docs/javascripts/mermaid-interactive.js",
        "docs/stylesheets/mermaid-interactive.css",
        ".claude/skills/documenting-data-flow/SKILL.md",
    ]:
        assert (project / rel).is_file(), rel


def test_skill_only_mentions_files_and_flags_that_exist(project):
    skill = (project / ".claude/skills/documenting-data-flow/SKILL.md").read_text()
    assert "--dry-run" not in skill
    assert "star-template.md" not in skill
    assert "scripts/build_diagram_rollup.py" not in skill


def test_build_is_a_dry_run_by_default(project, monkeypatch):
    assert run(monkeypatch, "build") == 0
    assert not (project / "docs/architecture_diagrams.generated.html").exists()


def test_build_write_emits_generated_siblings(project, monkeypatch):
    assert run(monkeypatch, "build", "--write") == 0
    assert (project / "docs/architecture_diagrams.generated.html").is_file()
    assert (project / "docs/architecture/diagrams/OVERVIEW.generated.md").is_file()


def test_validate_passes_on_a_fresh_project(project, monkeypatch):
    assert run(monkeypatch, "validate") == 0


def test_validate_fails_on_a_missing_piece(project, diagrams_dir, monkeypatch):
    (diagrams_dir / "00-template.md").unlink()
    assert run(monkeypatch, "validate") == 1


def test_noit_yml_moves_the_outputs(project, monkeypatch):
    (project / "noit.yml").write_text("out_html: site-src/arch.html\n")
    assert run(monkeypatch, "build", "--write") == 0
    assert (project / "site-src/arch.html").is_file()


def test_invalid_noit_yml_is_reported(project, monkeypatch, capsys):
    (project / "noit.yml").write_text("bogus: 1\n")
    assert run(monkeypatch, "build") == 1
    assert "unknown setting(s) bogus" in capsys.readouterr().out
