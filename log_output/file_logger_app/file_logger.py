import os
import time
from datetime import datetime, timezone
from uuid import uuid4


def main() -> None:
    log_file_path = os.environ.get("LOG_FILE_PATH", "/data/file_logger.log")
    log_directory = os.path.dirname(log_file_path)
    if log_directory:
        os.makedirs(log_directory, exist_ok=True)

    logger_id = str(uuid4())

    while True:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
        with open(log_file_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"{timestamp} {logger_id}\n")
            log_file.flush()
        time.sleep(5)


if __name__ == "__main__":
    main()
