import pytest

from noit_documenting_data_flow.config import DEFAULTS, load_config


def test_defaults_without_a_config_file(tmp_path):
    assert load_config(tmp_path) == DEFAULTS


def test_config_file_overrides_only_given_keys(tmp_path):
    (tmp_path / "noit.yml").write_text("diagrams_dir: arch/diagrams\n")
    config = load_config(tmp_path)
    assert config["diagrams_dir"] == "arch/diagrams"
    assert config["out_html"] == DEFAULTS["out_html"]


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("- a\n- b\n", "must be a mapping"),
        ("diagrams_dir: [1]\n", "must be a non-empty path string"),
        ("typo_dir: x\n", "unknown setting"),
        ("a: [unclosed\n", "not valid YAML"),
    ],
)
def test_bad_config_is_a_clear_error(tmp_path, text, message):
    (tmp_path / "noit.yml").write_text(text)
    with pytest.raises(ValueError, match=message):
        load_config(tmp_path)
