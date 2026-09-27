"""Replay newline-delimited BMS telemetry through the autonomous controller."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.battery import AutonomousBatteryController
from src.telemetry import JsonLineTelemetryAdapter


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", help="JSONL file; stdin is used by default")
    args = parser.parse_args()
    stream = open(args.path, encoding="utf-8") if args.path else sys.stdin
    try:
        controller = AutonomousBatteryController()
        trace = [
            controller.observe(observation).as_dict()
            for observation in JsonLineTelemetryAdapter(stream).observations()
        ]
    finally:
        if args.path:
            stream.close()
    if not trace:
        raise SystemExit("No telemetry observations were provided")
    errors = [item["prediction"]["error"] for item in trace]
    print(json.dumps({
        "observations": len(trace),
        "mean_prediction_error": sum(errors) / len(errors),
        "max_prediction_error": max(errors),
        "final_action": trace[-1]["action"],
    }, indent=2))


if __name__ == "__main__":
    main()