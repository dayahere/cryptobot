# crypto-bot

Paper-first crypto trading bot with CCXT, pre-trained linear AI, Prometheus + Alertmanager + Grafana, Gmail alerts, and Terraform for OCI **ap-hyderabad-1**.

## Local quickstart
`
docker compose up -d --build
`
Grafana: http://localhost:3000  |  Prometheus: http://localhost:9090  |  Alertmanager: http://localhost:9093

## Configure exchange
- .env has EXCHANGE=binance and symbol list prefilled.
- When going live, set PAPER_TRADING=false and add API_KEY/SECRET.

## Terraform (OCI)
Edit infra/terraform/terraform.tfvars (prefilled region), then:
`
cd infra/terraform
terraform init
terraform apply
`

## CI/CD
- Tests & docker build on push.
- Push a commit with message starting deploy: to trigger SSH deploy (set repo secrets OCI_HOST, OCI_USER, OCI_SSH_PRIVATE_KEY).






Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\New-CryptoBotRepo.prefilled.CLEAN.ps1 `
  -Path .\crypto-bot `
  -ProjectName crypto-bot `
  -Exchange binance `
  -Region ap-hyderabad-1

What’s inside (key changes)
1) .env (pre‑filled)

EXCHANGE=binance               # or coindcx
SYMBOLS=BTC/USDT,ETH/USDT,LTC/USDT,XRP/USDT,SOL/USDT,BNB/USDT,ADA/USDT,UNI/USDT,ETC/USDT
TIMEFRAME=1m
PAPER_TRADING=true
BASE_CURRENCY=USDT
MAX_NOTIONAL_PER_TRADE=100
DAILY_LOSS_LIMIT_PCT=2
RISK_TARGET_ATR_PCT=0.5
GMAIL_FROM=you@gmail.com
GMAIL_TO=you@gmail.com
GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx
METRICS_PORT=9101
LOG_LEVEL=INFO

2) Prometheus + Alertmanager (+ Gmail)
Prometheus loads alert rules from infra/prometheus/alerts/alerts.yml:
BotNoHeartbeat: time() - bot_heartbeat_seconds > 300 (5 minutes stale)
ApiErrorsHigh: increase(api_errors_total[10m]) > 10 (5‑minute for)
CooldownActive: cooldown_active > 0 (daily loss limit tripped)
Alertmanager is included and pre‑configured to send email via Gmail SMTP; edit infra/alertmanager/config.yml with your to/from and Gmail App Password (Google requires 2FA + App Password; “Less secure apps” is deprecated). 2
3) Bot changes (risk/metrics)
Added a cooldown_active Prometheus gauge; the bot pauses trading for the rest of the UTC day when daily loss ≤ −2%.
Heartbeat and API error metrics already exposed for alerting.
Exchange tuning: CCXT instantiated with rate limiting, time‑drift adjustment; for Binance a recvWindow hint is included; markets auto‑loaded to access symbol filters. (CCXT abstracts per‑exchange specifics so your code stays portable.) 3
4) Terraform defaults (OCI)
infra/terraform/terraform.tfvars is pre‑filled with region = "ap-hyderabad-1"; just set your compartment_ocid, SSH key path, and GitHub repo URL, then:

cd infra/terraform
terraform init
terraform apply

(OCI India regions include Hyderabad (ap‑hyderabad‑1) and Mumbai (ap‑mumbai‑1); you picked Hyderabad.)

5) GitHub Actions (CI/CD)
On each push: Python tests + Docker build.
Deploy via SSH when commit message starts with deploy: to your OCI VM (secrets: OCI_HOST, OCI_USER, OCI_SSH_PRIVATE_KEY).


Quick runbook
Local (paper trading):
  
pwsh ./New-CryptoBotRepo.prefilled.ps1 -Path ./crypto-bot -Exchange binance
cd ./crypto-bot
docker compose up -d --build
# Grafana:     http://localhost:3000  (admin / GF_SECURITY_ADMIN_PASSWORD)
# Prometheus:  http://localhost:9090
# Alertmanager: http://localhost:9093


Grafan dashboard

🖥 1. Infrastructure Health
Purpose: Quick “are my core services alive?” check.
Panels:
- Prometheus / Grafana / Alertmanager / Bot → Each is a stat panel showing up{job="..."}.
- Green = service responding to Prometheus scrapes.
- Red = service down or unreachable.
- Tip: If one turns red, check that service’s container logs first — it’s often a network or container restart issue.

📊 2. Trading Health KPIs
Purpose: See if your trading system is functioning normally.
Panels:
- Equity → Current account equity from account_equity.
- API Errors (5m) → Graph of sum(increase(api_errors_total[5m])).
- Spikes here mean your bot is hitting broker/exchange API issues.
- Heartbeat age (s) → time() - bot_heartbeat_seconds.
- Should stay low; if it climbs, your bot isn’t sending heartbeats.
- Cooldown → cooldown_active flag.
- Green = trading allowed, Red = cooldown in effect.

📈 3. Trade Performance
Purpose: Track daily trading outcomes and profitability.
Panels:
- Daily Trades → Won / Lost / Breakeven counts over the last 24h.
- Daily Realised PnL → Profit or loss realised in the last 24h.
- Rolling Daily PnL → Current day’s running PnL.
How to use:
- Look for trends — e.g., rising losses + rising API errors could mean execution issues.
- Compare PnL with trade counts to see if fewer trades are more profitable.

🚨 4. Alert Feed
Purpose: Live feed of Prometheus alerts.
Panels:
- Live Alerts (Prometheus ALERTS) → Table showing alertname, alertstate, severity, instance, job, value.
- alertstate mapping:
- firing = active problem
- pending = condition met but not yet firing
- Threshold colors help you spot critical vs warning states.

🔍 How to interpret at a glance
- Top row all green → infra is healthy.
- Heartbeat low + API errors flat → bot is running smoothly.
- PnL positive + trades stable → strategy performing well.
- Alerts empty → no active incidents.


## 📟 Mission Control Dashboard – At‑a‑Glance

This guide explains how to interpret the Mission Control Grafana dashboard at a glance.

---

### 🖥 Infrastructure Health

| Panel | ✅ Normal | ⚠ Abnormal |
|-------|----------|------------|
| Prometheus / Grafana / Alertmanager / Bot | Green (1) – service up | Red (0) – service down, check logs/network |

---

### 📊 Trading Health KPIs

| Panel | ✅ Normal | ⚠ Abnormal |
|-------|----------|------------|
| Equity | Stable / rising | Sudden drop – check trades/account |
| API Errors (5m) | Flat / near zero | Spikes – API issues or bad requests |
| Heartbeat age (s) | Low (<60s) | Rising – bot stalled/disconnected |
| Cooldown | Green (0) | Red (1) – cooldown active |

---

### 📈 Trade Performance

| Panel | ✅ Normal | ⚠ Abnormal |
|-------|----------|------------|
| Daily Trades | Matches strategy | Zero – bot idle; Spike – runaway loop |
| Daily Realised PnL | Positive / expected loss | Large unexpected loss |
| Rolling Daily PnL | Smooth curve | Sharp drop – bad trade/market event |

---

### 🚨 Alert Feed

| Panel | ✅ Normal | ⚠ Abnormal |
|-------|----------|------------|
| Live Alerts | Empty / low severity | Firing critical alerts – investigate |

---

**Usage Tip:**  
Scan **Infrastructure Health** first → check **Heartbeat & API Errors** for bot status → review **PnL & Trades** for performance → confirm **Alerts** for active incidents.




1️⃣ Create the .oci folder and config file
In PowerShell:

powershell
mkdir $env:USERPROFILE\.oci
notepad $env:USERPROFILE\.oci\config
2️⃣ Add your OCI credentials to config
The file should look like this (replace with your actual values):

Code
[DEFAULT]
user=ocid1.user.oc1..aaaaaaaexample
fingerprint=12:34:56:78:90:ab:cd:ef:12:34:56:78:90:ab:cd:ef
key_file=C:\Users\dayan\.oci\oci_api_key.pem
tenancy=ocid1.tenancy.oc1..aaaaaaaexample
region=ap-mumbai-1
Notes:

    user and tenancy OCIDs come from the OCI Console.

    fingerprint is the fingerprint of your public API key in OCI.

    key_file points to your private API key file.

    region is your OCI region code (e.g., us-ashburn-1, ap-mumbai-1).

3️⃣ Generate an API key (if you don’t have one yet)
    In the OCI Console, go to User Settings → API Keys.

    Click Add API Key → Generate a new key pair.

    Download the private key (oci_api_key.pem) and save it to C:\Users\dayan\.oci\oci_api_key.pem.

    Copy the fingerprint and OCIDs into your config file.

4️⃣ Test your setup
Run:

powershell
oci os ns get
If the OCI CLI returns your namespace, the config is correct. Then retry:

powershell
terraform init
terraform plan
💡 Tip: If you don’t want to use the default C:\Users\dayan\.oci\config path, you can set the environment variable:

powershell
$env:OCI_CONFIG_FILE="K:\path\to\your\config"
If you want, I can give you a ready-to-use minimal config template with placeholders for exactly what Terraform’s OCI provider expects, so you can just fill in your details and run terraform plan without guessing.