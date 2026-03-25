import subprocess
from typing import Optional

TASK_NAME = "RealEstateDailyBackup"


def _run_cmd(args):
    proc = subprocess.run(args, capture_output=True, text=True, shell=False)
    if proc.returncode != 0:
        msg = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(msg or "فشل تنفيذ أمر مجدول")
    return (proc.stdout or "").strip()


def create_daily_backup_task(run_time: str, python_exe: str, backup_job_path: str) -> None:
    task_command = f'"{python_exe}" "{backup_job_path}"'
    _run_cmd(
        [
            "schtasks",
            "/Create",
            "/F",
            "/SC",
            "DAILY",
            "/ST",
            run_time,
            "/TN",
            TASK_NAME,
            "/TR",
            task_command,
        ]
    )


def delete_daily_backup_task() -> None:
    _run_cmd(["schtasks", "/Delete", "/F", "/TN", TASK_NAME])


def task_exists() -> bool:
    proc = subprocess.run(
        ["schtasks", "/Query", "/TN", TASK_NAME], capture_output=True, text=True, shell=False
    )
    return proc.returncode == 0


def query_task() -> Optional[str]:
    if not task_exists():
        return None
    return _run_cmd(["schtasks", "/Query", "/TN", TASK_NAME, "/V", "/FO", "LIST"])

