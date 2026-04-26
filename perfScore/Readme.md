# Meraki Exporter

## Features

- Retrieves performance metrics from Cisco Meraki devices
- Provides metrics for Prometheus
- Sends alerts via Google Chat

## Requirements

- Docker
- Meraki API Key
- Google Chat Webhook URL

## Installation and Running with Docker

To run the Meraki Exporter using Docker, use the following command:

```bash
docker run -d \
  -p 8000:8000 \
  -e MERAKI_API_KEY=<your_meraki_api_key> \
  -e GOOGLE_CHAT_WEBHOOK=<your_google_chat_webhook_url> \
  -e ALERT_THRESHOLD=70 \
  -e REMINDER_INTERVAL=30 \
  -e SERIAL_AWS=<serial_number_1> \
  -e SERIAL_HCM=<serial_number_2> \
  -e SERIAL_DEVICE3=<serial_number_3> \
  --name meraki-exporter \
  binhphuong/meraki-perf-exporter:latest