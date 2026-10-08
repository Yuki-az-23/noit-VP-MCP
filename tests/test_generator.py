import pytest
import yaml

from noit_documenting_data_flow.generator import build_viewer, derive_id, parse_piece
from noit_documenting_data_flow.templates import VIEWER_TEMPLATE


@pytest.mark.parametrize(
    ("stem", "expected"),
    [("01-api-gateway", "d01_api_gateway"), ("Auth Flow", "auth_flow"), ("x--y", "x_y")],
)
def test_derive_id_is_a_valid_html_id(stem, expected):
    assert derive_id(stem) == expected


def test_parse_piece_reads_title_description_and_mermaid(tmp_path):
    piece = tmp_path / "01-x.md"
    piece.write_text("# My Title\n\nWhat it does.\n\n```mermaid\ngraph LR\n  a --> b\n```\n")
    assert parse_piece(piece) == {
        "title": "My Title",
        "desc": "What it does.",
        "mermaid": "graph LR\n  a --> b",
    }


def test_parse_piece_without_mermaid_is_an_error(tmp_path):
    piece = tmp_path / "01-x.md"
    piece.write_text("# Title\n\nNo diagram.\n")
    with pytest.raises(ValueError, match="No ```mermaid block"):
        parse_piece(piece)


def test_build_viewer_from_the_init_template(diagrams_dir):
    manifest = yaml.safe_load((diagrams_dir / "rollup.manifest.yml").read_text())
    html_out, overview = build_viewer(manifest, diagrams_dir, VIEWER_TEMPLATE)

    assert "{{" not in html_out, "every template placeholder is filled"
    assert 'id="sec-d00_template"' in html_out
    assert "['d00_template']" in html_out
    # Mermaid is HTML-escaped so <br/> survives inside the viewer
    assert "&lt;br/&gt;" in html_out
    assert "| 1 | [TEMPLATE: Your Function Name](00-template.md) |" in overview
    assert 'click d00_template "00-template.md"' in overview
