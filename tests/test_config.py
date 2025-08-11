import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config import get_settings  # type: ignore


def test_env_overrides_yaml(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        """
        wake_word: Computer
        stt_backend: porcupine
        device_index: 1
        audio_button_locator: locator
        """
    )
    monkeypatch.setenv("CONFIG_FILE", str(cfg))
    monkeypatch.setenv("WAKE_WORD", "Jarvis")

    get_settings.cache_clear()
    settings = get_settings()

    assert settings.wake_word == "Jarvis"
    assert settings.device_index == 1
    assert settings.log_level == "INFO"
