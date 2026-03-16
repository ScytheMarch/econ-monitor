"""Launcher: starts all Economic Monitor services with one command.

Services:
  1. changedetection.io (port 5000) - page change monitoring
  2. FastAPI webhook receiver (port 8001) - handles change notifications
  3. FRED poller (background) - polls FRED for updates every 15 min
  4. Streamlit dashboard (port 8501) - the user-facing UI

Usage:
  python launcher.py              # Start all services
  python launcher.py --no-cd      # Skip changedetection.io (if not installed)
  python launcher.py --dashboard  # Dashboard only (no detection services)
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

# Ensure the project is on the Python path
sys.path.insert(0, str(PROJECT_ROOT))


def _is_changedetection_available() -> bool:
    """Check if changedetection.io is pip-installed."""
    try:
        import importlib.util
        return importlib.util.find_spec("changedetection") is not None
    except Exception:
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Economic Monitor Launcher")
    parser.add_argument("--no-cd", action="store_true", help="Skip changedetection.io")
    parser.add_argument("--dashboard", action="store_true", help="Dashboard only, no detection services")
    parser.add_argument("--fetch", action="store_true", help="Run initial data fetch then exit")
    args = parser.parse_args()

    # Initial data fetch mode
    if args.fetch:
        _run_initial_fetch()
        return

    processes: list[subprocess.Popen] = []

    def cleanup(signum=None, frame=None):
        print("\nShutting down all services...")
        for p in processes:
            try:
                p.terminate()
            except Exception:
                pass
        for p in processes:
            try:
                p.wait(timeout=5)
            except Exception:
                p.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    python = sys.executable
    data_dir = PROJECT_ROOT / "data" / "changedetection"

    if not args.dashboard:
        # 1. changedetection.io
        if not args.no_cd and _is_changedetection_available():
            data_dir.mkdir(parents=True, exist_ok=True)
            print("[LAUNCHER] Starting changedetection.io on port 5000...")
            processes.append(subprocess.Popen(
                ["changedetection.io", "-d", str(data_dir), "-p", "5000"],
                cwd=str(PROJECT_ROOT),
            ))
            time.sleep(2)

            # Setup watches
            print("[LAUNCHER] Setting up changedetection.io watches...")
            try:
                from econ_monitor.detection.changedetection import setup_all_watches
                watches = setup_all_watches()
                print(f"[LAUNCHER] {len(watches)} watches configured")
            except Exception as e:
                print(f"[LAUNCHER] Warning: Could not setup watches: {e}")
        else:
            if not args.no_cd:
                print("[LAUNCHER] changedetection.io not installed. Install with: pip install changedetection.io")
            print("[LAUNCHER] Skipping changedetection.io (FRED poller will handle detection)")

        # 2. Webhook receiver
        print("[LAUNCHER] Starting webhook receiver on port 8001...")
        processes.append(subprocess.Popen(
            [python, "-m", "uvicorn",
             "econ_monitor.detection.webhook_receiver:app",
             "--host", "0.0.0.0",
             "--port", "8001",
             "--log-level", "info"],
            cwd=str(PROJECT_ROOT),
        ))

        # 3. FRED poller
        print("[LAUNCHER] Starting FRED poller (15-min interval)...")
        processes.append(subprocess.Popen(
            [python, "-m", "econ_monitor.data.fred_poller"],
            cwd=str(PROJECT_ROOT),
        ))

    # 4. Streamlit dashboard
    print("[LAUNCHER] Starting Streamlit dashboard on port 8501...")
    processes.append(subprocess.Popen(
        [python, "-m", "streamlit", "run",
         "econ_monitor/ui/app.py",
         "--server.port", "8501",
         "--server.headless", "true",
         "--browser.gatherUsageStats", "false"],
        cwd=str(PROJECT_ROOT),
    ))

    print("\n" + "=" * 60)
    print("Economic Monitor is running!")
    print("=" * 60)
    print(f"  Dashboard:      http://localhost:8501")
    if not args.dashboard:
        print(f"  Webhook API:    http://localhost:8001/health")
        if not args.no_cd and _is_changedetection_available():
            print(f"  Change Detect:  http://localhost:5000")
    print(f"\n  Press Ctrl+C to stop all services")
    print("=" * 60 + "\n")

    # Wait for any process to exit
    try:
        while True:
            for p in processes:
                if p.poll() is not None:
                    print(f"[LAUNCHER] Process {p.args} exited with code {p.returncode}")
            time.sleep(2)
    except KeyboardInterrupt:
        cleanup()


def _run_initial_fetch() -> None:
    """Fetch all indicator data and populate the SQLite cache."""
    from econ_monitor.config.indicators import INDICATORS
    from econ_monitor.data.openbb_client import fetch_series, get_series_info
    from econ_monitor.data import cache

    print(f"Fetching {len(INDICATORS)} indicators...")
    errors = []

    for i, (sid, ind) in enumerate(INDICATORS.items(), 1):
        print(f"  [{i}/{len(INDICATORS)}] {ind.name} ({sid})...", end=" ", flush=True)
        try:
            df = fetch_series(sid, lookback_years=5)
            if not df.empty:
                count = cache.upsert_observations(sid, df)
                try:
                    info = get_series_info(sid)
                    cache.upsert_metadata(
                        sid,
                        title=info.get("title", ind.name),
                        frequency=info.get("frequency", ind.frequency),
                        units=info.get("units", ind.unit),
                        last_updated=info.get("last_updated", ""),
                    )
                except Exception:
                    cache.upsert_metadata(sid, title=ind.name)
                print(f"OK ({count} obs)")
            else:
                print("EMPTY")
                errors.append(f"{ind.name}: empty response")
        except Exception as e:
            print(f"ERROR: {e}")
            errors.append(f"{ind.name}: {e}")

    print(f"\nDone! {len(INDICATORS) - len(errors)}/{len(INDICATORS)} successful.")
    if errors:
        print(f"\n{len(errors)} errors:")
        for err in errors:
            print(f"  - {err}")


if __name__ == "__main__":
    main()
