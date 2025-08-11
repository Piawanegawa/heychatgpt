import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Any


ALLOWED_STT = {"porcupine", "sapi"}


def _load_env_file(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def _load_yaml(path: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    if not os.path.exists(path):
        return data
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip("'\"")
            if value.isdigit():
                data[key] = int(value)
            else:
                data[key] = value
    return data


@dataclass
class Settings:
    wake_word: str = "Computer"
    stt_backend: str = "porcupine"
    device_index: int = 0
    chatgpt_window_title_regex: str = "^ChatGPT$"
    audio_button_locator: str = ""
    log_level: str = "INFO"


def _validate(settings: Settings) -> Settings:
    if settings.stt_backend not in ALLOWED_STT:
        raise ValueError(f"stt_backend must be one of {ALLOWED_STT}")
    if not settings.audio_button_locator:
        raise ValueError("audio_button_locator is required")
    return settings


@lru_cache()
def get_settings(config_file: str | None = None) -> Settings:
    _load_env_file()
    cfg_path = config_file or os.environ.get("CONFIG_FILE", "config.yaml")
    data = _load_yaml(cfg_path)

    for field in Settings.__dataclass_fields__:
        env_val = os.environ.get(field.upper())
        if env_val is not None:
            if field == "device_index":
                data[field] = int(env_val)
            else:
                data[field] = env_val

    settings = Settings(**data)
    return _validate(settings)
