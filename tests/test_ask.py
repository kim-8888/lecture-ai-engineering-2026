from types import SimpleNamespace

from app import ask as ask_module


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        text="回答",
        usage_metadata=SimpleNamespace(
            prompt_token_count=12,
            candidates_token_count=34,
        ),
    )
    chat = SimpleNamespace(send_message=lambda question: response)

    assert ask_module.ask("質問", chat) == "回答"
    assert capsys.readouterr().out == "[usage] input_tokens=12 output_tokens=34\n"


def test_main_keeps_chat_history_for_follow_up_questions(monkeypatch, capsys):
    questions = []

    def send_message(question):
        questions.append(question)
        return SimpleNamespace(text=f"{question}への回答", usage_metadata=None)

    chat = SimpleNamespace(send_message=send_message)
    monkeypatch.setattr(ask_module, "create_chat", lambda: chat)
    monkeypatch.setattr("sys.argv", ["app.ask", "最初の質問"])
    inputs = iter(["続けて質問", ""])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

    ask_module.main()

    assert questions == ["最初の質問", "続けて質問"]
    output = capsys.readouterr().out
    assert "最初の質問への回答" in output
    assert "続けて質問への回答" in output