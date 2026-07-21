#!/usr/bin/env bash
#
# Host-side watcher for the web UI's "Update & Restart" button.
#
# The app (running inside the container) drops a flag file into update_trigger/,
# which is bind-mounted from this repo. This script runs on the HOST, notices
# the flag, and rebuilds the container via deploy.sh. Wire it up with the
# systemd units in systemd/ (a .path unit that watches the folder) or a cron
# job -- see SELF_UPDATE.md.
#
# The app cannot rebuild itself: docker-compose down would kill the very
# process handling the request. Running the rebuild from the host avoids that.

set -euo pipefail

# Always operate from the repo root, regardless of the caller's working dir.
cd "$(dirname "$0")"

FLAG="update_trigger/update.request"

# Nothing to do if no update was requested.
[ -f "$FLAG" ] || exit 0

# Remove the flag first so a long rebuild cannot re-trigger us.
rm -f "$FLAG"

echo "[$(date -Is)] Update requested -- running deploy.sh"
./deploy.sh
echo "[$(date -Is)] Update complete"
