from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Assistente RAG para Assistencia Tecnica"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    base_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2])
    raw_data_dir: Path = Field(default=Path("data/raw"))
    sample_data_dir: Path = Field(default=Path("data/samples"))
    vector_store_dir: Path = Field(default=Path("data/vector_store"))

    chroma_collection: str = "clinic_procedure_docs"
    embedding_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    chunk_size: int = 900
    chunk_overlap: int = 150
    top_k: int = 4

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    llm_temperature: float = 0.1
    llm_timeout_seconds: int = 120
    llm_num_ctx: int | None = 2048
    llm_num_predict: int | None = 350
    llm_num_gpu: int | None = None

    whatsapp_verify_token: str | None = None
    whatsapp_access_token: str | None = None
    whatsapp_phone_number_id: str | None = None
    whatsapp_graph_api_version: str = "v20.0"
    whatsapp_app_secret: str | None = None
    whatsapp_provider: str = "chatpro"
    chatpro_base_url: str = "https://v5.chatpro.com.br"
    chatpro_instance_id: str | None = None
    chatpro_token: str | None = None
    chatpro_respond_from_me: bool = False
    chatpro_bot_prefix: str = "Assistente:"
    assistant_command_trigger: str = "!bot"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator(
        "llm_num_ctx",
        "llm_num_predict",
        "llm_num_gpu",
        "whatsapp_verify_token",
        "whatsapp_access_token",
        "whatsapp_phone_number_id",
        "whatsapp_app_secret",
        "chatpro_instance_id",
        "chatpro_token",
        mode="before",
    )
    @classmethod
    def empty_string_as_none(cls, value: object) -> object:
        return None if value == "" else value

    def model_post_init(self, __context: object) -> None:
        self.raw_data_dir = self._resolve_path(self.raw_data_dir)
        self.sample_data_dir = self._resolve_path(self.sample_data_dir)
        self.vector_store_dir = self._resolve_path(self.vector_store_dir)

    def _resolve_path(self, path: Path) -> Path:
        return path if path.is_absolute() else self.base_dir / path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
