import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from src.system.logger import setup_logger

logger = setup_logger("config_loader")
_project_root = Path(__file__).resolve().parents[2]  # solar_briefing/



class ConfigLoader:
    def __init__(self, config_dir: str | Path = None):
        # 明确加载 src/config/.env
        project_root = Path(__file__).resolve().parents[2]
        env_path = project_root / "src" / "config" / ".env"
        load_dotenv(env_path)

        self.env = os.getenv("APP_ENV", "dev")
        if config_dir is None:
            self.config_dir = project_root / "src" / "config"
        else:
            self.config_dir = Path(config_dir).resolve()

        self.config: dict = {}

    def load(self) -> dict:
        """
        Load base.yaml + environment-specific config (dev.yaml/prod.yaml).
        Replace ${VAR} placeholders with .env values.
        """
        base_path = self.config_dir / "base.yaml"
        self._merge_yaml_safe(base_path)

        env_path = self.config_dir / f"{self.env}.yaml"
        self._merge_yaml_safe(env_path)

        self._resolve_env_vars(self.config)
        return self.config

    def _merge_yaml_safe(self, path: Path):
        """
        Merge YAML file into config if it exists.
        """
        if not path.exists():
            logger.warning(f"Config file not found: {path}")
            return
        try:
            with path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                self._deep_merge(self.config, data)
                logger.info(f"Loaded config: {path}")
        except Exception as e:
            logger.error(f"Failed to load config {path}: {e}")

    def _deep_merge(self, target: dict, source: dict):
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value

    def _resolve_env_vars(self, config_dict: dict):
        """
        Replace ${VAR} placeholders with environment values.
        """
        for key, value in config_dict.items():
            if isinstance(value, dict):
                self._resolve_env_vars(value)
            elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                resolved = os.getenv(env_var)
                if resolved is None:
                    logger.warning(f"Env var {env_var} not set, keeping placeholder.")
                else:
                    config_dict[key] = resolved


# Simple wrapper function

def load_config(env: str | None = None) -> dict:
    # 如果没有传参数，就从环境变量里取
    if env is None:
        env = os.getenv("APP_ENV", "dev")

    project_root = Path(__file__).resolve().parents[2]
    base_file = project_root / "src/config/base.yaml"
    env_file = project_root / "src/config" / f"{env}.yaml"

    with open(base_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            env_config = yaml.safe_load(f)
        config.update(env_config)

    # 把相对路径转成绝对路径
    for key, rel_path in config.get("paths", {}).items():
        config["paths"][key] = str((project_root / rel_path).resolve())

    return config