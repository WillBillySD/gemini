# Site Monitor + SMS Alerts

Watch any website or RSS feed for new posts and get an instant SMS text alert via Twilio.

## What it does
- Add any RSS/Atom feed or web page URL to monitor
- Detects new posts/content changes automatically
- Texts your cell phone the moment something new appears
- Deduplicates — never alerts twice for the same post
- Simple Bootstrap web UI to manage sites and view alert history
- Runs on a schedule (default every 30 min) + manual "Check Now" button

## Quick start (local)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env — fill in your Twilio credentials and cell number

python monitor.py
# → http://localhost:5000
```

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `TWILIO_ACCOUNT_SID` | Yes | From [console.twilio.com](https://console.twilio.com) |
| `TWILIO_AUTH_TOKEN` | Yes | From Twilio console |
| `TWILIO_FROM_NUMBER` | Yes | Your Twilio phone number (e.g. `+15551234567`) |
| `ALERT_TO_NUMBER` | Yes | Your cell phone number to receive texts |
| `CHECK_INTERVAL_MINUTES` | No | How often to check sites (default: `30`) |
| `SECRET_KEY` | No | Flask session secret (any random string) |
| `PORT` | No | Web server port (default: `5000`) |

## Deploy to Azure App Service

```bash
# Login and select subscription
az login
az account set --subscription "<AZURE_SUBSCRIPTION_ID_OR_NAME>"

# Create resource group and App Service plan (Linux)
az group create --name <RG> --location eastus
az appservice plan create --name site-monitor-plan --resource-group <RG> --is-linux --sku B1

# Create the Web App (Python 3.12)
az webapp create --resource-group <RG> --plan site-monitor-plan --name <APP_NAME> --runtime "PYTHON|3.12"

# Set required app settings (Twilio credentials)
az webapp config appsettings set --resource-group <RG> --name <APP_NAME> --settings \
  TWILIO_ACCOUNT_SID="<value>" \
  TWILIO_AUTH_TOKEN="<value>" \
  TWILIO_FROM_NUMBER="<value>" \
  ALERT_TO_NUMBER="<value>" \
  SECRET_KEY="<random-string>"

# Zip-deploy
zip -r deploy.zip . -x ".git/*" "*.pyc" "__pycache__/*" "data/*.db"
az webapp deployment source config-zip --resource-group <RG> --name <APP_NAME> --src deploy.zip
```

## CI/CD via GitHub Actions

The repo includes `.github/workflows/azure-webapp.yml`. Push to `main` to auto-deploy.

Add these repository secrets (Settings → Secrets → Actions):

| Secret | Description |
|---|---|
| `APP_NAME` | Your Azure Web App name |
| `AZURE_RG` | Your Azure resource group name |
| `AZURE_WEBAPP_PUBLISH_PROFILE` | Publish profile XML from Azure Portal *(recommended)* |
| `AZURE_CREDENTIALS` | Service principal JSON *(alternative)* |
| `TWILIO_ACCOUNT_SID` | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `TWILIO_FROM_NUMBER` | Twilio phone number |
| `ALERT_TO_NUMBER` | Your cell phone number |
| `SECRET_KEY` | Flask secret key |
| `CHECK_INTERVAL_MINUTES` | Check frequency in minutes (default 30) |

```bash
# Get publish profile:
az webapp deployment list-publishing-profiles --name <APP_NAME> --resource-group <RG> --query "[0].xml" -o tsv

# Or create a Service Principal:
az ad sp create-for-rbac --name "github-deploy-<APP_NAME>" --role contributor \
  --scopes /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<RG> -o json
```
