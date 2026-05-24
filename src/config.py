import os
from pathlib import Path
import yaml
from dotenv import load_dotenv

load_dotenv()

_CONFIG_PATH = Path(__file__).parent.parent / "config" / "settings.yaml"

_DEFAULTS = {
    "searches": [],
    "filters": {
        "price": {"min": 0, "max": 999999},
        "max_age_days": None,
        "exclude_keywords": [],
        "seller_type": "all",
        "location": None,
    },
    "features": {
        "notifications": {
            "email": False,
            "email_config": {},
            "discord": False,
            "discord_webhook": None,
        },
        "output": {"csv": True, "json": False, "sqlite": False},
    },
    "http": {
        "request_delay": 2.0,
        "timeout": 10,
        "max_retries": 3,
        "proxies": [],
    },
    "scheduling": {
        "interval_seconds": 900,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load(path: Path = _CONFIG_PATH) -> dict:
    with open(path) as f:
        user_config = yaml.safe_load(f) or {}
    config = _deep_merge(_DEFAULTS, user_config)
    _validate(config)
    return config


def _validate(config: dict) -> None:
    if not config["searches"]:
        raise ValueError("config: at least one search must be defined under 'searches'")

    for i, search in enumerate(config["searches"]):
        url = search.get("url", "")
        if not url.startswith(("http://", "https://")):
            raise ValueError(f"config: searches[{i}].url is missing or not a valid HTTP URL: {url!r}")

    price = config["filters"]["price"]
    if price["min"] < 0 or price["max"] < 0:
        raise ValueError("config: price min/max must be non-negative")
    if price["min"] > price["max"]:
        raise ValueError("config: price min must not exceed price max")

    max_age = config["filters"].get("max_age_days")
    if max_age is not None and max_age <= 0:
        raise ValueError("config: max_age_days must be a positive number")

    seller_type = config["filters"]["seller_type"]
    if seller_type not in ("private", "dealer", "all"):
        raise ValueError(f"config: seller_type must be 'private', 'dealer', or 'all', got '{seller_type}'")

    http = config["http"]
    if http["request_delay"] < 0:
        raise ValueError("config: request_delay must be non-negative")
    if http["max_retries"] < 0:
        raise ValueError("config: max_retries must be non-negative")
    if http["timeout"] <= 0:
        raise ValueError("config: http.timeout must be positive")

    interval = config["scheduling"]["interval_seconds"]
    if interval <= 0:
        raise ValueError("config: scheduling.interval_seconds must be positive")
