# ONVIF-RTSP Bridge

Convert any RTSP stream (like HikVision camera substream) to an ONVIF Profile S compliant device that can be detected and used by Unifi Protect and other ONVIF-compatible NVRs.

## Features

- **ONVIF Profile S Compliant**: Full implementation of required ONVIF services
- **WS-Discovery**: Automatic device discovery on your network
- **RTSP Proxy**: Transparent stream forwarding with minimal latency
- **Docker Ready**: Easy deployment with Docker Compose
- **Unifi Protect Compatible**: Tested with Unifi Protect for seamless integration

## Quick Start

### 1. Clone/Copy the files

Ensure all files are in place in your project directory.

### 2. Configure your camera

Copy the example environment file and edit it:

```bash
cp .env.example .env
nano .env
```

Update the following key settings:

```env
# Your HikVision camera RTSP URL (substream)
RTSP_URL=rtsp://admin:yourpassword@192.168.1.100:554/Streaming/Channels/102

# ONVIF credentials (for Unifi Protect to use)
ONVIF_USERNAME=admin
ONVIF_PASSWORD=admin123

# Optional: Set if auto-detection fails
SERVER_IP=192.168.1.50
```

### 3. Start the bridge

**Option A: Docker (Linux recommended)**

```bash
docker-compose up -d
```

**Option B: Run locally (macOS/Linux)**

Running locally is recommended on macOS since Docker Desktop doesn't support host networking (required for WS-Discovery).

1. Install dependencies:

```bash
# macOS
brew install ffmpeg mediamtx

# Ubuntu/Debian
sudo apt install ffmpeg
# Download mediamtx from https://github.com/bluenviron/mediamtx/releases
```

2. Create Python virtual environment and install packages:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Run the bridge:

```bash
source venv/bin/activate
python -m src.main
```

4. To stop:

```bash
pkill -f "python -m src.main"
pkill -f mediamtx
```

### 4. Add to Unifi Protect

1. Open Unifi Protect
2. Go to **Settings** > **System** > **Cameras**
3. Click **Add Device**
4. Select **ONVIF** as the type
5. The bridge should be auto-discovered, or manually enter:
   - IP: Your server IP
   - Port: 8080 (default)
   - Username: admin (or your ONVIF_USERNAME)
   - Password: admin123 (or your ONVIF_PASSWORD)

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `CAMERA_NAME` | HikVision Camera | Display name in ONVIF discovery |
| `CAMERA_MANUFACTURER` | HikVision | Manufacturer shown in device info |
| `CAMERA_MODEL` | DS-2CD2xxx | Model shown in device info |
| `RTSP_URL` | (required) | Source RTSP stream URL |
| `ONVIF_PORT` | 8080 | ONVIF service port |
| `ONVIF_USERNAME` | admin | ONVIF authentication username |
| `ONVIF_PASSWORD` | admin123 | ONVIF authentication password |
| `RTSP_PROXY_PORT` | 8554 | Proxied RTSP stream port |
| `SERVER_IP` | (auto-detect) | Server IP address |
| `STREAM_WIDTH` | 1280 | Video width (match your substream) |
| `STREAM_HEIGHT` | 720 | Video height (match your substream) |
| `STREAM_FPS` | 15 | Frame rate |
| `STREAM_BITRATE` | 2048 | Bitrate in kbps |
| `ENABLE_DISCOVERY` | true | Enable WS-Discovery |

## HikVision RTSP URL Formats

Common RTSP URL patterns for HikVision cameras:

```
# Main stream (high quality)
rtsp://username:password@ip:554/Streaming/Channels/101

# Sub stream (lower quality, ideal for NVR)
rtsp://username:password@ip:554/Streaming/Channels/102

# Third stream
rtsp://username:password@ip:554/Streaming/Channels/103

# Alternative format
rtsp://username:password@ip:554/cam/realmonitor?channel=1&subtype=1
```

## Troubleshooting

### Camera not discovered

1. On macOS, run locally instead of Docker (Docker Desktop doesn't support host networking)
2. Ensure `network_mode: host` is set in docker-compose.yml (Linux only)
3. Check if port 3702 (WS-Discovery) is not blocked
4. Verify the bridge is running: `docker-compose logs -f`

### Stream not working

1. Test the source RTSP URL with VLC first
2. Check FFmpeg logs: `docker-compose logs onvif-bridge | grep ffmpeg`
3. Verify network connectivity to the camera

### Authentication issues

1. Ensure ONVIF credentials match what you enter in Unifi Protect
2. Some NVRs require specific authentication methods

### View logs

```bash
# Live logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100
```

## Architecture

```
┌──────────────┐      ┌─────────────────────┐      ┌──────────────┐
│  HikVision   │ RTSP │   ONVIF-RTSP        │ ONVIF│   Unifi      │
│   Camera     │ ───► │     Bridge          │ ◄──► │  Protect     │
│ (substream)  │      │  (Docker Container) │      │              │
└──────────────┘      └─────────────────────┘      └──────────────┘
                              │
                              ▼
                      ┌───────────────┐
                      │ WS-Discovery  │
                      │ (Auto-detect) │
                      └───────────────┘
```

## Running Multiple Cameras

Create separate services in docker-compose.yml for each camera:

```yaml
services:
  camera1:
    build: .
    environment:
      - CAMERA_NAME=Front Door
      - RTSP_URL=rtsp://admin:pass@192.168.1.101:554/Streaming/Channels/102
      - ONVIF_PORT=8080
      - RTSP_PROXY_PORT=8554
    network_mode: host

  camera2:
    build: .
    environment:
      - CAMERA_NAME=Back Yard
      - RTSP_URL=rtsp://admin:pass@192.168.1.102:554/Streaming/Channels/102
      - ONVIF_PORT=8081
      - RTSP_PROXY_PORT=8555
    network_mode: host
```

## Security Notes

- Use strong passwords for both HikVision camera and ONVIF credentials
- Consider running behind a firewall
- RTSP credentials are stored in environment variables (use Docker secrets for production)
- WS-Discovery broadcasts on the local network

## License

MIT License - Feel free to use and modify.

## Contributing

Pull requests welcome! Please test with Unifi Protect before submitting.
