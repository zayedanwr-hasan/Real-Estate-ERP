import psycopg2
from tkinter import messagebox


def get_db_error_message(error, prefix=""):
    """Format psycopg2 errors into readable UI-safe messages."""
    parts = []
    if prefix:
        parts.append(prefix)

    if isinstance(error, psycopg2.Error):
        primary = str(getattr(error, "pgerror", "") or "").strip()
        if not primary:
            primary = str(error).strip()

        detail = str(getattr(getattr(error, "diag", None), "message_detail", "") or "").strip()
        hint = str(getattr(getattr(error, "diag", None), "message_hint", "") or "").strip()

        parts.append(primary)
        if detail:
            parts.append(f"تفاصيل: {detail}")
        if hint:
            parts.append(f"تلميح: {hint}")
    else:
        parts.append(str(error))

    return "\n".join([p for p in parts if p])


def get_connection():
    """وظيفة عالمية للاتصال بقاعدة البيانات"""
    try:
        connection = psycopg2.connect(
            user="postgres",
            password="Zayed+",  # كلمة السر الخاصة بك في pgAdmin
            host="127.0.0.1",
            port="5432",
            database="RealEstateERP"
        )
        return connection
    except Exception as error:
        messagebox.showerror("خطأ في القاعدة", get_db_error_message(error, "تعذر الاتصال بقاعدة البيانات"))
        return None