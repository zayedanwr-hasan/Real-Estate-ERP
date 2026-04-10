import os
import shutil
import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple, cast

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

    # ---------- Infrastructure ----------

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
                    fetched = cur.fetchall() or []
                    rows = list(fetched)
        except Exception as exc:
            raise RuntimeError(get_db_error_message(exc, "تعذر تنفيذ الاستعلام")) from exc
        finally:
            conn.close()

        return cast(List[Tuple[Any, ...]], rows)

    def _run_query_with_fallback(self, candidates: Sequence[Tuple[str, Sequence[Any], str]], fail_prefix: str) -> List[Tuple[Any, ...]]:
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

    def _table_has_column(self, table_name: str, column_name: str) -> bool:
        rows = self._run_query(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'finance' AND table_name = %s AND column_name = %s
            LIMIT 1
            """,
            [table_name, column_name],
        )
        return bool(rows)

    def _ledger_date_column(self) -> str:
        return "posting_date" if self._table_has_column("ledger", "posting_date") else "date"

    def _ledger_description_column(self) -> str:
        return "line_description" if self._table_has_column("ledger", "line_description") else "description"

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

    # ---------- Lookups ----------

    def fetch_system_settings(self) -> Dict[str, str]:
        rows = self._run_query(
            """
            SELECT company_name, phone, email, address, logo_path
            FROM finance.system_settings
            ORDER BY id DESC
            LIMIT 1
            """,
            [],
        )
        if not rows:
            return {"company_name": SYSTEM_NAME, "phone": "", "email": "", "address": "", "logo_path": ""}
        row = rows[0]
        return {
            "company_name": row[0] or SYSTEM_NAME,
            "phone": row[1] or "",
            "email": row[2] or "",
            "address": row[3] or "",
            "logo_path": row[4] or "",
        }

    def fetch_accounts_for_picker(self) -> List[str]:
        rows = self._run_query(
            "SELECT account_code, account_name FROM finance.accounts ORDER BY account_code",
            [],
        )
        return [f"{row[0]} - {row[1]}" for row in rows if row and row[0]]

    def fetch_properties_for_picker(self) -> List[str]:
        rows = self._run_query(
            "SELECT id, property_name FROM finance.properties ORDER BY property_name",
            [],
        )
        return [f"{row[0]} - {row[1]}" for row in rows if row and row[0] is not None]

    def fetch_funds_for_picker(self) -> List[str]:
        rows = self._run_query(
            """
            SELECT account_code, account_name
            FROM finance.accounts
            WHERE TRIM(account_code) = '1101' OR TRIM(parent_code) = '1101' OR TRIM(account_code) LIKE '1101%'
            ORDER BY account_code
            """,
            [],
        )
        return [f"{row[0]} - {row[1]}" for row in rows if row and row[0]]

    def _resolve_account_label(self, account_code: str) -> str:
        by_code = """
            SELECT account_code, account_name
            FROM finance.accounts
            WHERE account_code = %s
            LIMIT 1
        """

        candidates: List[Tuple[str, Sequence[Any], str]] = [(by_code, [account_code], "accounts.account_code")]
        if self._is_int_like(account_code):
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

    # ---------- Dynamic Config ----------

    def get_available_report_types(self) -> List[str]:
        return [
            "كشف حساب تفصيلي",
            "أرصدة الموردين",
            "أرصدة العملاء",
            "كشف حركة صندوق",
            "ملخص حركة الصناديق",
            "حالة العقارات (الأراضي)",
            "إيرادات ومصروفات عقار",
            "طباعة دليل الحسابات",
            "ميزان المراجعة",
            "دفتر اليومية العامة",
        ]

    def get_report_config(self, report_type: str) -> Dict[str, Any]:
        mapping: Dict[str, Dict[str, Any]] = {
            "كشف حساب تفصيلي": {
                "builder": self._build_account_statement_report,
                "required_filters": ["account_code", "date_from", "date_to", "posted_status"],
                "title": "كشف حساب تفصيلي",
            },
            "أرصدة الموردين": {
                "builder": self._build_vendor_balances_report,
                "required_filters": ["date_from", "date_to"],
                "title": "أرصدة الموردين",
            },
            "أرصدة العملاء": {
                "builder": self._build_customer_balances_report,
                "required_filters": ["date_from", "date_to"],
                "title": "أرصدة العملاء",
            },
            "كشف حركة صندوق": {
                "builder": self._build_fund_movement_report,
                "required_filters": ["date_from", "date_to", "fund_code"],
                "title": "كشف حركة صندوق",
            },
            "ملخص حركة الصناديق": {
                "builder": self._build_funds_summary_report,
                "required_filters": ["date_from", "date_to"],
                "title": "ملخص حركة الصناديق",
            },
            "حالة العقارات (الأراضي)": {
                "builder": self._build_property_status_report,
                "required_filters": [],
                "title": "حالة العقارات (الأراضي)",
            },
            "إيرادات ومصروفات عقار": {
                "builder": self._build_property_revenue_expense_report,
                "required_filters": ["date_from", "date_to", "property_id"],
                "title": "إيرادات ومصروفات عقار",
            },
            "طباعة دليل الحسابات": {
                "builder": self._build_chart_of_accounts_report,
                "required_filters": [],
                "title": "طباعة دليل الحسابات",
            },
            "ميزان المراجعة": {
                "builder": self._build_trial_balance_report,
                "required_filters": ["date_from", "date_to"],
                "title": "ميزان المراجعة",
            },
            "دفتر اليومية العامة": {
                "builder": self._build_general_journal_report,
                "required_filters": ["date_from", "date_to"],
                "title": "دفتر اليومية العامة",
            },
        }
        if report_type not in mapping:
            raise RuntimeError(f"نوع التقرير غير مدعوم: {report_type}")
        return mapping[report_type]

    # ---------- Core Builders ----------

    def fetch_opening_balance(self, account_code: str, date_from: str) -> float:
        q_code = """
            SELECT COALESCE(SUM(COALESCE(l.debit, 0) - COALESCE(l.credit, 0)), 0)
            FROM finance.ledger l
            WHERE l.account_code = %s
              AND l.{date_col} < %s
        """.format(date_col=self._ledger_date_column())

        candidates: List[Tuple[str, Sequence[Any], str]] = [(q_code, [account_code, date_from], "ledger.account_code")]

        if self._is_int_like(account_code):
            q_id = """
                SELECT COALESCE(SUM(COALESCE(l.debit, 0) - COALESCE(l.credit, 0)), 0)
                FROM finance.ledger l
                WHERE l.account_id = %s
                  AND l.{date_col} < %s
            """.format(date_col=self._ledger_date_column())
            candidates.append((q_id, [int(account_code), date_from], "ledger.account_id"))

        rows = self._run_query_with_fallback(candidates, "تعذر احتساب الرصيد الافتتاحي من finance.ledger")
        return float(rows[0][0] or 0.0) if rows else 0.0

    def fetch_ledger_moves(self, account_code: str, date_from: str, date_to: str) -> List[Dict[str, Any]]:
        date_col = self._ledger_date_column()
        desc_col = self._ledger_description_column()
        query = f"""
            SELECT
                COALESCE(v.v_type, '') || '-' || COALESCE(v.id::text, '') AS doc_no,
                l.{date_col} AS row_date,
                COALESCE(l.{desc_col}, '') AS description,
                COALESCE(l.debit, 0) AS debit,
                COALESCE(l.credit, 0) AS credit,
                COALESCE(l.account_code::text, '') AS account_code
            FROM finance.ledger l
            LEFT JOIN finance.vouchers v ON l.voucher_id = v.id
            WHERE l.account_code = %s
              AND l.{date_col} BETWEEN %s AND %s
            ORDER BY l.{date_col}, v.id, l.id
        """

        candidates: List[Tuple[str, Sequence[Any], str]] = [(query, [account_code, date_from, date_to], "ledger.account_code")]
        if self._is_int_like(account_code):
            by_id = f"""
                SELECT
                    COALESCE(v.v_type, '') || '-' || COALESCE(v.id::text, '') AS doc_no,
                    l.{date_col} AS row_date,
                    COALESCE(l.{desc_col}, '') AS description,
                    COALESCE(l.debit, 0) AS debit,
                    COALESCE(l.credit, 0) AS credit,
                    COALESCE(l.account_code::text, '') AS account_code
                FROM finance.ledger l
                LEFT JOIN finance.vouchers v ON l.voucher_id = v.id
                WHERE l.account_id = %s
                  AND l.{date_col} BETWEEN %s AND %s
                ORDER BY l.{date_col}, v.id, l.id
            """
            candidates.append((by_id, [int(account_code), date_from, date_to], "ledger.account_id"))

        rows = self._run_query_with_fallback(candidates, "تعذر جلب حركات الحساب من finance.ledger")

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
                "debit": "",
                "credit": "",
                "balance": self._fmt(opening_balance),
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
                    "debit": self._fmt(debit),
                    "credit": self._fmt(credit),
                    "balance": self._fmt(running_balance),
                    "row_type": "normal",
                }
            )

        rows.append(
            {
                "date": "",
                "doc_no": "",
                "description": "الإجمالي",
                "debit": self._fmt(total_debit),
                "credit": self._fmt(total_credit),
                "balance": self._fmt(running_balance),
                "row_type": "total",
            }
        )

        return {"rows": rows, "total_debit": total_debit, "total_credit": total_credit, "closing_balance": running_balance}

    def _build_account_statement_report(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        account_code = str(filters.get("account_code", "")).strip()
        date_from = str(filters.get("date_from", "")).strip()
        date_to = str(filters.get("date_to", "")).strip()
        posted_status = str(filters.get("posted_status", "")).strip() or "مرحلة"
        account_label = str(filters.get("account_label", "")).strip() or self._resolve_account_label(account_code)

        opening_balance = self.fetch_opening_balance(account_code, date_from)
        moves = self.fetch_ledger_moves(account_code, date_from, date_to)
        statement = self._statement_rows(moves, opening_balance)

        return {
            "meta_items": [
                {"label": "اسم الحساب", "value": account_label},
                {"label": "من تاريخ", "value": date_from},
                {"label": "إلى تاريخ", "value": date_to},
                {"label": "الحالة", "value": posted_status},
            ],
            "table_columns": [
                {"key": "date", "label": "التاريخ", "class_name": "col-date"},
                {"key": "doc_no", "label": "رقم السند", "class_name": "col-doc"},
                {"key": "description", "label": "البيان", "class_name": "col-desc"},
                {"key": "debit", "label": "مدين", "class_name": "col-debit"},
                {"key": "credit", "label": "دائن", "class_name": "col-credit"},
                {"key": "balance", "label": "الرصيد", "class_name": "col-balance"},
            ],
            "rows": statement["rows"],
            "summary_items": [
                {"label": "المدين", "value": self._fmt(statement["total_debit"])},
                {"label": "الدائن", "value": self._fmt(statement["total_credit"])},
                {"label": "الرصيد", "value": self._fmt(statement["closing_balance"])},
            ],
        }

    def _build_vendor_balances_report(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        date_col = self._ledger_date_column()
        date_from = str(filters.get("date_from", "")).strip()
        date_to = str(filters.get("date_to", "")).strip()

        if self._table_has_column("vendors", "control_account"):
            query = f"""
                SELECT
                    COALESCE(v.vendor_name, '') AS vendor_name,
                    COALESCE(v.control_account::text, '') AS account_code,
                    COALESCE(SUM(COALESCE(l.credit, 0) - COALESCE(l.debit, 0)), 0) AS balance
                FROM finance.vendors v
                LEFT JOIN finance.ledger l
                    ON COALESCE(l.account_code::text, '') = COALESCE(v.control_account::text, '')
                   AND l.{date_col} BETWEEN %s AND %s
                GROUP BY v.vendor_name, v.control_account
                ORDER BY v.vendor_name
            """
            rows_db = self._run_query(query, [date_from, date_to])
        else:
            rows_db = self._run_query("SELECT COALESCE(vendor_name, '') FROM finance.vendors ORDER BY vendor_name", [])
            rows_db = [(row[0], "", 0) for row in rows_db]

        rows = [{"vendor_name": r[0], "account_code": r[1], "balance": self._fmt(r[2]), "row_type": "normal"} for r in rows_db]
        total_balance = sum(float(r[2] or 0) for r in rows_db)

        return {
            "meta_items": [{"label": "من تاريخ", "value": date_from}, {"label": "إلى تاريخ", "value": date_to}],
            "table_columns": [
                {"key": "vendor_name", "label": "اسم المورد", "class_name": "col-desc"},
                {"key": "account_code", "label": "كود الحساب", "class_name": "col-doc"},
                {"key": "balance", "label": "الرصيد", "class_name": "col-balance"},
            ],
            "rows": rows,
            "summary_items": [{"label": "إجمالي الأرصدة", "value": self._fmt(total_balance)}],
        }

    def _build_customer_balances_report(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        date_col = self._ledger_date_column()
        date_from = str(filters.get("date_from", "")).strip()
        date_to = str(filters.get("date_to", "")).strip()

        if self._table_has_column("customers", "control_account"):
            query = f"""
                SELECT
                    COALESCE(c.customer_name, '') AS customer_name,
                    COALESCE(c.control_account::text, '') AS account_code,
                    COALESCE(SUM(COALESCE(l.debit, 0) - COALESCE(l.credit, 0)), 0) AS balance
                FROM finance.customers c
                LEFT JOIN finance.ledger l
                    ON COALESCE(l.account_code::text, '') = COALESCE(c.control_account::text, '')
                   AND l.{date_col} BETWEEN %s AND %s
                GROUP BY c.customer_name, c.control_account
                ORDER BY c.customer_name
            """
            rows_db = self._run_query(query, [date_from, date_to])
        else:
            rows_db = self._run_query("SELECT COALESCE(customer_name, '') FROM finance.customers ORDER BY customer_name", [])
            rows_db = [(row[0], "", 0) for row in rows_db]

        rows = [{"customer_name": r[0], "account_code": r[1], "balance": self._fmt(r[2]), "row_type": "normal"} for r in rows_db]
        total_balance = sum(float(r[2] or 0) for r in rows_db)

        return {
            "meta_items": [{"label": "من تاريخ", "value": date_from}, {"label": "إلى تاريخ", "value": date_to}],
            "table_columns": [
                {"key": "customer_name", "label": "اسم العميل", "class_name": "col-desc"},
                {"key": "account_code", "label": "كود الحساب", "class_name": "col-doc"},
                {"key": "balance", "label": "الرصيد", "class_name": "col-balance"},
            ],
            "rows": rows,
            "summary_items": [{"label": "إجمالي الأرصدة", "value": self._fmt(total_balance)}],
        }

    def _build_fund_movement_report(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        date_col = self._ledger_date_column()
        desc_col = self._ledger_description_column()
        date_from = str(filters.get("date_from", "")).strip()
        date_to = str(filters.get("date_to", "")).strip()
        fund_code = str(filters.get("fund_code", "")).strip()

        query = f"""
            SELECT
                l.{date_col} AS row_date,
                COALESCE(v.v_type, '') || '-' || COALESCE(v.id::text, '') AS doc_no,
                COALESCE(a.account_name, '') AS fund_name,
                COALESCE(l.{desc_col}, '') AS description,
                COALESCE(l.debit, 0) AS debit,
                COALESCE(l.credit, 0) AS credit
            FROM finance.ledger l
            LEFT JOIN finance.accounts a ON COALESCE(a.account_code::text, '') = COALESCE(l.account_code::text, '')
            LEFT JOIN finance.vouchers v ON l.voucher_id = v.id
            WHERE COALESCE(l.account_code::text, '') = %s
              AND l.{date_col} BETWEEN %s AND %s
            ORDER BY l.{date_col}, l.id
        """
        rows_db = self._run_query(query, [fund_code, date_from, date_to])

        running = 0.0
        rows: List[Dict[str, Any]] = []
        total_debit = 0.0
        total_credit = 0.0
        for row in rows_db:
            debit = float(row[4] or 0)
            credit = float(row[5] or 0)
            running += debit - credit
            total_debit += debit
            total_credit += credit
            rows.append(
                {
                    "date": row[0].strftime("%Y-%m-%d") if row[0] else "",
                    "doc_no": row[1],
                    "fund_name": row[2],
                    "description": row[3],
                    "debit": self._fmt(debit),
                    "credit": self._fmt(credit),
                    "balance": self._fmt(running),
                    "row_type": "normal",
                }
            )

        return {
            "meta_items": [
                {"label": "الصندوق", "value": fund_code},
                {"label": "من تاريخ", "value": date_from},
                {"label": "إلى تاريخ", "value": date_to},
            ],
            "table_columns": [
                {"key": "date", "label": "التاريخ", "class_name": "col-date"},
                {"key": "doc_no", "label": "رقم السند", "class_name": "col-doc"},
                {"key": "fund_name", "label": "اسم الصندوق", "class_name": "col-doc"},
                {"key": "description", "label": "البيان", "class_name": "col-desc"},
                {"key": "debit", "label": "مدين", "class_name": "col-debit"},
                {"key": "credit", "label": "دائن", "class_name": "col-credit"},
                {"key": "balance", "label": "الرصيد", "class_name": "col-balance"},
            ],
            "rows": rows,
            "summary_items": [
                {"label": "إجمالي المدين", "value": self._fmt(total_debit)},
                {"label": "إجمالي الدائن", "value": self._fmt(total_credit)},
                {"label": "الرصيد", "value": self._fmt(running)},
            ],
        }

    def _build_funds_summary_report(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        date_col = self._ledger_date_column()
        date_from = str(filters.get("date_from", "")).strip()
        date_to = str(filters.get("date_to", "")).strip()

        query = f"""
            SELECT
                COALESCE(a.account_code::text, '') AS fund_code,
                COALESCE(a.account_name, '') AS fund_name,
                COALESCE(SUM(COALESCE(l.debit, 0)), 0) AS total_debit,
                COALESCE(SUM(COALESCE(l.credit, 0)), 0) AS total_credit,
                COALESCE(SUM(COALESCE(l.debit, 0) - COALESCE(l.credit, 0)), 0) AS balance
            FROM finance.accounts a
            LEFT JOIN finance.ledger l
                ON COALESCE(l.account_code::text, '') = COALESCE(a.account_code::text, '')
               AND l.{date_col} BETWEEN %s AND %s
            WHERE TRIM(a.account_code) = '1101' OR TRIM(a.parent_code) = '1101' OR TRIM(a.account_code) LIKE '1101%'
            GROUP BY a.account_code, a.account_name
            ORDER BY a.account_code
        """
        rows_db = self._run_query(query, [date_from, date_to])
        rows = [
            {
                "fund_code": r[0],
                "fund_name": r[1],
                "debit": self._fmt(r[2]),
                "credit": self._fmt(r[3]),
                "balance": self._fmt(r[4]),
                "row_type": "normal",
            }
            for r in rows_db
        ]

        total_debit = sum(float(r[2] or 0) for r in rows_db)
        total_credit = sum(float(r[3] or 0) for r in rows_db)
        total_balance = sum(float(r[4] or 0) for r in rows_db)

        return {
            "meta_items": [{"label": "من تاريخ", "value": date_from}, {"label": "إلى تاريخ", "value": date_to}],
            "table_columns": [
                {"key": "fund_code", "label": "كود الصندوق", "class_name": "col-doc"},
                {"key": "fund_name", "label": "اسم الصندوق", "class_name": "col-desc"},
                {"key": "debit", "label": "مدين", "class_name": "col-debit"},
                {"key": "credit", "label": "دائن", "class_name": "col-credit"},
                {"key": "balance", "label": "الرصيد", "class_name": "col-balance"},
            ],
            "rows": rows,
            "summary_items": [
                {"label": "إجمالي المدين", "value": self._fmt(total_debit)},
                {"label": "إجمالي الدائن", "value": self._fmt(total_credit)},
                {"label": "صافي الحركة", "value": self._fmt(total_balance)},
            ],
        }

    def _build_property_status_report(self, _filters: Dict[str, Any]) -> Dict[str, Any]:
        rows_db = self._run_query(
            """
            SELECT
                id,
                COALESCE(property_name, '') AS property_name,
                COALESCE(account_code::text, '') AS account_code,
                COALESCE(purchase_price, 0) AS purchase_price,
                COALESCE(total_cost, 0) AS total_cost,
                COALESCE(status, '') AS status
            FROM finance.properties
            ORDER BY id
            """,
            [],
        )
        rows = [
            {
                "property_id": r[0],
                "property_name": r[1],
                "account_code": r[2],
                "purchase_price": self._fmt(r[3]),
                "total_cost": self._fmt(r[4]),
                "status": r[5],
                "row_type": "normal",
            }
            for r in rows_db
        ]

        return {
            "meta_items": [{"label": "تاريخ الطباعة", "value": datetime.now().strftime("%Y-%m-%d")}],
            "table_columns": [
                {"key": "property_id", "label": "ID", "class_name": "col-doc"},
                {"key": "property_name", "label": "اسم العقار", "class_name": "col-desc"},
                {"key": "account_code", "label": "كود الحساب", "class_name": "col-doc"},
                {"key": "purchase_price", "label": "سعر الشراء", "class_name": "col-debit"},
                {"key": "total_cost", "label": "التكلفة الكلية", "class_name": "col-credit"},
                {"key": "status", "label": "الحالة", "class_name": "col-balance"},
            ],
            "rows": rows,
            "summary_items": [{"label": "عدد العقارات", "value": str(len(rows))}],
        }

    def _build_property_revenue_expense_report(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        date_col = self._ledger_date_column()
        property_id = str(filters.get("property_id", "")).strip()
        date_from = str(filters.get("date_from", "")).strip()
        date_to = str(filters.get("date_to", "")).strip()

        query = f"""
            SELECT
                p.id,
                COALESCE(p.property_name, '') AS property_name,
                COALESCE(p.account_code::text, '') AS account_code,
                COALESCE(SUM(COALESCE(l.credit, 0)), 0) AS revenue,
                COALESCE(SUM(COALESCE(l.debit, 0)), 0) AS expense
            FROM finance.properties p
            LEFT JOIN finance.ledger l
                ON COALESCE(l.account_code::text, '') = COALESCE(p.account_code::text, '')
               AND l.{date_col} BETWEEN %s AND %s
            WHERE p.id = %s
            GROUP BY p.id, p.property_name, p.account_code
        """
        rows_db = self._run_query(query, [date_from, date_to, property_id])

        rows: List[Dict[str, Any]] = []
        total_revenue = 0.0
        total_expense = 0.0
        for row in rows_db:
            revenue = float(row[3] or 0)
            expense = float(row[4] or 0)
            total_revenue += revenue
            total_expense += expense
            rows.append(
                {
                    "property_id": row[0],
                    "property_name": row[1],
                    "account_code": row[2],
                    "revenue": self._fmt(revenue),
                    "expense": self._fmt(expense),
                    "net": self._fmt(revenue - expense),
                    "row_type": "normal",
                }
            )

        return {
            "meta_items": [{"label": "العقار", "value": property_id}, {"label": "من تاريخ", "value": date_from}, {"label": "إلى تاريخ", "value": date_to}],
            "table_columns": [
                {"key": "property_id", "label": "ID", "class_name": "col-doc"},
                {"key": "property_name", "label": "اسم العقار", "class_name": "col-desc"},
                {"key": "account_code", "label": "كود الحساب", "class_name": "col-doc"},
                {"key": "revenue", "label": "الإيرادات", "class_name": "col-credit"},
                {"key": "expense", "label": "المصروفات", "class_name": "col-debit"},
                {"key": "net", "label": "الصافي", "class_name": "col-balance"},
            ],
            "rows": rows,
            "summary_items": [
                {"label": "إجمالي الإيرادات", "value": self._fmt(total_revenue)},
                {"label": "إجمالي المصروفات", "value": self._fmt(total_expense)},
                {"label": "صافي النتيجة", "value": self._fmt(total_revenue - total_expense)},
            ],
        }

    def _build_chart_of_accounts_report(self, _filters: Dict[str, Any]) -> Dict[str, Any]:
        is_active_expr = "COALESCE(is_active, true)" if self._table_has_column("accounts", "is_active") else "true"
        rows_db = self._run_query(
            f"""
            SELECT
                COALESCE(account_code::text, '') AS account_code,
                COALESCE(account_name, '') AS account_name,
                COALESCE(parent_code::text, '') AS parent_code,
                COALESCE(account_level, '') AS account_level,
                {is_active_expr} AS is_active
            FROM finance.accounts
            ORDER BY account_code
            """,
            [],
        )
        rows = [
            {
                "account_code": r[0],
                "account_name": r[1],
                "parent_code": r[2],
                "account_level": r[3],
                "is_active": "فعال" if bool(r[4]) else "غير فعال",
                "row_type": "normal",
            }
            for r in rows_db
        ]

        return {
            "meta_items": [{"label": "تاريخ الطباعة", "value": datetime.now().strftime("%Y-%m-%d")}],
            "table_columns": [
                {"key": "account_code", "label": "كود الحساب", "class_name": "col-doc"},
                {"key": "account_name", "label": "اسم الحساب", "class_name": "col-desc"},
                {"key": "parent_code", "label": "الحساب الأب", "class_name": "col-doc"},
                {"key": "account_level", "label": "المستوى", "class_name": "col-doc"},
                {"key": "is_active", "label": "الحالة", "class_name": "col-balance"},
            ],
            "rows": rows,
            "summary_items": [{"label": "عدد الحسابات", "value": str(len(rows))}],
        }

    def _build_trial_balance_report(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        date_col = self._ledger_date_column()
        date_from = str(filters.get("date_from", "")).strip()
        date_to = str(filters.get("date_to", "")).strip()

        query = f"""
            SELECT
                COALESCE(a.account_code::text, '') AS account_code,
                COALESCE(a.account_name, '') AS account_name,
                COALESCE(SUM(COALESCE(l.debit, 0)), 0) AS total_debit,
                COALESCE(SUM(COALESCE(l.credit, 0)), 0) AS total_credit
            FROM finance.accounts a
            LEFT JOIN finance.ledger l
                ON COALESCE(l.account_code::text, '') = COALESCE(a.account_code::text, '')
               AND l.{date_col} BETWEEN %s AND %s
            GROUP BY a.account_code, a.account_name
            ORDER BY a.account_code
        """
        rows_db = self._run_query(query, [date_from, date_to])
        rows = []
        total_debit = 0.0
        total_credit = 0.0
        for row in rows_db:
            debit = float(row[2] or 0)
            credit = float(row[3] or 0)
            total_debit += debit
            total_credit += credit
            rows.append(
                {
                    "account_code": row[0],
                    "account_name": row[1],
                    "debit": self._fmt(debit),
                    "credit": self._fmt(credit),
                    "balance": self._fmt(debit - credit),
                    "row_type": "normal",
                }
            )

        return {
            "meta_items": [{"label": "من تاريخ", "value": date_from}, {"label": "إلى تاريخ", "value": date_to}],
            "table_columns": [
                {"key": "account_code", "label": "كود الحساب", "class_name": "col-doc"},
                {"key": "account_name", "label": "اسم الحساب", "class_name": "col-desc"},
                {"key": "debit", "label": "مدين", "class_name": "col-debit"},
                {"key": "credit", "label": "دائن", "class_name": "col-credit"},
                {"key": "balance", "label": "الرصيد", "class_name": "col-balance"},
            ],
            "rows": rows,
            "summary_items": [
                {"label": "إجمالي المدين", "value": self._fmt(total_debit)},
                {"label": "إجمالي الدائن", "value": self._fmt(total_credit)},
                {"label": "الفرق", "value": self._fmt(total_debit - total_credit)},
            ],
        }

    def _build_general_journal_report(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        date_col = self._ledger_date_column()
        desc_col = self._ledger_description_column()
        date_from = str(filters.get("date_from", "")).strip()
        date_to = str(filters.get("date_to", "")).strip()

        query = f"""
            SELECT
                l.id,
                l.{date_col} AS row_date,
                COALESCE(v.v_type, '') || '-' || COALESCE(v.id::text, '') AS doc_no,
                COALESCE(l.account_code::text, '') AS account_code,
                COALESCE(l.{desc_col}, '') AS description,
                COALESCE(l.debit, 0) AS debit,
                COALESCE(l.credit, 0) AS credit
            FROM finance.ledger l
            LEFT JOIN finance.vouchers v ON l.voucher_id = v.id
            WHERE l.{date_col} BETWEEN %s AND %s
            ORDER BY l.{date_col}, l.id
        """
        rows_db = self._run_query(query, [date_from, date_to])

        rows = []
        total_debit = 0.0
        total_credit = 0.0
        for row in rows_db:
            debit = float(row[5] or 0)
            credit = float(row[6] or 0)
            total_debit += debit
            total_credit += credit
            rows.append(
                {
                    "entry_id": row[0],
                    "date": row[1].strftime("%Y-%m-%d") if row[1] else "",
                    "doc_no": row[2],
                    "account_code": row[3],
                    "description": row[4],
                    "debit": self._fmt(debit),
                    "credit": self._fmt(credit),
                    "row_type": "normal",
                }
            )

        return {
            "meta_items": [{"label": "من تاريخ", "value": date_from}, {"label": "إلى تاريخ", "value": date_to}],
            "table_columns": [
                {"key": "entry_id", "label": "رقم القيد", "class_name": "col-doc"},
                {"key": "date", "label": "التاريخ", "class_name": "col-date"},
                {"key": "doc_no", "label": "رقم السند", "class_name": "col-doc"},
                {"key": "account_code", "label": "الحساب", "class_name": "col-doc"},
                {"key": "description", "label": "البيان", "class_name": "col-desc"},
                {"key": "debit", "label": "مدين", "class_name": "col-debit"},
                {"key": "credit", "label": "دائن", "class_name": "col-credit"},
            ],
            "rows": rows,
            "summary_items": [
                {"label": "إجمالي المدين", "value": self._fmt(total_debit)},
                {"label": "إجمالي الدائن", "value": self._fmt(total_credit)},
            ],
        }

    # ---------- Rendering ----------

    def _build_base_context(self, report_title: str, user_name: str) -> Dict[str, Any]:
        branding = self.fetch_system_settings()
        return {
            "report_title": report_title,
            "company_name": branding["company_name"],
            "company_phone": branding["phone"],
            "company_email": branding["email"],
            "company_address": branding["address"],
            "company_logo": branding["logo_path"],
            "company_logo_uri": self._logo_uri(branding["logo_path"]),
            "print_date": datetime.now().strftime("%Y-%m-%d"),
            "print_time": datetime.now().strftime("%H:%M:%S"),
            "user_name": user_name,
            "template_name": "account_statement.html",
        }

    def generate_report(self, report_type: str, filters: Dict[str, Any], user_name: str) -> Dict[str, Any]:
        self.cleanup_temp_files()
        config = self.get_report_config(report_type)
        dynamic = config["builder"](filters)
        context = self._build_base_context(config["title"], user_name)
        context.update(dynamic)
        context.setdefault("meta_items", [])
        context.setdefault("table_columns", [])
        context.setdefault("rows", [])
        context.setdefault("summary_items", [])
        html = self.render_html(context)
        pdf_path = self.generate_pdf(html)
        return {"context": context, "pdf_path": pdf_path, "html": html}

    def render_html(self, context: Dict[str, Any]) -> str:
        template_name = str(context.get("template_name") or "account_statement.html")
        template = self.template_env.get_template(template_name)
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

    # Backward-compatible entrypoint kept for existing callers.
    def generate_account_statement(
        self,
        account_code: str | None = None,
        date_from: str = "",
        date_to: str = "",
        account_label: str = "",
        posted_status: str = "مرحلة",
        user_name: str = "المستخدم الحالي",
        account_id: str | int | None = None,
    ) -> Dict[str, Any]:
        code = str(account_code or account_id or "").strip()
        return self.generate_report(
            report_type="كشف حساب تفصيلي",
            filters={
                "account_code": code,
                "account_label": account_label,
                "date_from": date_from,
                "date_to": date_to,
                "posted_status": posted_status,
            },
            user_name=user_name,
        )

    @staticmethod
    def save_as_pdf(source_pdf: str, target_pdf: str) -> None:
        shutil.copy2(source_pdf, target_pdf)

    @staticmethod
    def export_excel(rows: List[Dict[str, Any]], target_path: str) -> None:
        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError("مكتبة pandas غير مثبتة") from exc

        if not rows:
            pd.DataFrame([]).to_excel(target_path, index=False)
            return

        export_rows = [{k: v for k, v in row.items() if k != "row_type"} for row in rows]
        pd.DataFrame(export_rows).to_excel(target_path, index=False)

