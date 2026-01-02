"""配置数据模型和文件管理。"""

from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
import yaml
import os


@dataclass
class OpenAlexConfig:
    """OpenAlex API 配置。"""
    email: Optional[str] = None


@dataclass
class LLMConfig:
    """LLM 配置。"""
    provider: Optional[str] = None  # gemini, openai, deepseek, ollama
    api_key: Optional[str] = None
    model: Optional[str] = None

    def get_default_model(self) -> str:
        """获取默认模型名称。"""
        defaults = {
            "gemini": "gemini-1.5-pro",
            "openai": "gpt-4",
            "deepseek": "deepseek-chat",
            "ollama": "llama2",
        }
        return defaults.get(self.provider or "", "gemini-1.5-pro")


@dataclass
class DatabaseConfig:
    """数据库配置。"""
    host: Optional[str] = None
    port: Optional[int] = None
    user: Optional[str] = None
    password: Optional[str] = None


@dataclass
class DownloadConfig:
    """下载配置。"""
    directory: Optional[str] = None


@dataclass
class Config:
    """主配置类。"""
    openalex: OpenAlexConfig = field(default_factory=OpenAlexConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    download: DownloadConfig = field(default_factory=DownloadConfig)


class ConfigManager:
    """配置管理器。"""

    CONFIG_FILENAME = "config.yaml"

    def __init__(self) -> None:
        """初始化配置管理器。"""
        self.config_path = self._get_config_path()

    def _get_config_path(self) -> Path:
        """
        获取配置文件的路径。

        优先级:
        1. 环境变量 ACM_CONFIG_PATH
        2. ~/.config/acm-scholar/config.yaml
        3. ./config.yaml
        """
        env_path = os.environ.get("ACM_CONFIG_PATH")
        if env_path:
            return Path(env_path)

        xdg_config = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
        config_dir = Path(xdg_config) / "acm-scholar"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / self.CONFIG_FILENAME

    def load(self) -> Optional[Config]:
        """
        加载配置文件。

        Returns:
            Config 对象，如果配置文件不存在则返回 None
        """
        if not self.config_path.exists():
            return None

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            return self._dict_to_config(data)
        except Exception:
            return None

    def _dict_to_config(self, data: dict) -> Config:
        """
        将字典转换为 Config 对象。

        Args:
            data: 配置字典

        Returns:
            Config 对象
        """
        config = Config()

        if "openalex" in data:
            config.openalex = OpenAlexConfig(**data["openalex"])

        if "llm" in data:
            config.llm = LLMConfig(**data["llm"])

        if "database" in data:
            config.database = DatabaseConfig(**data["database"])

        if "download" in data:
            config.download = DownloadConfig(**data["download"])

        return config

    def save(self, config: Config) -> None:
        """
        保存配置到文件。

        Args:
            config: Config 对象
        """
        data = self._config_to_dict(config)

        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    def _config_to_dict(self, config: Config) -> dict:
        """
        将 Config 对象转换为字典。

        Args:
            config: Config 对象

        Returns:
            配置字典
        """
        return {
            "openalex": {
                "email": config.openalex.email,
            },
            "llm": {
                "provider": config.llm.provider,
                "api_key": config.llm.api_key,
                "model": config.llm.model,
            },
            "database": {
                "host": config.database.host,
                "port": config.database.port,
                "user": config.database.user,
                "password": config.database.password,
            },
            "download": {
                "directory": config.download.directory,
            },
        }

    def get_download_dir(self) -> Path:
        """
        获取下载目录路径。

        Returns:
            Path 对象
        """
        config = self.load()
        download_dir = config.download.directory if config else "~/acm-papers/"
        path = Path(download_dir).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        return path
