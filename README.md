# Brother-User-Print-Logging
 A TrueNAS SCALE custom app to download brother printer usage CSVs, process them, and publish usage data to MQTT.

 # PrintLogging App for TrueNAS SCALE

This project contains a Python script and Dockerfile to run a custom TrueNAS SCALE app that:

- Logs into a network printer’s web interface
- Downloads a CSV usage log file
- Renames and stores the CSV logs in a mounted directory
- Parses the CSV and publishes print usage data (total, black & white, color) per user to an MQTT broker

## Features

- Headless Firefox browser automation with Selenium for downloading CSV logs
- Configurable MQTT broker credentials and topics via environment variables
- Configurable user mapping from printer usernames to friendly user IDs using JSON environment variable
- Runs inside a lightweight Docker container for easy deployment on TrueNAS SCALE

## Getting Started

### Prerequisites

- TrueNAS SCALE with Docker/Apps support
- MQTT broker accessible from TrueNAS SCALE
- Network printer with web interface supporting CSV export

### Installation

1. Clone this repository or use it directly in TrueNAS SCALE Apps "Install Custom App" using the GitHub repo URL.
2. Customize environment variables such as:

```bash
- MQTT_BROKER
- MQTT_PORT
- MQTT_USERNAME
- MQTT_PASSWORD
- PRINTER_URL
- PRINTER_PASSWORD
- USER_MAPPING_JSON
- DOWNLOADS_FOLDER
- DESTINATION_FOLDER

