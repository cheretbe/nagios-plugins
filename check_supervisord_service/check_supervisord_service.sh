#!/bin/bash


# Nagios status codes
STATE_OK=0
STATE_WARNING=1
STATE_CRITICAL=2
STATE_UNKNOWN=3

if [ -z "${1}" ]; then
  echo "CRITICAL - Missing service name"
  exit $STATE_CRITICAL
fi

service_status="$(/usr/bin/sudo --non-interactive /usr/bin/supervisorctl status ${1} 2>&1)"
if [ $? -ne 0 ]; then
  echo "CRITICAL - supervisorctl call has failed: ${service_status}"
  exit $STATE_CRITICAL
fi

echo $service_status | grep 'RUNNING' 1> /dev/null
if [ $? -eq 0 ]; then
  echo "OK - '${1}' service is running"
else
  echo "CRITICAL - '${1}' service is not running. Status: ${service_status}"
  exit $STATE_CRITICAL
fi
