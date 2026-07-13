import sys
import time
from datetime import datetime, timezone
import uuid

def main():
    """Generate and output a random string with timestamp every 5 seconds."""
    random_string = str(uuid.uuid4())  # Generate a random UUID string
    while True:
        now_utc = datetime.now(timezone.utc)
        iso_string = now_utc.isoformat().replace("+00:00", "Z")
        print(f"{iso_string}: {random_string}")
        sys.stdout.flush()
        time.sleep(5)

if __name__ == "__main__":
    main()
