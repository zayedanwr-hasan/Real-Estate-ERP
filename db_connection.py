import psycopg2
from tkinter import messagebox

def get_connection():
    """وظيفة عالمية للاتصال بقاعدة البيانات"""
    try:
        connection = psycopg2.connect(
            user="postgres",
            password="Zayed+", # كلمة السر الخاصة بك في pgAdmin
            host="127.0.0.1",
            port="5432",
            database="RealEstateERP"
        )
        return connection
    except Exception as error:
        messagebox.showerror("خطأ في القاعدة", f"تعذر الاتصال بقاعدة البيانات: {error}")
        return None