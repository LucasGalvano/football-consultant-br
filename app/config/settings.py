from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = ""
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    
    # MongoDB
    MONGO_USER: str = ""
    MONGO_PASSWORD: str = ""
    MONGO_URI: str = ""
    MONGO_DB: str = ""
    
    # AstraDB
    ASTRA_DB_SECURE_BUNDLE_PATH: str = ""
    ASTRA_DB_TOKEN_PATH: str = ""
    ASTRA_DB_KEYSPACE: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()