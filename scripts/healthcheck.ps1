Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$frontend = Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8900
$backend = Invoke-RestMethod http://127.0.0.1:8900/api/health
$dashboard = Invoke-RestMethod http://127.0.0.1:8900/api/dashboard

[PSCustomObject]@{
    FrontendStatus = $frontend.StatusCode
    BackendStatus = $backend.status
    BackendVersion = $backend.version
    OrderCount = $dashboard.order_count
    TaskCount = $dashboard.task_count
}
