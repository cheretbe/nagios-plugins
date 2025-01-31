#!/usr/bin/env python3

import os
import sys
import datetime
import pathlib
import argparse
import json
import subprocess

# Nagios status codes
STATUS_UNKNOWN = -1
STATUS_OK = 0
STATUS_WARNING = 1
STATUS_CRITICAL = 2


def main(args):
    exit_status = STATUS_OK
    exit_status_text = ""

    try:
        status_file_name = os.path.expanduser("~/.cache/cheretbe/nagios-plugins/seafile_status.json")
        if os.path.isfile(status_file_name):
            with open(status_file_name) as status_f:
                seafile_status = json.load(status_f)
            for library in seafile_status.keys():
                # [!] 3.7+
                seafile_status[library] = datetime.datetime.fromisoformat(seafile_status[library])
        else:
            seafile_status = {}

        for line in subprocess.check_output(("seaf-cli", "status"), universal_newlines=True).splitlines():
            if line[0] != "#":
                library, status = line.split(maxsplit=1)
                if library not in seafile_status:
                    # Strip microseconds to emulate Linux 'date -Iseconds' behavior
                    seafile_status[library] = datetime.datetime.now().replace(microsecond=0)
                # https://github.com/haiwen/seafile/blob/master/daemon/sync-mgr.c#L473
                if exit_status_text:
                    exit_status_text += "; "

                # if library == "projects":
                # seafile_status[library] = datetime.datetime.now().replace(microsecond=0) - datetime.timedelta(minutes=100)
                # seafile_status[library] = datetime.datetime.now().replace(microsecond=0) - datetime.timedelta(days=1, minutes=10)
                # status = "committing"

                if status == "synchronized":
                    exit_status_text += f"{library}: {status}"
                    seafile_status[library] = datetime.datetime.now().replace(microsecond=0)
                elif status in ["committing", "initializing", "downloading", "merging", "uploading"]:
                    time_delta = datetime.datetime.now().replace(microsecond=0) - seafile_status[library]
                    status_icon = ""
                    if time_delta.total_seconds() > (args.warning * 60):
                        status_icon = "(!)"
                        if exit_status != STATUS_CRITICAL:
                            exit_status = STATUS_WARNING
                    if time_delta.total_seconds() > (args.critical * 60):
                        status_icon = "(!)"
                        exit_status = STATUS_CRITICAL
                    exit_status_text += f"{library}: {status} {status_icon}{str(time_delta)}"
                else:
                    exit_status = STATUS_CRITICAL
                    exit_status_text += f"{library}: {status}"

        for library in seafile_status.keys():
            seafile_status[library] = seafile_status[library].isoformat()

        os.makedirs(os.path.dirname(status_file_name), exist_ok=True)
        with open(status_file_name, "w", encoding="utf-8") as status_f:
            json.dump(seafile_status, status_f, ensure_ascii=False, indent=4)
    except Exception as e:
        exit_status = STATUS_UNKNOWN
        exit_status_text = f"Unhandled exception: {e}"

    print(exit_status_text)
    sys.exit(exit_status)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-w", "--warning", type=int, default=30, help="Warning threshold in minutes (default=30)"
    )
    parser.add_argument(
        "-c", "--critical", type=int, default=90, help="Warning threshold in minutes (default=90)"
    )
    args = parser.parse_args()

    main(args)
