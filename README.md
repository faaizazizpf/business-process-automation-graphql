# Business Process Automation GraphQL

This repository contains automation and GraphQL tooling for business process integrations. The part you run regularly is the SyncAutomation service. This README focuses on the daily-run batch script you mentioned:

File: `services/SyncAutomation/run_daily_job.bat`

## Overview

The `run_daily_job.bat` script is a simple Windows batch wrapper that:
- switches to the repository directory (expected at `C:\zoe_data_sync`),
- checks out the `buxfer_sync` branch,
- activates the Python virtual environment (`venv`),
- runs `services/SyncAutomation/RunSyncAccount.py` with `--mode now` to perform an immediate sync.

If you only need to run this batch file, the instructions below will get you there.

## Prerequisites

- Windows (the batch file is Windows-specific).
- Git installed and on your PATH: https://git-scm.com/
- Python 3.x installed on the system used to create the virtual environment (the repo expects a `venv` folder).
- The repository cloned locally at `C:\zoe_data_sync` (or edit the batch file to point to your location).
- A Python virtual environment created under the repo root as `venv` (so `venv\Scripts\activate` exists).
- Any environment variables or credentials required by `RunSyncAccount.py` must be configured (see Troubleshooting).

## Batch file content (for reference)

The batch file currently contains:
```batch
@echo off
cd C:\zoe_data_sync
git checkout buxfer_sync
call venv\Scripts\activate
cd services\SyncAutomation
python .\RunSyncAccount.py --mode now
```

## How to run manually

1. Open Command Prompt as the user that owns the files (or as Administrator if required).
2. Change directory (optional):
   - If you are not already at `C:\zoe_data_sync`, either:
     - clone the repo there: `git clone https://github.com/faaizazizpf/business-process-automation-graphql C:\zoe_data_sync`, or
     - edit the batch file to point to your local path.
3. Run the batch file:
   - Double-click `services\SyncAutomation\run_daily_job.bat` in Explorer, or
   - From cmd:
     cd C:\zoe_data_sync
     services\SyncAutomation\run_daily_job.bat

Running the batch file will:
- checkout the `buxfer_sync` branch,
- activate the venv,
- run the sync script immediately.

## Scheduling the batch file (Task Scheduler)

To run the batch daily via Windows Task Scheduler:

1. Open Task Scheduler.
2. Create Task -> Name it (e.g., "Zoe Data Daily Sync").
3. Trigger: Daily at your desired time.
4. Action: Start a program:
   - Program/script: C:\Windows\System32\cmd.exe
   - Add arguments: /c "C:\zoe_data_sync\services\SyncAutomation\run_daily_job.bat"
5. Configure to run whether user is logged in or not, and provide credentials if needed.
6. Enable "Run with highest privileges" if the job needs elevated access.

Alternatively, schedule from the command line:
schtasks /Create /SC DAILY /TN "ZoeDataDailySync" /TR "\"C:\zoe_data_sync\services\SyncAutomation\run_daily_job.bat\"" /ST 02:00

Adjust the time and paths to suit your environment.

## Troubleshooting

- "git checkout" fails:
  - Ensure `C:\zoe_data_sync` exists and is a valid git repo.
  - Make sure branch `buxfer_sync` exists: `git branch -a` or `git fetch --all`.
- Virtualenv activation fails:
  - Confirm `venv\Scripts\activate` exists. If not, create the virtualenv:
    - python -m venv venv
    - venv\Scripts\activate
    - pip install -r requirements.txt (if present)
- Python script errors:
  - Run the Python step interactively to see error details:
    - Open cmd, activate venv, then:
      cd C:\zoe_data_sync\services\SyncAutomation
      python RunSyncAccount.py --mode now
  - Check for missing environment variables or credentials the script expects.
- Logging:
  - If the script writes logs, check `services/SyncAutomation` or other configured log locations.
  - Consider modifying the batch file to redirect output to a log: 
    - Add at the end: python .\RunSyncAccount.py --mode now >> C:\zoe_data_sync\sync_daily.log 2>&1

## Security and credentials

- Avoid storing plaintext credentials in repository files.
- Use environment variables, OS credential stores, or secure vault solutions.
- If credentials are required by the sync script, ensure the account running the scheduled task has access to them.

## Contributing and changes

If you change paths, branch names, or the virtualenv name, update `services/SyncAutomation/run_daily_job.bat` accordingly. If you would like, I can:
- add a small wrapper that logs output with timestamps,
- create an example Windows Task Scheduler export (.xml),
- or update the batch file to accept a configurable repo path.

## Contact / Maintainer

Repo owner: @faaizazizpf

License: (add license details here if desired)

---

If you want, I can create and commit this README.md into the repository for you, or update the batch file to include output logging and configurable path options. Which would you like me to do next?
