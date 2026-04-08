import argparse
import tkinter as tk
from tkinter import messagebox

from reporting import ReportManager, ReportPreviewWindow


def parse_args():
    parser = argparse.ArgumentParser(description="LandLedger Account Statement Preview Demo")
    parser.add_argument("--account-id", type=int, required=True)
    parser.add_argument("--date-from", required=True, help="YYYY-MM-DD")
    parser.add_argument("--date-to", required=True, help="YYYY-MM-DD")
    parser.add_argument("--account-label", default="")
    parser.add_argument("--posted-status", default="مرحلة")
    parser.add_argument("--user", default="المستخدم الحالي")
    return parser.parse_args()


def main():
    args = parse_args()

    root = tk.Tk()
    root.withdraw()

    manager = ReportManager()
    try:
        report_data = manager.generate_account_statement(
            account_id=args.account_id,
            date_from=args.date_from,
            date_to=args.date_to,
            account_label=args.account_label or str(args.account_id),
            posted_status=args.posted_status,
            user_name=args.user,
        )
    except Exception as exc:
        messagebox.showerror("خطأ", str(exc))
        root.destroy()
        return

    window = ReportPreviewWindow(root, manager, report_data)
    window.focus_force()
    root.mainloop()


if __name__ == "__main__":
    main()

