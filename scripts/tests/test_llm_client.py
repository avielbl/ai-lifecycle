"""Unit tests for llm_client.py — all LLM calls are mocked.

anthropic and openai are NOT installed in the test environment on purpose —
they are optional dependencies installed per-project via uv.
We inject stub modules into sys.modules before importing llm_client so that
the lazy-import blocks in _build_client() pick up the stubs.
"""

import sys
import os
import importlib
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Stub out anthropic and openai BEFORE importing llm_client
# ---------------------------------------------------------------------------
_mock_anthropic_module = MagicMock()
_mock_openai_module = MagicMock()
sys.modules.setdefault("anthropic", _mock_anthropic_module)
sys.modules.setdefault("openai", _mock_openai_module)

sys.path.insert(0, str(Path(__file__).parent.parent))
import llm_client as lc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cfg(provider="anthropic", model="claude-sonnet-4-6", base_url=None, api_key_env="TEST_KEY"):
    return {
        "provider": provider,
        "model": model,
        "base_url": base_url,
        "api_key_env": api_key_env,
        "max_tokens": 256,
        "temperature": 0.0,
    }


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def test_load_config_from_file(tmp_path):
    cfg_file = tmp_path / "llm_config.yaml"
    cfg_file.write_text(
        "provider: openai-compatible\n"
        "model: gpt-4o\n"
        "base_url: http://localhost:11434/v1\n"
        "api_key_env: OPENAI_API_KEY\n"
        "max_tokens: 4096\n"
        "temperature: 0.2\n"
    )
    cfg = lc.load_config(str(cfg_file))

    assert cfg["provider"] == "openai-compatible"
    assert cfg["model"] == "gpt-4o"
    assert cfg["base_url"] == "http://localhost:11434/v1"
    assert cfg["max_tokens"] == 4096
    assert cfg["temperature"] == 0.2


def test_load_config_defaults_when_missing():
    cfg = lc.load_config("/nonexistent/path.yaml")

    assert cfg["provider"] == "anthropic"
    assert cfg["model"] == "claude-sonnet-4-6"
    assert cfg["base_url"] is None
    assert cfg["api_key_env"] == "ANTHROPIC_API_KEY"
    assert cfg["max_tokens"] == 8192
    assert cfg["temperature"] == 0.0


def test_load_config_env_var_overrides(monkeypatch):
    monkeypatch.setenv("BMAD_LLM_PROVIDER", "openai-compatible")
    monkeypatch.setenv("BMAD_LLM_MODEL", "llama3:70b")
    monkeypatch.setenv("BMAD_LLM_BASE_URL", "http://localhost:11434/v1")

    cfg = lc.load_config("/nonexistent/path.yaml")

    assert cfg["provider"] == "openai-compatible"
    assert cfg["model"] == "llama3:70b"
    assert cfg["base_url"] == "http://localhost:11434/v1"


# ---------------------------------------------------------------------------
# Missing API key
# ---------------------------------------------------------------------------

def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("TEST_KEY", raising=False)
    with pytest.raises(EnvironmentError, match="TEST_KEY"):
        lc.LLMClient(config=_make_cfg())


# ---------------------------------------------------------------------------
# Anthropic calls
# ---------------------------------------------------------------------------

def _make_anthropic_instance(response_text: str) -> MagicMock:
    """Return a mock Anthropic client instance wired to return response_text."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=response_text)]
    instance = MagicMock()
    instance.messages.create.return_value = mock_response
    return instance


def _make_openai_instance(response_text: str) -> MagicMock:
    """Return a mock OpenAI client instance wired to return response_text."""
    mock_choice = MagicMock()
    mock_choice.message.content = response_text
    instance = MagicMock()
    instance.chat.completions.create.return_value = MagicMock(choices=[mock_choice])
    return instance


def test_anthropic_chat_string_message(monkeypatch):
    monkeypatch.setenv("TEST_KEY", "sk-test")
    instance = _make_anthropic_instance("Hello from Claude")
    _mock_anthropic_module.Anthropic.return_value = instance

    client = lc.LLMClient(config=_make_cfg())
    result = client.chat("Say hello")

    assert result == "Hello from Claude"
    call_kwargs = instance.messages.create.call_args.kwargs
    assert call_kwargs["messages"] == [{"role": "user", "content": "Say hello"}]
    assert "system" not in call_kwargs


def test_anthropic_chat_with_system(monkeypatch):
    monkeypatch.setenv("TEST_KEY", "sk-test")
    instance = _make_anthropic_instance("Result")
    _mock_anthropic_module.Anthropic.return_value = instance

    client = lc.LLMClient(config=_make_cfg())
    client.chat("Analyse this", system="You are a data scientist.")

    call_kwargs = instance.messages.create.call_args.kwargs
    assert call_kwargs["system"] == "You are a data scientist."


def test_anthropic_per_call_overrides(monkeypatch):
    monkeypatch.setenv("TEST_KEY", "sk-test")
    instance = _make_anthropic_instance("ok")
    _mock_anthropic_module.Anthropic.return_value = instance

    client = lc.LLMClient(config=_make_cfg())
    client.chat("test", max_tokens=512, temperature=0.5)

    call_kwargs = instance.messages.create.call_args.kwargs
    assert call_kwargs["max_tokens"] == 512
    assert call_kwargs["temperature"] == 0.5


# ---------------------------------------------------------------------------
# OpenAI-compatible calls
# ---------------------------------------------------------------------------

def test_openai_compatible_chat(monkeypatch):
    monkeypatch.setenv("TEST_KEY", "sk-test")
    instance = _make_openai_instance("Response from Ollama")
    _mock_openai_module.OpenAI.return_value = instance

    cfg = _make_cfg(provider="openai-compatible", model="llama3:70b",
                    base_url="http://localhost:11434/v1")
    client = lc.LLMClient(config=cfg)
    result = client.chat("Hello")

    assert result == "Response from Ollama"


def test_openai_compatible_system_prepended(monkeypatch):
    monkeypatch.setenv("TEST_KEY", "sk-test")
    instance = _make_openai_instance("ok")
    _mock_openai_module.OpenAI.return_value = instance

    cfg = _make_cfg(provider="openai-compatible", model="gpt-4o")
    client = lc.LLMClient(config=cfg)
    client.chat("What is F1?", system="You are an ML expert.")

    messages_sent = instance.chat.completions.create.call_args.kwargs["messages"]
    assert messages_sent[0] == {"role": "system", "content": "You are an ML expert."}
    assert messages_sent[1] == {"role": "user", "content": "What is F1?"}


def test_openai_compatible_base_url_passed(monkeypatch):
    monkeypatch.setenv("TEST_KEY", "sk-test")
    _mock_openai_module.OpenAI.reset_mock()
    _mock_openai_module.OpenAI.return_value = _make_openai_instance("ok")

    cfg = _make_cfg(provider="openai-compatible", base_url="http://myserver:8000/v1")
    lc.LLMClient(config=cfg)

    _, kwargs = _mock_openai_module.OpenAI.call_args
    assert kwargs.get("base_url") == "http://myserver:8000/v1"
