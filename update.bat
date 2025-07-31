@echo off
setlocal enabledelayedexpansion

REM === Configuration ===
set REMOTE_USER=
set REMOTE_HOST=
set REMOTE_DIR=~/pifi
set EXCLUDES=keep.sh .env important.txt

echo Cleaning remote directory on %REMOTE_HOST%...

REM Build the find command with excludes
set EXCLUDE_PATTERN=

for %%F in (%EXCLUDES%) do (
    set EXCLUDE_PATTERN=!EXCLUDE_PATTERN! -not -name %%F
)

REM Compose the remote command (use single quotes for remote shell)
set REMOTE_CMD=find "%REMOTE_DIR%" -mindepth 1 %EXCLUDE_PATTERN% -exec rm -rf {} +

REM Run the remote command via SSH
ssh %REMOTE_USER%@%REMOTE_HOST% %REMOTE_CMD%

REM Copy local folder to remote
echo Transferring project folder to %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR% ...
scp -r . %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%

echo Done.
pause