#!/usr/bin/env python3

import argparse
import subprocess
import json

# Nagios status codes
STATUS_UNKNOWN = -1
STATUS_OK = 0
STATUS_WARNING = 1
STATUS_CRITICAL = 2
STATUS_NAMES = {
    STATUS_OK: "OK",
    STATUS_WARNING: "WARNING",
    STATUS_CRITICAL: "CRITICAL",
    STATUS_UNKNOWN: "UNKNOWN",
}


def main(args):
    completed_proc = subprocess.run(args.original_command, stdout=subprocess.PIPE, encoding="utf-8")
    status_obj = {"status": completed_proc.returncode}
    if args.no_text_status:
        status_obj["status_text"] = completed_proc.stdout.rstrip()
    else:
        status_obj["status_text"] = (
            f"{STATUS_NAMES[completed_proc.returncode]} {completed_proc.stdout.rstrip()}"
        )
    print(json.dumps(status_obj))


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-n",
        "--no-text-status",
        action="store_true",
        default=False,
        help="Do not add Nagios code text representation before status text",
    )
    parser.add_argument("original_command", nargs="*")

    return parser.parse_args()


if __name__ == "__main__":
    main(parse_args())
