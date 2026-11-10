@echo off
rem Run a Chalk command inside the Docker container: chalk test thrun-pr 4   (no arguments: start the app)
setlocal
cd /d "%~dp0"
if "%~1"=="" (docker compose up & goto :eof)
set RUNNING=
for /f %%i in ('docker compose ps -q --status running chalk 2^>nul') do set RUNNING=%%i
if defined RUNNING (docker compose exec chalk just %*) else (docker compose run --rm chalk just %*)
