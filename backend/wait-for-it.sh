#!/usr/bin/env bash
#   Use this script to test if a given TCP host/port are available
#   Source: https://github.com/vishnubob/wait-for-it

set -e

host="$1"
shift
port="$1"
shift

timeout="${WAITFORIT_TIMEOUT:-15}"
interval="${WAITFORIT_INTERVAL:-1}"

start_ts=$(date +%s)
while :
do
  nc -z "$host" "$port" && break
  now_ts=$(date +%s)
  if [ $((now_ts - start_ts)) -ge $timeout ]; then
    echo "Timeout waiting for $host:$port"
    exit 1
  fi
  sleep $interval
done

exec "$@"