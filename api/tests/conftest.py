import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://catalog:catalog@127.0.0.1:5432/catalog",
)
os.environ.setdefault("APP_ENV", "local")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("SESSION_SECRET", "test-only-secret")
