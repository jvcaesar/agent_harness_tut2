from harness import Harness
from harness.model import DummyModel, OllamaModel, end_turn
from agent import format_model_error, run_interactive_chat


def test_interactive_chat_prints_response_and_exits(tmp_path):
    inputs = iter(["Hello", "quit"])
    output: list[str] = []
    model = DummyModel(policy=lambda *_: end_turn("Hello, human."))
    harness = Harness(model=model, cwd=tmp_path)

    run_interactive_chat(harness, input_fn=lambda _: next(inputs), output_fn=output.append)

    assert output == ["AI> Hello, human.", "Goodbye."]
    assert model.calls == 1


def test_interactive_chat_exits_on_end_of_input(tmp_path):
    output: list[str] = []
    harness = Harness(model=DummyModel(), cwd=tmp_path)

    def end_input(_: str) -> str:
        raise EOFError

    run_interactive_chat(harness, input_fn=end_input, output_fn=output.append)

    assert output == ["Goodbye."]


def test_interactive_chat_formats_and_persists_model_errors(tmp_path):
    inputs = iter(["Hello", "exit"])
    output: list[str] = []
    model = DummyModel(policy=lambda *_: (_ for _ in ()).throw(RuntimeError("sk-secret connection refused")))
    harness = Harness(model=model, cwd=tmp_path)

    run_interactive_chat(harness, input_fn=lambda _: next(inputs), output_fn=output.append)

    assert output == ["AI response failed unexpectedly. Try again, or set HARNESS_DEBUG=true to see diagnostic details.", "Goodbye."]
    event = harness.persistence.replay()[0]
    assert event["event"] == "model_error"
    assert "sk-secret" not in event["detail"]


def test_format_model_error_explains_ollama_connection_failure():
    model = OllamaModel(model="llama3.1", base_url="http://localhost:11434")

    message = format_model_error(RuntimeError("connection refused"), model)

    assert message == "AI is unavailable: Ollama could not be reached at http://localhost:11434. Start Ollama with `ollama serve`, then try again."