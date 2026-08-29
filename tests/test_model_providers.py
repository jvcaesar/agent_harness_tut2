import os

from harness.model import build_model_from_env, describe_active_model, end_turn


def test_build_model_from_env_prefers_ollama_when_enabled(monkeypatch):
    monkeypatch.setenv("OLLAMA_ENABLED", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    model = build_model_from_env()
    assert model.__class__.__name__ == "OllamaModel"


def test_build_model_from_env_uses_openai_when_key_is_present(monkeypatch):
    monkeypatch.setenv("OLLAMA_ENABLED", "false")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    model = build_model_from_env()
    assert model.__class__.__name__ == "OpenAIModel"


def test_build_model_from_env_loads_dotenv_file(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("OLLAMA_ENABLED=true\nOLLAMA_MODEL=llama3.2\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OLLAMA_ENABLED", raising=False)
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    model = build_model_from_env()

    assert model.__class__.__name__ == "OllamaModel"
    assert model.model == "llama3.2"


def test_model_contract_helpers_return_expected_shapes():
    assert end_turn("done") == {"stop_reason": "end_turn", "text": "done"}


def test_describe_active_model_reports_selected_provider(monkeypatch):
    monkeypatch.setenv("OLLAMA_ENABLED", "true")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    assert describe_active_model() == "OllamaModel (llama3.2)"
