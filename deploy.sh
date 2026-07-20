#!/usr/bin/env bash
#
# Deploy / update the pyLoad Jellyfin Mover container on the home server.
#
# Pulls the latest code, rebuilds the image and starts a fresh container.
#
# Why "down" before "up":
#   docker-compose v1 (1.29.2) crashes when it tries to *recreate* a
#   container on top of an image built by BuildKit, with:
#       KeyError: 'ContainerConfig'
#   Removing the old container first avoids the broken recreate path, so
#   "up" creates a brand-new container instead. No data is lost -- the
#   media lives in the bind-mounted host directories, and move status is
#   only ever held in memory.
#
# If you have Docker Compose V2 available, `docker compose up -d --build`
# (note the space, no hyphen) does not have this bug and can be used directly.

set -euo pipefail

# Always run from the repo root, regardless of where the script is called from.
cd "$(dirname "$0")"

# Bake the current source into the image -- pull first so it is up to date.
git pull --ff-only

# Stop and remove the existing container (safe: it holds no persistent data).
docker-compose down

# Rebuild the image and start a fresh container.
docker-compose up -d --build

echo
echo "Deployed. Follow logs with: docker-compose logs -f"
