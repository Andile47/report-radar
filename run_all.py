"""Report Radar - build everything, in order, from data/reports.csv.

Run from the repo root:  python run_all.py
Then open the dashboard: streamlit run dashboard/app.py

Steps (stops at the first one that fails):
  1. data/check_data.py              check the dataset follows the contract
  2. intake/classifier.py            add category, urgency and review flags
  3. intake/evaluate.py              test the classifier on 30 tricky reports
  4. forecast/forecast.py            weekly forecast, workload table, chart
  5. hotspots/hotspot_analysis.py    clusters, ranked list, map
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = [
    ("Check data", "data/check_data.py"),
    ("Classify reports", "intake/classifier.py"),
    ("Test the classifier", "intake/evaluate.py"),
    ("Forecast", "forecast/forecast.py"),
    ("Hotspots", "hotspots/hotspot_analysis.py"),
]


def main() -> int:
    for number, (name, script) in enumerate(STEPS, start=1):
        print(f"\n=== {number}/{len(STEPS)} {name} ({script}) ===", flush=True)
        start = time.time()
        result = subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT)
        if result.returncode != 0:
            print(f"\nStopped: {script} failed. Fix it and run again.")
            return result.returncode
        print(f"--- done in {time.time() - start:.0f}s")
    print("\nAll steps finished. Open the dashboard with:  streamlit run dashboard/app.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
