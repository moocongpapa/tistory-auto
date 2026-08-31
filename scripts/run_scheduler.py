"""
Master Scheduler Daemon Entrypoint
Runs APScheduler 24/7 for 5 blogs across configured 6-hour intervals.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Set root directory in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from core.scheduler import MultiBlogScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join("data", "scheduler.log"), encoding="utf-8")
    ]
]

def main():
    os.makedirs("data", exist_ok=True)
    scheduler = MultiBlogScheduler()
    scheduler.start_schedules()

if __name__ == "__main__":
    main()
