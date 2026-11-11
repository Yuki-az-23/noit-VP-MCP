import asyncio
import json

import pytest
import yaml
from starlette.testclient import TestClient

from noit_documenting_data_flow import mcp_server


def call(name, **arguments):
    result = asyncio.run(mcp_server.call_tool(name, arguments))
    return result.isError, result.content[0].text


API_PIECE = {
    "slug": "api",
    "title": 'Handle "request"',
    "function_path": "src/api.py",
    "group": "infra",
    "inputs": [{"id": "in1", "label": "HTTP"}],
    "dependencies": [{"id": "auth", "label": "Auth", "type": "extSvc"}],
    "outputs": [{"id": "out1", "label": "Response"}],
}


def test_create_writes_piece_manifest_and_pages(diagrams_dir):
    is_error, _ = call("create_diagram_piece", **API_PIECE)
    assert not is_error

    text = (diagrams_dir / "01-api.md").read_text()
    assert 'hub["⚙️ Handle #quot;request#quot;<br/>src/api.py"]:::hub' in text
    assert 'hub -->|"query"| auth' in text
    manifest = yaml.safe_load((diagrams_dir / "rollup.manifest.yml").read_text())
    assert {"file": "01-api.md", "group": "infra"} in manifest["diagrams"]
    assert "01-api.md" in (diagrams_dir / ".pages").read_text()


def test_create_rejects_bad_node_ids(diagrams_dir):
    is_error, text = call(
        "create_diagram_piece",
        slug="x",
        title="X",
        function_path="x.py",
        inputs=[{"id": "a b", "label": "x"}],
    )
    assert is_error
    assert "Invalid node id" in text


def test_list_returns_json_the_extension_reads(diagrams_dir):
    call("create_diagram_piece", **API_PIECE)
    is_error, text = call("list_diagram_pieces")
    assert not is_error
    pieces = {p["file"]: p for p in json.loads(text)}
    assert pieces["01-api.md"] == {
        "file": "01-api.md",
        "slug": "api",
        "title": 'Handle "request"',
        "function_path": "src/api.py",
        "group": "infra",
        "file_path": "docs/architecture/diagrams/01-api.md",
        "exists": True,
    }


def test_update_metadata_keeps_the_spokes(diagrams_dir):
    call("create_diagram_piece", **API_PIECE)
    is_error, _ = call(
        "update_diagram_piece",
        file="01-api.md",
        title="Handle API",
        function_path="src/api/handler.py",
        group="ops",
    )
    assert not is_error

    text = (diagrams_dir / "01-api.md").read_text()
    assert text.startswith("# Handle API\n")
    assert 'hub["⚙️ Handle API<br/>src/api/handler.py"]:::hub' in text
    assert 'hub -->|"query"| auth' in text
    manifest = yaml.safe_load((diagrams_dir / "rollup.manifest.yml").read_text())
    assert {"file": "01-api.md", "group": "ops"} in manifest["diagrams"]


def test_update_with_spokes_rebuilds_the_diagram(diagrams_dir):
    call("create_diagram_piece", **API_PIECE)
    call("update_diagram_piece", file="01-api.md", outputs=[{"id": "logs", "label": "Logs"}])

    text = (diagrams_dir / "01-api.md").read_text()
    assert 'hub ==>|"result"| logs' in text
    assert "auth" not in text


@pytest.mark.parametrize("tool", ["get_diagram_piece", "update_diagram_piece"])
@pytest.mark.parametrize("name", ["../../../.env", "/etc/passwd", "rollup.manifest.yml"])
def test_files_outside_the_diagrams_folder_are_refused(project, tool, name):
    (project / ".env").write_text("SECRET=1")
    is_error, text = call(tool, file=name)
    assert is_error
    assert "SECRET" not in text


def test_build_viewer_write_matches_the_cli(project):
    is_error, _ = call("build_viewer", write=True)
    assert not is_error
    assert (project / "docs/architecture_diagrams.generated.html").is_file()
    assert not (project / "docs/architecture_diagrams.html").exists()


def test_http_app_requires_the_bearer_token():
    app = mcp_server.create_http_app("s3cret")
    with TestClient(app) as client:
        assert client.post("/mcp", json={}).status_code == 401
        bad = client.post("/mcp", json={}, headers={"Authorization": "Bearer nope"})
        assert bad.status_code == 401


def test_http_mode_refuses_to_start_without_a_token(monkeypatch):
    monkeypatch.delenv(mcp_server.TOKEN_ENV, raising=False)
    monkeypatch.setattr("sys.argv", ["noit-mcp-server", "--transport", "http"])
    assert mcp_server.main() == 2
