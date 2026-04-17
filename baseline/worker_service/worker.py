import os
import time


POLL_SECONDS = int(os.getenv("WORKER_POLL_SECONDS", "5"))


if __name__ == "__main__":
    print(f"worker_service started, polling every {POLL_SECONDS}s")
    while True:
        print("worker_service heartbeat")
        time.sleep(POLL_SECONDS)
