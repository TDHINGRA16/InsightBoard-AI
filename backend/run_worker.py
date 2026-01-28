"""
Windows-friendly RQ worker runner.

RQ's default Worker uses os.fork(), which is not available on Windows.
This script uses rq.worker.SimpleWorker, which executes jobs in-process.

Usage (from backend/ with venv activated):
  python run_worker.py
  python run_worker.py high default low

Env:
  REDIS_URL must be set (or present in backend/.env via pydantic-settings).
"""

from __future__ import annotations

import sys

from rq import Queue
from rq.worker import SimpleWorker

from app.core.logging import setup_logging
from app.workers.queue import get_redis_connection


def main(argv: list[str]) -> int:
    setup_logging()

    queue_names = argv[1:] if len(argv) > 1 else ["high", "default", "low"]
    connection = get_redis_connection()

    queues = [Queue(name, connection=connection) for name in queue_names]

    # SimpleWorker avoids os.fork() and works on Windows.
    worker = SimpleWorker(queues, connection=connection)
    worker.work(with_scheduler=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

