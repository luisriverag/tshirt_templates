import json
import sys
from types import SimpleNamespace

import pytest

from tshirt_templates.badges import Badge
from tshirt_templates.cli import generate_pdf_from_file, main


DEMO_BADGE = Badge(
    id="demo-badge.svg",
    name="Demo Badge",
    path="demo-badge.svg",
    raw_url="/static/demo-badge.svg",
    extension=".svg",
)


def test_generate_pdf_from_file_writes_output(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setitem(
        sys.modules,
        "tshirt_templates.pdf",
        SimpleNamespace(render_pdf=lambda *args, **kwargs: calls.append((args, kwargs)) or b"%PDF-1.4\n%%EOF"),
    )
    template = tmp_path / "template.json"
    output = tmp_path / "out" / "template.pdf"
    template.write_text(
        json.dumps(
            {
                "badge_ids": [DEMO_BADGE.id],
                "options": {"sides": ["front"], "front_text": "Ada", "include_print_marks": True},
            }
        ),
        encoding="utf-8",
    )

    content = generate_pdf_from_file(template, output)

    assert content == b"%PDF-1.4\n%%EOF"
    assert output.read_bytes() == content
    assert calls[0][1]["panel_text"]["front"] == "Ada"
    assert calls[0][1]["print_marks"] is True


def test_cli_generate_pdf_command(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr("tshirt_templates.cli.generate_pdf_from_file", lambda *args: b"%PDF")
    template = tmp_path / "template.json"
    output = tmp_path / "template.pdf"
    template.write_text("{}", encoding="utf-8")

    assert main(["generate-pdf", str(template), str(output)]) == 0

    assert "Wrote 4 bytes" in capsys.readouterr().out


def test_generate_pdf_from_file_rejects_non_object_json(tmp_path):
    template = tmp_path / "template.json"
    template.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="Template JSON must be an object"):
        generate_pdf_from_file(template, tmp_path / "template.pdf")
