# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ONVIF-RTSP Bridge converts any RTSP stream (e.g., HikVision camera substream) into an ONVIF Profile S compliant device. This allows non-ONVIF cameras to be discovered and used by Unifi Protect and other ONVIF-compatible NVRs.

## Build and Run Commands

```bash
# Build and start with Docker
docker-compose up -d

# Rebuild after code changes
docker-compose up -d --build

# View logs
docker-compose logs -f

# Run locally without Docker (requires Python 3.11+, FFmpeg)
pip install -r requirements.txt
python -m src.main
```

## Configuration

All configuration is via environment variables (see `.env.example`). Key settings:
- `RTSP_URL`: Source camera RTSP stream URL (required)
- `ONVIF_PORT`: ONVIF service port (default: 8080)
- `RTSP_PROXY_PORT`: Proxied stream port (default: 8554)
- `ONVIF_USERNAME`/`ONVIF_PASSWORD`: Credentials for ONVIF clients
- `SERVER_IP`: Leave empty for auto-detection

## Architecture

```
src/
├── main.py              # Entry point, orchestrates all services
├── config.py            # Config dataclass loading from env vars
├── onvif_server.py      # aiohttp HTTP server routing SOAP requests
├── discovery.py         # WS-Discovery (UDP multicast on port 3702)
├── rtsp_proxy.py        # mediamtx + FFmpeg RTSP re-streaming
├── services/
│   ├── device_service.py  # ONVIF Device Service (GetDeviceInformation, GetCapabilities, etc.)
│   ├── media_service.py   # ONVIF Media Service (GetProfiles, GetStreamUri, etc.)
│   └── events_service.py  # ONVIF Events Service (minimal implementation)
└── utils/
    ├── soap_utils.py      # SOAP envelope parsing and response wrapping
    └── logging_config.py  # Colorlog configuration
```

**Key flows:**
1. `OnvifRtspBridge` starts three async services: RTSP proxy, ONVIF HTTP server, WS-Discovery
2. ONVIF clients send SOAP requests to `/onvif/device_service` or `/onvif/media_service`
3. `GetStreamUri` returns the proxied RTSP URL (`rtsp://server:8554/stream`)
4. RTSP proxy uses mediamtx as RTSP server + FFmpeg to relay the source stream

## ONVIF Protocol Notes

- SOAP requests come as HTTP POST with XML body
- Action is extracted from SOAP body element name (e.g., `GetDeviceInformation`)
- Services respond with wrapped XML using `SoapHandler.wrap_response()`
- WS-Discovery uses UDP multicast (239.255.255.250:3702) for Hello/Bye/ProbeMatch

## Docker Requirements

- `network_mode: host` is required for WS-Discovery multicast to work
- mediamtx (RTSP server) and FFmpeg are installed in the container
- mediamtx serves RTSP on port 8554, FFmpeg pulls from source and pushes to mediamtx
- Health check hits `/onvif/device_service` endpoint
