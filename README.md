# meraki-exporter

Prometheus exporter for **Cisco Meraki appliance performance scores**.
Optionally sends alerts to **Google Chat** when performance degrades.

## How it works

```
Meraki API  →  exporter  →  /metrics  →  Prometheus  →  Grafana
                   ↓
              Google Chat (alert / reminder / resolved)
```

- Scrapes `perfScore` from each configured Meraki device via the Meraki API
- Exposes it as a Prometheus gauge: `meraki_performance{device="hn"}`
- Sends Google Chat alerts when score exceeds `ALERT_THRESHOLD`
- Sends reminders every `REMINDER_INTERVAL` minutes if still above threshold
- Sends a resolved message when score drops back to normal

## Quick Start

```bash
# 1. Copy env template
cp .env.example .env

# 2. Fill in your values
vi .env

# 3. Run
docker compose up -d
```

Metrics available at: `http://localhost:8000/metrics`
Health check: `http://localhost:8000/healthz`

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MERAKI_API_KEY` | yes | — | Meraki Dashboard API key |
| `SERIAL_<label>` | yes (≥1) | — | Device serial, e.g. `SERIAL_HN=Q2AB-XXXX` |
| `GOOGLE_CHAT_WEBHOOK` | no | — | Google Chat webhook URL for alerts |
| `ALERT_THRESHOLD` | no | `75` | Score (0–100) above which an alert fires |
| `REMINDER_INTERVAL` | no | `30` | Minutes between repeat alerts |
| `TRACKING` | no | `false` | Send startup notification (`true` to enable) |

### Adding devices

Add one `SERIAL_` variable per device in `.env`:

```env
SERIAL_HN=Q2AB-XXXX-XXXX
SERIAL_HCM=Q2AB-YYYY-YYYY
SERIAL_AWS=Q2AB-ZZZZ-ZZZZ
```

Each becomes a label on the metric: `meraki_performance{device="hn"}`.

## Docker

### Run pre-built image

```bash
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name meraki-exporter \
  0xphuong/meraki-exporter:latest
```

### Build locally

```bash
docker build -t meraki-exporter ./perfScore
docker run -d -p 8000:8000 --env-file .env meraki-exporter
```

## Prometheus scrape config

```yaml
scrape_configs:
  - job_name: meraki
    static_configs:
      - targets: ['meraki-exporter:8000']
    scrape_interval: 60s
```

## Grafana

Import dashboard — query example:

```promql
meraki_performance{device=~".*"}
```

Add alert rule: fire when `meraki_performance > 75` for 5m.

## Project Structure

```
meraki-exporter/
├── perfScore/
│   ├── meraki-exporter-multi.py    ← main exporter (current)
│   ├── meraki-exporter-multi-v1.0.0.py  ← original v1 (archived)
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml
├── .env.example
├── .gitignore
├── CHANGELOG.md
└── LICENSE
```

## Security

- **Never commit `.env`** — it contains your API key (`.gitignore` covers this)
- Get your Meraki API key from: **Dashboard → My Profile → API access**
- Rotate the key immediately if it was ever committed to git

## Changelog

See [CHANGELOG.md](./CHANGELOG.md).

## License

[MIT](./LICENSE)
