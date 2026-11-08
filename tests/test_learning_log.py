"""第3回 宿題（実装）: save_learning_log と承認（requires_approval=True）のテスト。

TestModel を使うので、APIキーも利用枠も使わない。
保存先は pytest の一時フォルダ（tmp_path）に差し替え、本物の learning_log/ には書かない。
"""

import pytest
from pydantic_ai import DeferredToolRequests
from pydantic_ai.messages import ToolReturnPart
from pydantic_ai.models.test import TestModel

from app import tools
from app.agent import agent, resolve_approvals


@pytest.fixture
def log_dir(tmp_path, monkeypatch):
    path = tmp_path / "learning_log"
    monkeypatch.setattr(tools, "LOG_DIR", path)
    return path


def _saved_files(log_dir):
    return list(log_dir.glob("*.md")) if log_dir.exists() else []


def test_save_learning_log_writes_markdown(log_dir):
    message = tools.save_learning_log("LoRAとQLoRA", "- QLoRA は量子化したモデルに LoRA を使う")
    files = _saved_files(log_dir)
    assert len(files) == 1
    assert "保存しました" in message
    text = files[0].read_text(encoding="utf-8")
    assert text.startswith("# LoRAとQLoRA")
    assert "QLoRA は量子化したモデルに LoRA を使う" in text


def test_save_learning_log_makes_safe_file_name(log_dir):
    tools.save_learning_log("a/b:c?", "本文")
    (path,) = _saved_files(log_dir)
    assert path.parent == log_dir  # / が入っても別フォルダに書かない
    assert "/" not in path.name and ":" not in path.name


def test_save_learning_log_rejects_empty_input(log_dir):
    assert "指定してください" in tools.save_learning_log("", "本文")
    assert "指定してください" in tools.save_learning_log("題名", "  ")
    assert _saved_files(log_dir) == []


def test_tool_waits_for_approval_and_does_not_save(log_dir):
    """モデルが save_learning_log を呼んでも、承認されるまでは実行されない。"""
    with agent.override(model=TestModel(call_tools=["save_learning_log"])):
        result = agent.run_sync("今日の学習を記録して")
    assert isinstance(result.output, DeferredToolRequests)
    assert [c.tool_name for c in result.output.approvals] == ["save_learning_log"]
    assert _saved_files(log_dir) == []


def test_approved_call_saves_the_log(log_dir):
    model = TestModel(call_tools=["save_learning_log"])
    with agent.override(model=model):
        first = agent.run_sync("今日の学習を記録して")
        result = resolve_approvals(agent, first, model, approve=lambda call: True)
    assert isinstance(result.output, str)
    assert len(_saved_files(log_dir)) == 1
    returns = [p for m in result.all_messages() for p in m.parts if isinstance(p, ToolReturnPart)]
    assert any("保存しました" in str(p.content) for p in returns)


def test_denied_call_does_not_save(log_dir):
    model = TestModel(call_tools=["save_learning_log"])
    with agent.override(model=model):
        first = agent.run_sync("今日の学習を記録して")
        result = resolve_approvals(agent, first, model, approve=lambda call: False)
    assert isinstance(result.output, str)
    assert _saved_files(log_dir) == []
    returns = [p for m in result.all_messages() for p in m.parts if isinstance(p, ToolReturnPart)]
    assert any("許可しませんでした" in str(p.content) for p in returns)
