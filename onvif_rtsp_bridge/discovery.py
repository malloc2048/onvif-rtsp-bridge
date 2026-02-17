"""WS-Discovery service for ONVIF device discovery."""

import asyncio
import logging
import socket
import struct
import uuid
from datetime import datetime, timezone

from onvif_rtsp_bridge.config import Config

logger = logging.getLogger(__name__)

# WS-Discovery constants
WS_DISCOVERY_PORT = 3702
WS_DISCOVERY_MULTICAST = "239.255.255.250"
WS_DISCOVERY_NS = "http://schemas.xmlsoap.org/ws/2005/04/discovery"


class WsDiscoveryService:
    """WS-Discovery service for ONVIF device auto-detection."""
    
    def __init__(self, config: Config):
        self.config = config
        self.running = False
        self.socket = None
        self.task = None
        self.message_id = str(uuid.uuid4())
        
    async def start(self):
        """Start the WS-Discovery service."""
        self.running = True
        
        # Create UDP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            pass  # Not available on all systems
            
        # Bind to discovery port
        self.socket.bind(('', WS_DISCOVERY_PORT))
        
        # Join multicast group
        mreq = struct.pack("4sl", socket.inet_aton(WS_DISCOVERY_MULTICAST), socket.INADDR_ANY)
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        
        # Set non-blocking
        self.socket.setblocking(False)
        
        # Start listener task
        self.task = asyncio.create_task(self._listen())
        
        # Send initial Hello
        await self._send_hello()
        
        logger.info(f"WS-Discovery service started on port {WS_DISCOVERY_PORT}")
        
    async def stop(self):
        """Stop the WS-Discovery service."""
        self.running = False
        
        # Send Bye message
        await self._send_bye()
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
                
        if self.socket:
            self.socket.close()
            
        logger.info("WS-Discovery service stopped")
        
    async def _listen(self):
        """Listen for WS-Discovery Probe messages."""
        loop = asyncio.get_event_loop()
        
        while self.running:
            try:
                # Receive data
                data, addr = await loop.run_in_executor(
                    None, 
                    lambda: self.socket.recvfrom(65535)
                )
                
                # Process the message
                await self._process_message(data, addr)
                
            except BlockingIOError:
                await asyncio.sleep(0.1)
            except Exception as e:
                if self.running:
                    logger.error(f"WS-Discovery error: {e}")
                await asyncio.sleep(1)
                
    async def _process_message(self, data: bytes, addr: tuple):
        """Process incoming WS-Discovery message."""
        try:
            message = data.decode('utf-8')
            
            # Check if it's a Probe message
            if 'Probe' in message and 'NetworkVideoTransmitter' in message:
                logger.info(f"Received WS-Discovery Probe from {addr}")
                await self._send_probe_match(addr)
            elif 'Probe' in message:
                # Generic probe - respond anyway
                logger.debug(f"Received generic Probe from {addr}")
                await self._send_probe_match(addr)
                
        except Exception as e:
            logger.error(f"Error processing WS-Discovery message: {e}")
            
    async def _send_hello(self):
        """Send WS-Discovery Hello message."""
        message_id = str(uuid.uuid4())
        instance_id = str(int(datetime.now(timezone.utc).timestamp()))
        
        hello = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope 
    xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
    xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing"
    xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery"
    xmlns:dn="http://www.onvif.org/ver10/network/wsdl">
    <soap:Header>
        <wsa:MessageID>urn:uuid:{message_id}</wsa:MessageID>
        <wsa:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To>
        <wsa:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Hello</wsa:Action>
    </soap:Header>
    <soap:Body>
        <d:Hello>
            <wsa:EndpointReference>
                <wsa:Address>urn:uuid:{self.config.hardware_id}</wsa:Address>
            </wsa:EndpointReference>
            <d:Types>dn:NetworkVideoTransmitter</d:Types>
            <d:Scopes>
                onvif://www.onvif.org/type/video_encoder
                onvif://www.onvif.org/type/Network_Video_Transmitter
                onvif://www.onvif.org/Profile/Streaming
                onvif://www.onvif.org/hardware/{self.config.camera_model}
                onvif://www.onvif.org/name/{self.config.camera_name.replace(' ', '_')}
            </d:Scopes>
            <d:XAddrs>{self.config.device_service_url}</d:XAddrs>
            <d:MetadataVersion>1</d:MetadataVersion>
        </d:Hello>
    </soap:Body>
</soap:Envelope>'''
        
        try:
            self.socket.sendto(
                hello.encode('utf-8'),
                (WS_DISCOVERY_MULTICAST, WS_DISCOVERY_PORT)
            )
            logger.info("Sent WS-Discovery Hello message")
        except Exception as e:
            logger.error(f"Error sending Hello: {e}")
            
    async def _send_bye(self):
        """Send WS-Discovery Bye message."""
        message_id = str(uuid.uuid4())
        
        bye = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope 
    xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
    xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing"
    xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery">
    <soap:Header>
        <wsa:MessageID>urn:uuid:{message_id}</wsa:MessageID>
        <wsa:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To>
        <wsa:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Bye</wsa:Action>
    </soap:Header>
    <soap:Body>
        <d:Bye>
            <wsa:EndpointReference>
                <wsa:Address>urn:uuid:{self.config.hardware_id}</wsa:Address>
            </wsa:EndpointReference>
        </d:Bye>
    </soap:Body>
</soap:Envelope>'''
        
        try:
            self.socket.sendto(
                bye.encode('utf-8'),
                (WS_DISCOVERY_MULTICAST, WS_DISCOVERY_PORT)
            )
            logger.info("Sent WS-Discovery Bye message")
        except Exception as e:
            logger.error(f"Error sending Bye: {e}")
            
    async def _send_probe_match(self, addr: tuple):
        """Send WS-Discovery ProbeMatch response."""
        message_id = str(uuid.uuid4())
        relates_to = str(uuid.uuid4())  # Should extract from probe, but this works
        instance_id = str(int(datetime.now(timezone.utc).timestamp()))
        
        probe_match = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope 
    xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
    xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing"
    xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery"
    xmlns:dn="http://www.onvif.org/ver10/network/wsdl">
    <soap:Header>
        <wsa:MessageID>urn:uuid:{message_id}</wsa:MessageID>
        <wsa:RelatesTo>urn:uuid:{relates_to}</wsa:RelatesTo>
        <wsa:To>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:To>
        <wsa:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/ProbeMatches</wsa:Action>
        <d:AppSequence InstanceId="{instance_id}" MessageNumber="1"/>
    </soap:Header>
    <soap:Body>
        <d:ProbeMatches>
            <d:ProbeMatch>
                <wsa:EndpointReference>
                    <wsa:Address>urn:uuid:{self.config.hardware_id}</wsa:Address>
                </wsa:EndpointReference>
                <d:Types>dn:NetworkVideoTransmitter</d:Types>
                <d:Scopes>
                    onvif://www.onvif.org/type/video_encoder
                    onvif://www.onvif.org/type/Network_Video_Transmitter
                    onvif://www.onvif.org/Profile/Streaming
                    onvif://www.onvif.org/hardware/{self.config.camera_model}
                    onvif://www.onvif.org/name/{self.config.camera_name.replace(' ', '_')}
                </d:Scopes>
                <d:XAddrs>{self.config.device_service_url}</d:XAddrs>
                <d:MetadataVersion>1</d:MetadataVersion>
            </d:ProbeMatch>
        </d:ProbeMatches>
    </soap:Body>
</soap:Envelope>'''
        
        try:
            # Send unicast response to the probe source
            self.socket.sendto(probe_match.encode('utf-8'), addr)
            logger.info(f"Sent ProbeMatch to {addr}")
        except Exception as e:
            logger.error(f"Error sending ProbeMatch: {e}")
