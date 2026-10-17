"""A tool that returns a picture ([text, Image]) must not be annotated ``-> str``: the MCP
output check then refuses every result that worked (Oct 17 2026: every viewport screenshot)."""

from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parent / "__init__.py"


def _returns_image(fn: ast.FunctionDef) -> bool:
    for node in ast.walk(fn):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.List):
            for elt in node.value.elts:
                if isinstance(elt, ast.Call) and getattr(elt.func, "id", "") == "Image":
                    return True
    return False


def test_picture_tools_are_not_annotated_as_str() -> None:
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    picture_tools = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and _returns_image(n)]
    assert any(n.name == "blender_get_viewport_screenshot" for n in picture_tools)
    for fn in picture_tools:
        assert not (isinstance(fn.returns, ast.Name) and fn.returns.id == "str"), fn.name
