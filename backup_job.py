import json
import os
from datetime import datetime

from backup_service import create_json_backup


def _read_settings(settings_path):
    if not os.path.exists(settings_path):
        return {}
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def main():
    base_dir = os.path.dirname(__file__)
    settings_path = os.path.join(base_dir, "app_settings.json")
    settings = _read_settings(settings_path)

    backup_root = settings.get("backup_path") or os.path.join(base_dir, "backups")
    path = create_json_backup(backup_root=backup_root, created_by="scheduler")

    log_path = os.path.join(base_dir, "backups", "backup_job.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat(timespec='seconds')} OK {path}\n")


if __name__ == "__main__":
    main()

