# AI Daily Brief

Daily automated newsletter generator (AI + web hosting + marketing). Collects fresh stories, filters/ranks, writes a client-ready brief with citations (source links), and emails it to you via SendGrid.

## What it does
- Pulls items from curated RSS feeds (AI + hosting/cloud + marketing)
- Filters + ranks by relevance
- Deduplicates (won't resend the same URLs)
- Generates a daily newsletter (HTML + plain text) using OpenAI
- Emails to you (approval mode) via SendGrid
- Stores sent history in SQLite

## Quick start (local)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env with OPENAI_API_KEY + SENDGRID_API_KEY

python -m src.main
```

## Deploy to Azure App Service (quick)

This repo includes a `Procfile` and a GitHub Actions workflow for deploying to Azure App Service.

Replace `<APP_NAME>` and `<RG>` with your values before running the commands below.

```bash
# Login and select subscription
az login
az account set --subscription "<AZURE_SUBSCRIPTION_ID_OR_NAME>"

# Create resource group and App Service plan (Linux)
az group create --name <RG> --location eastus
az appservice plan create --name gemini-plan --resource-group <RG> --is-linux --sku B1

# Create the Web App (Python 3.12)
az webapp create --resource-group <RG> --plan gemini-plan --name <APP_NAME> --runtime "PYTHON|3.12"

# (Optional) Explicitly set the startup command (Procfile will usually be detected):
az webapp config set --resource-group <RG> --name <APP_NAME> --startup-file "gunicorn -w 4 -b 0.0.0.0:8000 src.app:app"

# Set required app settings (secrets)
az webapp config appsettings set --resource-group <RG> --name <APP_NAME> --settings \
	OPENAI_API_KEY="<value>" SENDGRID_API_KEY="<value>"

# Zip-deploy from repository root
zip -r deploy.zip . -x ".git/*"
az webapp deployment source config-zip --resource-group <RG> --name <APP_NAME> --src deploy.zip
```

GitHub Actions: The repo contains `.github/workflows/azure-webapp.yml`. Provide either `AZURE_WEBAPP_PUBLISH_PROFILE` (recommended) or `AZURE_CREDENTIALS` (service principal JSON) and `APP_NAME` as repository secrets to enable CI/CD.

## Setting GitHub Secrets

Add the following repository secrets (Settings → Secrets → Actions) so CI/CD and the app can access required values:

- `APP_NAME` — your Azure Web App name (globally unique).
- `AZURE_WEBAPP_PUBLISH_PROFILE` — recommended: copy the publish profile XML from the Azure Portal (App Service → Get publish profile) and paste it here.
- `AZURE_CREDENTIALS` — alternative: a Service Principal JSON created with `az ad sp create-for-rbac` (used by `azure/login@v1`).
- `OPENAI_API_KEY` — your OpenAI key.
- `SENDGRID_API_KEY` — your SendGrid API key.

Quick commands to obtain credentials (replace placeholders):

```bash
# Get a publish profile (returns XML):
az webapp deployment list-publishing-profiles --name <APP_NAME> --resource-group <RG> --query "[0].xml" -o tsv

# Or create a Service Principal (example JSON):
az ad sp create-for-rbac --name "github-deploy-<APP_NAME>" --role contributor --scopes /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<RG> -o json
```

Paste the resulting values into GitHub Secrets. The Actions workflow will use whichever credential you supply (`AZURE_WEBAPP_PUBLISH_PROFILE` preferred).
