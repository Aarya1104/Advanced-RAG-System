from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Load .env file in the parent directory
    model_config = SettingsConfigDict(
        env_file='../.env', env_file_encoding='utf-8')

    GOOGLE_API_KEY: str
    COHERE_API_KEY: str
    QDRANT_URL: str
    QDRANT_API_KEY: str
    QDRANT_COLLECTION_NAME: str = "mini-rag-collection"


settings = Settings()
