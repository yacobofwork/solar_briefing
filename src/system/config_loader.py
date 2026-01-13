import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Project root directory (two levels up from this file)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ConfigLoader:
    def __init__(self, config_dir: str | Path = None):
        """
        Initialize the configuration loader.
        Loads environment variables from src/config/.env.
        """
        env_path = _PROJECT_ROOT / "src" / "config" / ".env"
        load_dotenv(env_path)

        # Determine environment (default: dev)
        self.env = os.getenv("APP_ENV", "dev")

        # Set configuration directory
        if config_dir is None:
            self.config_dir = _PROJECT_ROOT / "src" / "config"
        else:
            self.config_dir = Path(config_dir).resolve()

        self.config: dict = {}

    def load(self) -> dict:
        """
        Load base.yaml and environment-specific config (dev.yaml/prod.yaml).
        Resolve environment variables and convert relative paths to absolute.
        """
        base_path = self.config_dir / "base.yaml"
        self._merge_yaml_safe(base_path)

        env_path = self.config_dir / f"{self.env}.yaml"
        self._merge_yaml_safe(env_path)

        self._resolve_env_vars(self.config)
        self._resolve_paths(self.config)
        return self.config

    def _merge_yaml_safe(self, path: Path):
        """
        Merge YAML file into config if it exists.
        """
        if not path.exists():
            print(f"[WARN] Config file not found: {path}")
            return
        try:
            with path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                self._deep_merge(self.config, data)
            print(f"[INFO] Loaded config: {path}")
        except Exception as e:
            print(f"[ERROR] Failed to load config {path}: {e}")

    def _deep_merge(self, target: dict, source: dict):
        """
        Recursively merge source dict into target dict.
        """
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value

    def _resolve_env_vars(self, config_dict: dict):
        """
        Replace ${VAR} placeholders with environment variable values.
        """
        for key, value in config_dict.items():
            if isinstance(value, dict):
                self._resolve_env_vars(value)
            elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                resolved = os.getenv(env_var)
                if resolved is None:
                    print(f"[WARN] Env var {env_var} not set, keeping placeholder.")
                else:
                    config_dict[key] = resolved

    def _resolve_paths(self, config_dict: dict):
        """
        Convert relative paths under 'paths' to absolute paths.
        """
        if "paths" in config_dict:
            for key, rel_path in config_dict["paths"].items():
                config_dict["paths"][key] = str((_PROJECT_ROOT / rel_path).resolve())


# Simple wrapper function
def load_config(env: str | None = None) -> dict:
    """
    Convenience function to load configuration directly.
    """
    if env is None:
        env = os.getenv("APP_ENV", "dev")

    loader = ConfigLoader()
    loader.env = env
    return loader.load()