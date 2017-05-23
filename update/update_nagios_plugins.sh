#!/bin/bash

# This script always return 0 (even on error), so as not to trigger admin
# notifications when run from a cron job. Error status is written in
# the status file. The only exception is argument parsing error

do_update=0
verbose_mode=0
verbose_cmd_option=""

function echoMsg () {
  echo "$(date -Iseconds) $1"
}

function echoVerboseMsg () {
  if [ $verbose_mode -eq 1 ]; then echo "$(date -Iseconds) $1"; fi
}

function writeStatus () {
  echo "$(date -Iseconds);$1;$2" >$status_file_path
}

function startService () {
  echoVerboseMsg "Starting '$1' service"
  sudo -n /usr/sbin/service $1 start
}

function stopService () {
  echoVerboseMsg "Stopping '$1' service"
  sudo -n /usr/sbin/service $1 stop
}


while [[ $# -gt 0 ]]
do
  case $1 in
    -u|--do-update)
      do_update=1
    ;;
    -v|--verbose)
      verbose_mode=1
      verbose_cmd_option="--verbose"
    ;;
    *)
      echo "$1: Unknown option"
      exit 1
    ;;
  esac
  shift
done

this_script_full_path="$(readlink -e "$0")"
echoVerboseMsg "Executing '$this_script_full_path'"

if [ $do_update -eq 0 ]; then
  # -u: do not create the file, just return a name
  temp_script_name=$(mktemp -u)
  echoVerboseMsg "Temporary script name: $temp_script_name"
  cp "$this_script_full_path" "$temp_script_name"
  exec $temp_script_name --do-update $verbose_cmd_option
  # Should not get here unless exec call has failed
  exit 1
fi

status_file_path="${HOME}/plugins_update_status"
git_repo_path="${HOME}/nagios-plugins"

echoMsg "Checking for Nagios plugins repo updates"

cd $git_repo_path

GIT_TERMINAL_PROMPT=0

git_output=$((git fetch) 2>&1)
if [ $? -ne 0 ]; then
  echoMsg "Error fetching repository: $git_output"
  writeStatus "ERROR" "Error fetching repository"
  exit 0
fi

if [ $(git rev-parse HEAD) == $(git rev-parse @{u}) ]; then
  echoMsg "Repository is up to date"
  writeStatus "OK" "Repository is up to date"
else
  #/usr/sbin/service cron status >/dev/null 2>&1
  /usr/sbin/service nagios-nrpe-server status >/dev/null 2>&1
  nrpe_service_status=$?

  /usr/sbin/service nagios status >/dev/null 2>&1
  nagios_service_status=$?

  if [ $nrpe_service_status -eq 0 ]; then stopService nagios-nrpe-server; fi 
  if [ $nagios_service_status -eq 0 ]; then stopService nagios; fi 

  echoVerboseMsg "Pulling updates"
  git_output=$((git pull) 2>&1)
  if [ $? -ne 0 ]; then
    echoMsg "Error updating repository: $git_output"
    writeStatus "ERROR" "Error updating repository"
  else
    echoMsg "Repository has been updated"
    writeStatus "OK" "Repository has been updated"
  fi

  if [ $nrpe_service_status -eq 0 ]; then startService nagios-nrpe-server; fi
  if [ $nagios_service_status -eq 0 ]; then startService nagios; fi
fi

echoVerboseMsg "Removing temporary script file '$this_script_full_path'"
rm "$this_script_full_path"
exit 0
