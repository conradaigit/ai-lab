# SECRETS_INVENTORY

Status: Initial policy document  
Purpose: Define how secrets are handled in local development, in the repo, and later in cloud environments.

---

# 1. Core rule

Secrets must never be committed to Git / GitHub.

The repo may document:

- secret names
- where they are used
- which environment uses them
- who or what system owns them

The repo must not contain:

- actual API keys
- passwords
- tokens
- private certificates
- private broker credentials
- private cloud credentials

---

# 2. Current secrets pattern

## 2.1 Local development

Local development should use:

- environment variables
- optional non-committed `.env` files when needed

Any `.env` file must remain local-only and untracked.

## 2.2 Repo behavior

The repo should only store documentation of:

- secret variable names
- purpose of each secret
- where each secret is injected
- which workflows depend on it

## 2.3 Cloud behavior

Cloud-hosted secrets should later move to:

- Azure Key Vault

This is the intended pattern for:

- Azure-hosted jobs
- cloud workflows
- broker-facing automation
- remote-control or machine-control services later

---

# 3. Initial secret classes

## 3.1 LLM / AI provider secrets

Examples:

- OpenAI API keys
- Anthropic API keys
- other model-provider credentials later

## 3.2 Azure secrets

Examples:

- storage connection strings
- service principal credentials
- managed identity related references
- key vault references

## 3.3 Broker / trading secrets

Examples:

- IBKR-related credentials
- account identifiers
- gateway or service auth values

## 3.4 Infrastructure / remote control secrets

Examples:

- machine control endpoints
- MQTT credentials later
- remote service tokens
- webhook signing secrets

---

# 4. Ownership fields to document

For each real secret later, document:

- `name`
- `purpose`
- `used_by`
- `environment`
- `injection_method`
- `owner`
- `rotation_notes`

---

# 5. Current initial inventory

## OPENAI_API_KEY
- purpose: authenticate Codex CLI, Codex extension, or other OpenAI tooling if needed
- used_by: local agent tooling and later cloud agent jobs
- environment: local now, cloud later
- injection_method: environment variable
- owner: operator

## ANTHROPIC_API_KEY
- purpose: authenticate Claude tooling if used
- used_by: optional local or cloud workflows
- environment: local now, cloud later
- injection_method: environment variable
- owner: operator

## AZURE_STORAGE_CONNECTION_STRING
- purpose: access Azure storage during development if connection-string auth is used
- used_by: artifact upload/download helpers
- environment: local development only unless explicitly required
- injection_method: environment variable
- owner: operator

## AZURE_KEY_VAULT_URI
- purpose: identify the Azure Key Vault used for cloud secret retrieval later
- used_by: cloud jobs and services
- environment: cloud later
- injection_method: environment variable or config reference
- owner: operator

## IBKR_* (placeholder family)
- purpose: broker authentication and integration
- used_by: later paper/live trading workflows only
- environment: not yet active
- injection_method: to be defined before broker integration
- owner: operator

---

# 6. Rules before higher-risk integration

Before Azure automation, IBKR integration, CNC control, printing control, or other higher-risk domains are activated:

- every required secret must be named here
- every injection method must be documented
- local vs cloud handling must be explicit
- no secret value may be stored in repo files
- production-like secrets should not be reused casually in development

---

# 7. Immediate rule of thumb

- local dev -> environment variables, optional local `.env`
- repo -> secret names and usage docs only
- cloud -> Azure Key Vault later
