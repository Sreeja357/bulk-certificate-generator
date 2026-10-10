import mysql.connector
from config import Config

class DatabaseConnection:
    def __init__(self):
        self.connection = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )

    def cursor(self, dictionary=False):
        return self.connection.cursor(dictionary=dictionary)

    def commit(self):
        self.connection.commit()

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()