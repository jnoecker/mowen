"""Application configuration via environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Mowen server settings.

    All values can be overridden with ``MOWEN_`` prefixed environment
    variables (e.g. ``MOWEN_DATABASE_URL``, ``MOWEN_HOST``).
    """

    database_url: str = "sqlite:///{home}/.mowen/data.db"
    upload_dir: Path = Path("~/.mowen/documents")
    host: str = "127.0.0.1"
    port: int = 8000
    max_upload_bytes: int = 50 * 1024 * 1024  # 50 MB
    cors_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(env_prefix="MOWEN_")

    @model_validator(mode="after")
    def _expand_paths(self) -> "Settings":
        # Expand ~ in upload_dir
        self.upload_dir = self.upload_dir.expanduser().resolve()

        # Expand ~ placeholder in database_url
        home = str(Path.home())
        if "{home}" in self.database_url:
            self.database_url = self.database_url.replace("{home}", home)
        elif self.database_url.startswith("sqlite:///~/"):
            # Only expand ~ at the start of the path, not in the middle
            self.database_url = "sqlite:///" + home + self.database_url[len("sqlite:///~"):]

        # Ensure the database parent directory exists
        if self.database_url.startswith("sqlite:///"):
            db_path = Path(self.database_url[len("sqlite:///"):])
            db_path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure the upload directory exists
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton :class:`Settings` instance."""
    return Settings()
