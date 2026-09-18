import os
from pathlib import Path
from dotenv import load_dotenv
import yaml

_BASE_DIR = Path(__file__).resolve().parents[1]
_PROJECT_ROOT = (_BASE_DIR / "..").resolve()

# Load config.yaml
_config_path = _PROJECT_ROOT / "config" / "config.yaml"
if _config_path.exists():
    with open(_config_path, "r") as f:
        _config = yaml.safe_load(f)
else:
    _config = {}

# Load .env file for sensitive overrides
_env_path = _PROJECT_ROOT / "config" / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


def get(key: str, default=None):
    """Get config value, checking env var first, then config.yaml."""
    env_val = os.getenv(key)
    if env_val is not None:
        return env_val
    keys = key.split(".")
    val = _config
    for k in keys:
        if isinstance(val, dict):
            val = val.get(k)
        else:
            return default
        if val is None:
            return default
    return val


def get_database_url():
    url = get("database.url", "sqlite:///backend/data/product.db")
    if "sqlite" in url:
        db_path = url.replace("sqlite:///", "")
        if not os.path.isabs(db_path):
            project_root = os.getenv("PROJECT_ROOT", str(_PROJECT_ROOT))
            db_path = str(Path(project_root) / db_path)
        url = f"sqlite:///{db_path}"
    return url


def get_upload_dir():
    upload_dir = get("paths.uploads", "backend/data/uploads")
    if not os.path.isabs(upload_dir):
        project_root = os.getenv("PROJECT_ROOT", str(_PROJECT_ROOT))
        upload_dir = os.path.join(project_root, upload_dir)
    return upload_dir


def get_log_dir():
    log_dir = get("paths.logs", "backend/logs")
    if not os.path.isabs(log_dir):
        project_root = os.getenv("PROJECT_ROOT", str(_PROJECT_ROOT))
        log_dir = os.path.join(project_root, log_dir)
    return log_dir


def get_server_config():
    return {
        "host": get("server.host", "0.0.0.0"),
        "port": int(get("server.port", 8000)),
        "frontend_origin": get("server.frontend_origin", "http://localhost:3000"),
    }


def get_ai_config():
    return {
        "api_url": get("ai.api_url", "http://framework.gruru.net:11434/v1"),
        "api_key": os.getenv("AI_API_KEY", ""),
        "model": get("ai.model", "qwen3.6:35B"),
        "prompt": get("ai.prompt", ""),
    }


def save_ai_config(api_url: str, model: str, prompt: str):
    """Save AI configuration to config.yaml."""
    if "ai" not in _config:
        _config["ai"] = {}
    _config["ai"]["api_url"] = api_url
    _config["ai"]["model"] = model
    _config["ai"]["prompt"] = prompt
    
    with open(_config_path, "w") as f:
        yaml.dump(_config, f, default_flow_style=False, sort_keys=False)
    
    # Reload config to reflect changes
    _reload_config()


def _reload_config():
    """Reload config from disk."""
    global _config
    with open(_config_path, "r") as f:
        _config = yaml.safe_load(f) or {}


def get_full_config():
    """Return the full configuration for the frontend."""
    return {
        "database": _config.get("database", {}),
        "paths": _config.get("paths", {}),
        "server": _config.get("server", {}),
        "ai": _config.get("ai", {}),
        "image": _config.get("image", {}),
    }
