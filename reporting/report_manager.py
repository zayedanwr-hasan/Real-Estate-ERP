import os
import shutil
import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import pdfkit
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from app_constants import SYSTEM_NAME, WKHTMLTOPDF_PATH
from db_connection import get_connection, get_db_error_message


class ReportManager:
    def __init__(self, wkhtmltopdf_path: str | None = None):
        root = Path(__file__).resolve().parent
        self.template_env = Environment(
            loader=FileSystemLoader(str(root / "templates")),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=StrictUndefined,
        )
        self.wkhtmltopdf_path = self._resolve_wkhtmltopdf_path(wkhtmltopdf_path)
        self._temp_dir = os.path.join(tempfile.gettempdir(), "landledger_reporting_cache")
        os.makedirs(self._temp_dir, exist_ok=True)
        self._active_files: List[str] = []

    def _resolve_wkhtmltopdf_path(self, explicit_path: str | None) -> str:
        explicit = str(explicit_path or "").strip()
        env_path = str(os.getenv("WKHTMLTOPDF_PATH", "")).strip()
        const_path = str(WKHTMLTOPDF_PATH or "").strip()

        candidates: List[str] = [
            explicit,
            env_path,
            const_path,
            shutil.which("wkhtmltopdf") or "",
            r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
            r"C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe",
        ]

        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return candidate
        return ""

    def _pdfkit_config(self):
        if self.wkhtmltopdf_path and os.path.exists(self.wkhtmltopdf_path):
            return pdfkit.configuration(wkhtmltopdf=self.wkhtmltopdf_path)
        return None

    def cleanup_temp_files(self) -> None:
        for file_path in list(self._active_files):
            try:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass
            finally:
                if file_path in self._active_files:
                    self._active_files.remove(file_path)

    def _track_file(self, file_path: str) -> str:
        self._active_files.append(file_path)
        return file_path

    def _run_query(self, query: str, params: Sequence[Any]) -> List[Tuple[Any, ...]]:
        conn = get_connection()
        if not conn:
            raise RuntimeError("تعذر الاتصال بقاعدة البيانات")

        rows: List[Tuple[Any, ...]] = []
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(query, list(params))
                    fetched = cur.fetchall()
                    rows = list(fetched) if fetched else []
        except Exception as exc:
            raise RuntimeError(get_db_error_message(exc, "تعذر تنفيذ الاستعلام")) from exc
        finally:
            conn.close()

        return rows

    def _run_query_with_fallback(
        self,
        candidates: Sequence[Tuple[str, Sequence[Any], str]],
        fail_prefix: str,
    ) -> List[Tuple[Any, ...]]:
        last_exc: Exception | None = None
        attempts: List[str] = []

        for query, params, label in candidates:
            try:
                return self._run_query(query, params)
            except Exception as exc:
                last_exc = exc
                attempts.append(label)

        details = f"المحاولات: {', '.join(attempts)}" if attempts else ""
        message = fail_prefix if not details else f"{fail_prefix}\n{details}"
        if last_exc is not None:
            raise RuntimeError(f"{message}\n{last_exc}") from last_exc
        raise RuntimeError(message)

    @staticmethod
    def _is_int_like(value: str) -> bool:
        return str(value or "").strip().isdigit()

    @staticmethod
    def _fmt(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, (int, float, Decimal)):
            return f"{float(value):,.2f}"
        return str(value)

    @staticmethod
    def _logo_uri(path_value: str) -> str:
        token = str(path_value or "").strip()
        if not token:
            return ""
        if token.startswith("http://") or token.startswith("https://") or token.startswith("file://"):
            return token
        return Path(token).resolve().as_uri()

    def fetch_system_settings(self) -> Dict[str, str]:
        # noinspection SqlResolve
        query = """
            SELECT company_name, phone, email, address, logo_path
            FROM finance.system_settings
            ORDER BY id DESC
            LIMIT 1
        """
        rows = self._run_query(query, [])
        if not rows:
            return {
                "company_name": SYSTEM_NAME,
                "phone": "",
                "email": "",
                "address": "",
                "logo_path": "",
            }
        row = rows[0]
        return {
            "company_name": row[0] or SYSTEM_NAME,
            "phone": row[1] or "",
            "email": row[2] or "",
            "address": row[3] or "",
            "logo_path": row[4] or "",
        }

    def _resolve_account_label(self, account_code: str) -> str:
        # noinspection SqlResolve
        by_code = """
            SELECT account_code, account_name
            FROM finance.accounts
            WHERE account_code = %s
            LIMIT 1
        """

        candidates: List[Tuple[str, Sequence[Any], str]] = [(by_code, [account_code], "accounts.account_code")]
        if self._is_int_like(account_code):
            # noinspection SqlResolve
            by_id = """
                SELECT account_code, account_name
                FROM finance.accounts
                WHERE id = %s
                LIMIT 1
            """
            candidates.append((by_id, [int(account_code)], "accounts.id"))

        rows = self._run_query_with_fallback(candidates, "تعذر قراءة بيانات الحساب من finance.accounts")
        if not rows:
            return account_code
        code, name = rows[0]
        return f"{code} - {name}" if code and name else (name or code or account_code)

    def fetch_opening_balance(self, account_code: str, date_from: str) -> float:
        # noinspection SqlResolve
        q_code = """
            SELECT COALESCE(SUM(COALESCE(l.debit, 0) - COALESCE(l.credit, 0)), 0)
            FROM finance.ledger l
            WHERE l.account_code = %s
              AND l.posting_date < %s
        """

        candidates: List[Tuple[str, Sequence[Any], str]] = [(q_code, [account_code, date_from], "ledger.account_code + posting_date")]

        if self._is_int_like(account_code):
            # noinspection SqlResolve
            q_id = """
                SELECT COALESCE(SUM(COALESCE(l.debit, 0) - COALESCE(l.credit, 0)), 0)
                FROM finance.ledger l
                WHERE l.account_id = %s
                  AND l.posting_date < %s
            """
            candidates.append((q_id, [int(account_code), date_from], "ledger.account_id + posting_date"))

        rows = self._run_query_with_fallback(
            candidates,
            "تعذر احتساب الرصيد الافتتاحي من finance.ledger. تحقق من أعمدة posting_date/debit/credit/account_code.",
        )
        return float(rows[0][0] or 0.0) if rows else 0.0

    def fetch_ledger_moves(self, account_code: str, date_from: str, date_to: str) -> List[Dict[str, Any]]:
        # Preferred mapping per verified schema.
        # noinspection SqlResolve
        query_a = """
            SELECT
                COALESCE(v.v_type, '') || '-' || COALESCE(v.id::text, '') AS doc_no,
                l.posting_date,
                COALESCE(l.line_description, '') AS description,
                COALESCE(l.debit, 0) AS debit,
                COALESCE(l.credit, 0) AS credit,
                COALESCE(l.account_code::text, '') AS account_code
            FROM finance.ledger l
            LEFT JOIN finance.vouchers v ON l.voucher_id = v.id
            WHERE l.account_code = %s
              AND l.posting_date BETWEEN %s AND %s
            ORDER BY l.posting_date, v.id, l.id
        """

        # Fallback mapping if posting/date or description naming differs slightly.
        # noinspection SqlResolve
        query_b = """
            SELECT
                COALESCE(v.v_type, '') || '-' || COALESCE(v.id::text, '') AS doc_no,
                l.date,
                COALESCE(l.description, '') AS description,
                COALESCE(l.debit, 0) AS debit,
                COALESCE(l.credit, 0) AS credit,
                COALESCE(l.account_code::text, '') AS account_code
            FROM finance.ledger l
            LEFT JOIN finance.vouchers v ON l.voucher_id = v.id
            WHERE l.account_code = %s
              AND l.date BETWEEN %s AND %s
            ORDER BY l.date, v.id, l.id
        """

        candidates: List[Tuple[str, Sequence[Any], str]] = [
            (query_a, [account_code, date_from, date_to], "ledger.posting_date + line_description + account_code"),
            (query_b, [account_code, date_from, date_to], "ledger.date + description + account_code"),
        ]

        if self._is_int_like(account_code):
            # noinspection SqlResolve
            query_c = """
                SELECT
                    COALESCE(v.v_type, '') || '-' || COALESCE(v.id::text, '') AS doc_no,
                    l.posting_date,
                    COALESCE(l.line_description, '') AS description,
                    COALESCE(l.debit, 0) AS debit,
                    COALESCE(l.credit, 0) AS credit,
                    COALESCE(l.account_code::text, '') AS account_code
                FROM finance.ledger l
                LEFT JOIN finance.vouchers v ON l.voucher_id = v.id
                WHERE l.account_id = %s
                  AND l.posting_date BETWEEN %s AND %s
                ORDER BY l.posting_date, v.id, l.id
            """
            candidates.append((query_c, [int(account_code), date_from, date_to], "ledger.account_id + posting_date"))

        rows = self._run_query_with_fallback(
            candidates,
            "تعذر جلب الحركات من finance.ledger. تحقق من أعمدة posting_date/line_description/debit/credit/voucher_id/account_code.",
        )

        result: List[Dict[str, Any]] = []
        for row in rows:
            result.append(
                {
                    "doc_no": row[0] or "",
                    "date": row[1].strftime("%Y-%m-%d") if row[1] else "",
                    "description": row[2] or "",
                    "debit": float(row[3] or 0),
                    "credit": float(row[4] or 0),
                    "account_code": row[5] or "",
                }
            )
        return result

    def _statement_rows(self, moves: List[Dict[str, Any]], opening_balance: float) -> Dict[str, Any]:
        rows: List[Dict[str, Any]] = [
            {
                "date": "",
                "doc_no": "",
                "description": "الرصيد الافتتاحي",
                "debit": None,
                "credit": None,
                "balance": opening_balance,
                "row_type": "opening",
            }
        ]

        total_debit = 0.0
        total_credit = 0.0
        running_balance = opening_balance

        for move in moves:
            debit = float(move["debit"])
            credit = float(move["credit"])
            total_debit += debit
            total_credit += credit
            running_balance += debit - credit
            rows.append(
                {
                    "date": move["date"],
                    "doc_no": move["doc_no"],
                    "description": move["description"],
                    "debit": debit,
                    "credit": credit,
                    "balance": running_balance,
                    "row_type": "normal",
                }
            )

        rows.append(
            {
                "date": "",
                "doc_no": "",
                "description": "الإجمالي",
                "debit": total_debit,
                "credit": total_credit,
                "balance": running_balance,
                "row_type": "total",
            }
        )

        for row in rows:
            row["debit_text"] = self._fmt(row["debit"])
            row["credit_text"] = self._fmt(row["credit"])
            row["balance_text"] = self._fmt(row["balance"])

        return {
            "rows": rows,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "closing_balance": running_balance,
        }

    def build_context(
        self,
        account_code: str,
        account_label: str,
        date_from: str,
        date_to: str,
        posted_status: str,
        user_name: str,
    ) -> Dict[str, Any]:
        branding = self.fetch_system_settings()
        resolved_account_label = account_label or self._resolve_account_label(account_code)
        opening_balance = self.fetch_opening_balance(account_code, date_from)
        moves = self.fetch_ledger_moves(account_code, date_from, date_to)
        statement = self._statement_rows(moves, opening_balance)

        return {
            "report_title": "كشف حساب تفصيلي",
            "company_name": branding["company_name"],
            "company_phone": branding["phone"],
            "company_email": branding["email"],
            "company_address": branding["address"],
            "company_logo": branding["logo_path"],
            "company_logo_uri": self._logo_uri(branding["logo_path"]),
            "print_date": datetime.now().strftime("%Y-%m-%d"),
            "print_time": datetime.now().strftime("%H:%M:%S"),
            "user_name": user_name,
            "date_from": date_from,
            "date_to": date_to,
            "account_code": account_code,
            "account_label": resolved_account_label,
            "posted_status": posted_status,
            "rows": statement["rows"],
            "total_debit_text": self._fmt(statement["total_debit"]),
            "total_credit_text": self._fmt(statement["total_credit"]),
            "closing_balance_text": self._fmt(statement["closing_balance"]),
        }

    def render_html(self, context: Dict[str, Any]) -> str:
        template = self.template_env.get_template("account_statement.html")
        html = template.render(**context)
        html_path = self._track_file(os.path.join(self._temp_dir, f"statement_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.html"))
        with open(html_path, "w", encoding="utf-8") as handle:
            handle.write(html)
        return html

    def generate_pdf(self, html: str, output_pdf_path: str | None = None) -> str:
        target = output_pdf_path or self._track_file(os.path.join(self._temp_dir, f"statement_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.pdf"))
        options = {
            "encoding": "UTF-8",
            "page-size": "A4",
            "margin-top": "10mm",
            "margin-right": "8mm",
            "margin-bottom": "10mm",
            "margin-left": "8mm",
            "print-media-type": "",
            "enable-local-file-access": "",
            "quiet": "",
        }
        config = self._pdfkit_config()
        if config is None:
            raise RuntimeError(
                "لم يتم العثور على wkhtmltopdf.exe.\n"
                "الرجاء تثبيته أو تحديد المسار في WKHTMLTOPDF_PATH.\n"
                "رابط التحميل: https://wkhtmltopdf.org/downloads.html"
            )
        try:
            pdfkit.from_string(html, target, options=options, configuration=config)
        except OSError as exc:
            raise RuntimeError(
                "تعذر إنشاء PDF عبر wkhtmltopdf.\n"
                "تحقق من تثبيت الأداة وصلاحية المسار.\n"
                "رابط التحميل: https://wkhtmltopdf.org/downloads.html"
            ) from exc
        return target

    def generate_account_statement(
        self,
        account_code: str,
        date_from: str,
        date_to: str,
        account_label: str,
        posted_status: str,
        user_name: str,
    ) -> Dict[str, Any]:
        self.cleanup_temp_files()
        context = self.build_context(
            account_code=account_code,
            account_label=account_label,
            date_from=date_from,
            date_to=date_to,
            posted_status=posted_status,
            user_name=user_name,
        )
        html = self.render_html(context)
        pdf_path = self.generate_pdf(html)
        return {"context": context, "pdf_path": pdf_path, "html": html}

    @staticmethod
    def save_as_pdf(source_pdf: str, target_pdf: str) -> None:
        shutil.copy2(source_pdf, target_pdf)

    @staticmethod
    def export_excel(rows: List[Dict[str, Any]], target_path: str) -> None:
        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError("مكتبة pandas غير مثبتة") from exc

        export_rows = [
            {
                "التاريخ": row.get("date", ""),
                "رقم السند": row.get("doc_no", ""),
                "البيان": row.get("description", ""),
                "مدين": row.get("debit_text", ""),
                "دائن": row.get("credit_text", ""),
                "الرصيد": row.get("balance_text", ""),
            }
            for row in rows
        ]
        pd.DataFrame(export_rows).to_excel(target_path, index=False)

