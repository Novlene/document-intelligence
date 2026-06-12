from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    groq_api_key: str = ""
    api_key: str = "dev-key-change-in-prod"
    secret_key: str = "dev-secret-change-in-prod"

    upload_dir: Path = Path("./uploads")
    chroma_dir: Path = Path("./chroma_db")
    pages_dir: Path = Path("./uploads/pages")
    max_file_size_mb: int = 50
    allowed_extensions: str = "pdf,png,jpg,jpeg,tiff"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    hf_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"

    class Config:
        env_file = ".env"

    @property
    def allowed_ext_list(self) -> list[str]:
        return [f".{e.strip()}" for e in self.allowed_extensions.split(",")]

    def ensure_dirs(self):
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.pages_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()