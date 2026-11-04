import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

try:
    connection = psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=5,
    )

    print("Connected to the PharmVault database successfully!")
    connection.close()

except Exception as error:
    print("Database connection failed:", error)