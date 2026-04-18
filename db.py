
import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="Root1110z.",
        database="1220201_1220168",
        port=3306
    )


