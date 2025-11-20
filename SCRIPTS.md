Automation scripts for ETL-RabbitMQ project

I added a set of PowerShell scripts to `scripts/` to automate demo steps on Windows.

Scripts included:

- `scripts\run-full.ps1` : build images, start services, load schema, run producer, run transform (one command demo)
- `scripts\load-schema.ps1` : load `create_tables.sql` into the MySQL container
- `scripts\run-producer.ps1` : run the producer one-off container
- `scripts\run-consumers.ps1` : start both consumer services in background
- `scripts\run-transform.ps1` : run the transform container one-off
- `scripts\stop-all.ps1` : stop and remove containers (`docker compose down`)

Usage (PowerShell):

```powershell
# Run full demo (build, start, load schema, produce, transform)
.\scripts\run-full.ps1

# Or run step-by-step:
.\scripts\load-schema.ps1
.\scripts\run-consumers.ps1
.\scripts\run-producer.ps1
.\scripts\run-transform.ps1

# Stop all
.\scripts\stop-all.ps1
```

Notes:

- Scripts assume the default MySQL root password `rootpassword` as in `.env`. If you changed credentials, edit the scripts accordingly.
- Scripts use short sleeps to wait for services; for more robust demos replace sleeps with health checks.
- These scripts are for Windows PowerShell. For Linux/macOS you can run equivalent `docker compose` commands or I can add bash scripts if needed.
