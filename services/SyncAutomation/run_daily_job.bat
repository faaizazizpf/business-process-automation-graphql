@echo off
cd C:\zoe_data_sync
git checkout buxfer_sync
call venv\Scripts\activate
cd services\SyncAutomation
python .\RunSyncAccount.py --mode now