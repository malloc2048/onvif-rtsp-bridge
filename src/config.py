"""Configuration management for ONVIF-RTSP Bridge."""

import os
import socket
import uuid
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# Load .env file
load_dotenv()


def get_local_ip() -> str:
    """Get the local IP address of this machine."""
    try:
        # Create a socket to determine the outgoing IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


@dataclass
class Config:
    """Application configuration loaded from environment variables."""
    
    # Camera identification
    camera_name: str = field(default_factory=lambda: os.getenv("CAMERA_NAME", "ONVIF Camera"))
    camera_manufacturer: str = field(default_factory=lambda: os.getenv("CAMERA_MANUFACTURER", "Generic"))
    camera_model: str = field(default_factory=lambda: os.getenv("CAMERA_MODEL", "RTSP-Bridge"))
    camera_serial: str = field(default_factory=lambda: os.getenv("CAMERA_SERIAL", str(uuid.uuid4())[:8].upper()))
    camera_firmware: str = "1.0.0"
    
    # Hardware ID (unique identifier for this device)
    hardware_id: str = field(default_factory=lambda: os.getenv("HARDWARE_ID", str(uuid.uuid4())))
    
    # Source RTSP configuration
    rtsp_url: str = field(default_factory=lambda: os.getenv("RTSP_URL", "rtsp://admin:admin@192.168.1.100:554/Streaming/Channels/102"))
    rtsp_username: str = field(default_factory=lambda: os.getenv("RTSP_USERNAME", "admin"))
    rtsp_password: str = field(default_factory=lambda: os.getenv("RTSP_PASSWORD", "admin"))
    
    # ONVIF server configuration
    onvif_port: int = field(default_factory=lambda: int(os.getenv("ONVIF_PORT", "8080")))
    onvif_username: str = field(default_factory=lambda: os.getenv("ONVIF_USERNAME", "admin"))
    onvif_password: str = field(default_factory=lambda: os.getenv("ONVIF_PASSWORD", "admin123"))
    
    # Network configuration
    server_ip: str = field(default_factory=lambda: os.getenv("SERVER_IP", "") or get_local_ip())
    rtsp_proxy_port: int = field(default_factory=lambda: int(os.getenv("RTSP_PROXY_PORT", "8554")))
    
    # Stream configuration
    stream_width: int = field(default_factory=lambda: int(os.getenv("STREAM_WIDTH", "1280")))
    stream_height: int = field(default_factory=lambda: int(os.getenv("STREAM_HEIGHT", "720")))
    stream_fps: int = field(default_factory=lambda: int(os.getenv("STREAM_FPS", "15")))
    stream_bitrate: int = field(default_factory=lambda: int(os.getenv("STREAM_BITRATE", "2048")))
    
    # Discovery configuration
    enable_discovery: bool = field(default_factory=lambda: os.getenv("ENABLE_DISCOVERY", "true").lower() == "true")
    
    # Profile tokens
    profile_token: str = "MainProfile"
    video_source_token: str = "VideoSource_1"
    video_encoder_token: str = "VideoEncoder_1"
    
    @property
    def rtsp_url_masked(self) -> str:
        """Return RTSP URL with password masked."""
        url = self.rtsp_url
        if "@" in url and "://" in url:
            # Mask the password in the URL
            prefix = url.split("://")[0] + "://"
            rest = url.split("://")[1]
            if "@" in rest:
                auth = rest.split("@")[0]
                host = rest.split("@")[1]
                if ":" in auth:
                    user = auth.split(":")[0]
                    return f"{prefix}{user}:****@{host}"
        return url
    
    @property
    def onvif_service_url(self) -> str:
        """Get the base ONVIF service URL."""
        return f"http://{self.server_ip}:{self.onvif_port}"
    
    @property
    def proxy_rtsp_url(self) -> str:
        """Get the proxied RTSP stream URL."""
        return f"rtsp://{self.server_ip}:{self.rtsp_proxy_port}/stream"
    
    @property
    def device_service_url(self) -> str:
        """Get the device service URL."""
        return f"{self.onvif_service_url}/onvif/device_service"
    
    @property
    def media_service_url(self) -> str:
        """Get the media service URL."""
        return f"{self.onvif_service_url}/onvif/media_service"
    
    @property
    def events_service_url(self) -> str:
        """Get the events service URL."""
        return f"{self.onvif_service_url}/onvif/events_service"
    
    def validate(self):
        """Validate configuration."""
        errors = []
        
        if not self.rtsp_url:
            errors.append("RTSP_URL is required")
            
        if not self.server_ip:
            errors.append("Could not determine server IP")
            
        if self.onvif_port < 1 or self.onvif_port > 65535:
            errors.append("ONVIF_PORT must be between 1 and 65535")
            
        if self.rtsp_proxy_port < 1 or self.rtsp_proxy_port > 65535:
            errors.append("RTSP_PROXY_PORT must be between 1 and 65535")
            
        if errors:
            raise ValueError("Configuration errors: " + "; ".join(errors))
