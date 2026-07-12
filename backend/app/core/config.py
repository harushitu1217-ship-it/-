from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="MINGJING_", extra="ignore")

    database_url: str = f"sqlite:///{(PROJECT_ROOT / 'data' / 'mingjing.db').as_posix()}"
    jwt_secret: str = "development-only-change-me"
    upload_dir: Path = PROJECT_ROOT / "data" / "uploads"

    def ensure_local_directories(self) -> None:
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        prefix = "sqlite:///"
        if self.database_url.startswith(prefix) and self.database_url != "sqlite:///:memory:":
            Path(self.database_url.removeprefix(prefix)).parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_local_directories()
    return settings
