#!/usr/bin/env python

import sys
import argparse

# Nagios status codes
STATUS_UNKNOWN  = -1
STATUS_OK       =  0
STATUS_WARNING  =  1
STATUS_CRITICAL =  2

def main():
  exit_code = STATUS_UNKNOWN
  try:
    parser = argparse.ArgumentParser(description="Nagios plugin to report status from custom file")
    parser.add_argument("status_file_name", help="File to read status information from")
    options = parser.parse_args()
    # dummy = 1 / 0

  except Exception as e:
    print("Unhandled exception: {}".format(e))
    exit_code = STATUS_CRITICAL

  return (exit_code)

if __name__ == '__main__':
  sys.exit(main())