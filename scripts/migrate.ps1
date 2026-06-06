Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

docker compose exec backend python -m app.db.migrate
