import os
import time
import fire
import requests
from datetime import datetime, timezone


TWO_DAYS = 60 * 60 * 24 * 2


def cleanup(ext, path, keep):
    for f in os.listdir(path):
        if not f.endswith(ext):
            continue

        fn = os.path.join(path, f)
        try:
            stats = os.stat(fn)
            if datetime.now(timezone.utc).timestamp() - stats.st_ctime >= keep:
                os.remove(fn)
        except FileNotFoundError:
            print(f"file not found {fn}")
            continue


def main(backup_dir, keep=TWO_DAYS, timeout=30 * 60, url="http://0.0.0.0:9070/backup", file_prefix="cozo-backup"):
    while True:
        cleanup(".bk", backup_dir, keep)

        for _ in range(5):
            backup_fn = f"{file_prefix}-{datetime.now(timezone.utc).strftime('%Y-%m-%d_%H:%M:%S.%f')}.bk"
            resp = requests.post(
                url, 
                json={
                    "path": os.path.join(backup_dir, backup_fn),
                },
            )
            try:
                resp.raise_for_status()
                break
            except:
                time.sleep(10)
                continue

        time.sleep(timeout)


if __name__ == "__main__":
    fire.Fire(main)