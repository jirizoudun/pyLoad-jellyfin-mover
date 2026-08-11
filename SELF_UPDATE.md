# Self-update ("Update & Restart" button)

The web UI has an **Update & Restart** button that pulls the latest code and
rebuilds the container. Because the app runs *inside* the container it would
need to rebuild, it cannot run `docker-compose down/up` itself — that would kill
the very process handling the request. Instead:

1. The button POSTs to `/self-update`, which drops a flag file at
   `update_trigger/update.request` (bind-mounted into the container).
2. A **host-side watcher** notices the flag and runs `deploy.sh`
   (`git pull` → `docker-compose down` → `docker-compose up -d --build`).
3. The UI shows an overlay, waits for the app to go down and come back, then
   reloads automatically.

Nothing rebuilds until you set up the host watcher below. Without it, the button
just writes a flag file that never gets acted on.

## One-time host setup

These steps run **on the home server**, once. They assume the repo lives at
`/opt/stacks/pyLoad-jellyfin-mover` — adjust the paths if yours differs.

### Option A — systemd path unit (recommended)

Watches the trigger folder and rebuilds the instant the flag appears.

```bash
# 1. Point the units at your repo location (skip if it's /opt/stacks/pyLoad-jellyfin-mover).
#    Edit the paths inside these two files first:
#      systemd/pyload-mover-update.path
#      systemd/pyload-mover-update.service

# 2. Install and enable.
sudo cp systemd/pyload-mover-update.path    /etc/systemd/system/
sudo cp systemd/pyload-mover-update.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now pyload-mover-update.path
```

Check it's armed and watch a run:

```bash
systemctl status pyload-mover-update.path
journalctl -u pyload-mover-update.service -f
```

### Option B — cron poller

Simpler, no systemd; checks once a minute.

```cron
* * * * * /opt/stacks/pyLoad-jellyfin-mover/update-watcher.sh >> /var/log/pyload-mover-update.log 2>&1
```

`update-watcher.sh` is a no-op when there's no flag, so polling is cheap.

## Permissions

The container runs as root and writes a root-owned flag file. The watcher must
be able to remove that file and run `docker` + `git` in the repo:

- **systemd** runs as root by default, which covers all of this.
- If you run docker as a **non-root user**, set `User=`/`Group=` in
  `pyload-mover-update.service` to that account, and make sure the repo and
  `update_trigger/` are writable by it.

## Security note

The web UI has **no authentication**, so anyone who can reach it can trigger a
host rebuild. The button has a confirmation dialog, but keep the UI on a trusted
LAN / behind your firewall — do not expose it to the public internet.

## Testing without the button

```bash
# Simulate what the button does, from the host:
touch /opt/stacks/pyLoad-jellyfin-mover/update_trigger/update.request
# systemd (Option A) rebuilds immediately; cron (Option B) within a minute.
# Or run the watcher directly:
./update-watcher.sh
```
