#!/usr/bin/env python3
"""
ONVIF-RTSP Bridge Main Entry Point
Converts RTSP streams to ONVIF Profile S compatible streams.
"""

import asyncio
import signal
import sys
import logging
from datetime import datetime

from src.config import Config
from src.onvif_server import OnvifServer
from src.discovery import WsDiscoveryService
from src.rtsp_proxy import RtspProxy
from src.utils.logging_config import setup_logging


logger = logging.getLogger(__name__)


class OnvifRtspBridge:
    """Main application class for ONVIF-RTSP Bridge."""
    
    def __init__(self):
        self.config = Config()
        self.onvif_server = None
        self.discovery_service = None
        self.rtsp_proxy = None
        self.running = False
        
    async def start(self):
        """Start all services."""
        logger.info("=" * 60)
        logger.info("ONVIF-RTSP Bridge Starting")
        logger.info("=" * 60)
        logger.info(f"Camera Name: {self.config.camera_name}")
        logger.info(f"Source RTSP: {self.config.rtsp_url_masked}")
        logger.info(f"ONVIF Port: {self.config.onvif_port}")
        logger.info(f"RTSP Proxy Port: {self.config.rtsp_proxy_port}")
        logger.info("=" * 60)
        
        self.running = True
        
        # Start RTSP Proxy
        self.rtsp_proxy = RtspProxy(self.config)
        await self.rtsp_proxy.start()
        logger.info(f"RTSP Proxy started on port {self.config.rtsp_proxy_port}")
        
        # Start ONVIF Server
        self.onvif_server = OnvifServer(self.config)
        await self.onvif_server.start()
        logger.info(f"ONVIF Server started on port {self.config.onvif_port}")
        
        # Start WS-Discovery if enabled
        if self.config.enable_discovery:
            self.discovery_service = WsDiscoveryService(self.config)
            await self.discovery_service.start()
            logger.info("WS-Discovery service started")
        
        logger.info("=" * 60)
        logger.info("ONVIF-RTSP Bridge is ready!")
        logger.info(f"ONVIF URL: http://{self.config.server_ip}:{self.config.onvif_port}/onvif/device_service")
        logger.info(f"RTSP URL: rtsp://{self.config.server_ip}:{self.config.rtsp_proxy_port}/stream")
        logger.info("=" * 60)
        
    async def stop(self):
        """Stop all services gracefully."""
        logger.info("Shutting down ONVIF-RTSP Bridge...")
        self.running = False
        
        if self.discovery_service:
            await self.discovery_service.stop()
            
        if self.onvif_server:
            await self.onvif_server.stop()
            
        if self.rtsp_proxy:
            await self.rtsp_proxy.stop()
            
        logger.info("Shutdown complete")
        
    async def run(self):
        """Run the bridge until interrupted."""
        await self.start()
        
        # Keep running until signaled to stop
        while self.running:
            await asyncio.sleep(1)


def handle_signal(bridge: OnvifRtspBridge, loop: asyncio.AbstractEventLoop):
    """Handle shutdown signals."""
    def signal_handler():
        logger.info("Received shutdown signal")
        asyncio.create_task(bridge.stop())
        loop.stop()
    return signal_handler


async def main():
    """Main entry point."""
    setup_logging()
    
    bridge = OnvifRtspBridge()
    loop = asyncio.get_event_loop()
    
    # Setup signal handlers
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, handle_signal(bridge, loop))
    
    try:
        await bridge.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        await bridge.stop()


if __name__ == "__main__":
    asyncio.run(main())
