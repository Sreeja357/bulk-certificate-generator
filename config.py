import os

class Config:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "your_actual_password")
    DB_NAME = os.getenv("DB_NAME", "bulk_certificate_db")