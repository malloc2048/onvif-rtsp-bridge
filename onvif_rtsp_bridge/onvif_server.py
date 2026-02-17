"""ONVIF Server implementation for Profile S compliance."""

import logging
from datetime import datetime, timezone
from aiohttp import web
from lxml import etree

from onvif_rtsp_bridge.config import Config
from onvif_rtsp_bridge.services.device_service import DeviceService
from onvif_rtsp_bridge.services.media_service import MediaService
from onvif_rtsp_bridge.services.events_service import EventsService
from onvif_rtsp_bridge.utils.soap_utils import SoapHandler

logger = logging.getLogger(__name__)


class OnvifServer:
    """ONVIF Profile S compliant server."""
    
    def __init__(self, config: Config):
        self.config = config
        self.app = web.Application()
        self.runner = None
        self.site = None
        
        # Initialize services
        self.soap_handler = SoapHandler(config)
        self.device_service = DeviceService(config, self.soap_handler)
        self.media_service = MediaService(config, self.soap_handler)
        self.events_service = EventsService(config, self.soap_handler)
        
        # Setup routes
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup HTTP routes for ONVIF services."""
        self.app.router.add_post('/onvif/device_service', self._handle_device_service)
        self.app.router.add_post('/onvif/media_service', self._handle_media_service)
        self.app.router.add_post('/onvif/events_service', self._handle_events_service)
        
        # GET endpoints for service discovery
        self.app.router.add_get('/onvif/device_service', self._handle_wsdl_request)
        self.app.router.add_get('/onvif/media_service', self._handle_wsdl_request)
        self.app.router.add_get('/onvif/events_service', self._handle_wsdl_request)
        
        # Health check endpoint
        self.app.router.add_get('/health', self._handle_health)
        
    async def start(self):
        """Start the ONVIF server."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, '0.0.0.0', self.config.onvif_port)
        await self.site.start()
        logger.info(f"ONVIF server listening on port {self.config.onvif_port}")
        
    async def stop(self):
        """Stop the ONVIF server."""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("ONVIF server stopped")
        
    async def _handle_device_service(self, request: web.Request) -> web.Response:
        """Handle Device Service SOAP requests."""
        try:
            body = await request.read()
            logger.debug(f"Device service request: {body[:500]}")
            
            response = await self.device_service.handle_request(body)
            
            return web.Response(
                body=response,
                content_type='application/soap+xml', charset='utf-8'
            )
        except Exception as e:
            logger.exception(f"Error handling device service request: {e}")
            return self._soap_fault("Server", str(e))
            
    async def _handle_media_service(self, request: web.Request) -> web.Response:
        """Handle Media Service SOAP requests."""
        try:
            body = await request.read()
            logger.debug(f"Media service request: {body[:500]}")
            
            response = await self.media_service.handle_request(body)
            
            return web.Response(
                body=response,
                content_type='application/soap+xml', charset='utf-8'
            )
        except Exception as e:
            logger.exception(f"Error handling media service request: {e}")
            return self._soap_fault("Server", str(e))
            
    async def _handle_events_service(self, request: web.Request) -> web.Response:
        """Handle Events Service SOAP requests."""
        try:
            body = await request.read()
            logger.debug(f"Events service request: {body[:500]}")
            
            response = await self.events_service.handle_request(body)
            
            return web.Response(
                body=response,
                content_type='application/soap+xml', charset='utf-8'
            )
        except Exception as e:
            logger.exception(f"Error handling events service request: {e}")
            return self._soap_fault("Server", str(e))
            
    async def _handle_wsdl_request(self, request: web.Request) -> web.Response:
        """Handle WSDL/service discovery GET requests."""
        return web.Response(
            text="ONVIF Service Endpoint - Use POST for SOAP requests",
            content_type='text/plain'
        )
        
    async def _handle_health(self, request: web.Request) -> web.Response:
        """Handle health check requests."""
        return web.json_response({
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "camera_name": self.config.camera_name,
            "onvif_port": self.config.onvif_port,
            "rtsp_proxy_port": self.config.rtsp_proxy_port
        })
        
    def _soap_fault(self, code: str, message: str) -> web.Response:
        """Generate a SOAP fault response."""
        fault = self.soap_handler.create_fault(code, message)
        return web.Response(
            body=fault,
            status=500,
            content_type='application/soap+xml', charset='utf-8'
        )
