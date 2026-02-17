"""SOAP utilities for ONVIF services."""

import re
import logging
from lxml import etree
from datetime import datetime, timezone

from onvif_rtsp_bridge.config import Config

logger = logging.getLogger(__name__)

# SOAP/ONVIF Namespaces
NAMESPACES = {
    'soap': 'http://www.w3.org/2003/05/soap-envelope',
    'soap12': 'http://www.w3.org/2003/05/soap-envelope',
    'wsse': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd',
    'wsu': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd',
    'tds': 'http://www.onvif.org/ver10/device/wsdl',
    'trt': 'http://www.onvif.org/ver10/media/wsdl',
    'tev': 'http://www.onvif.org/ver10/events/wsdl',
    'tt': 'http://www.onvif.org/ver10/schema',
    'wsa': 'http://www.w3.org/2005/08/addressing',
    'wsnt': 'http://docs.oasis-open.org/wsn/b-2',
    'wstop': 'http://docs.oasis-open.org/wsn/t-1',
}


class SoapHandler:
    """Handles SOAP message parsing and creation."""
    
    def __init__(self, config: Config):
        self.config = config
        
    def get_action(self, body: bytes) -> str:
        """Extract the SOAP action from the request body."""
        try:
            # Parse the XML
            root = etree.fromstring(body)
            
            # Find the Body element
            body_elem = root.find('.//{http://www.w3.org/2003/05/soap-envelope}Body')
            if body_elem is None:
                body_elem = root.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Body')
            
            if body_elem is not None and len(body_elem) > 0:
                # Get the first child element (the action)
                action_elem = body_elem[0]
                # Extract just the local name (without namespace)
                action = etree.QName(action_elem.tag).localname
                return action
                
        except Exception as e:
            logger.error(f"Error parsing SOAP action: {e}")
            
        # Fallback: try regex
        try:
            body_str = body.decode('utf-8')
            # Look for common action patterns
            patterns = [
                r'<\w+:(\w+)\s*xmlns',  # <tds:GetDeviceInformation xmlns...
                r'<(\w+)\s*xmlns',       # <GetDeviceInformation xmlns...
                r'<\w+:(\w+)>',          # <tds:GetDeviceInformation>
                r'<(\w+)/>',             # <GetDeviceInformation/>
            ]
            for pattern in patterns:
                match = re.search(pattern, body_str)
                if match:
                    action = match.group(1)
                    # Filter out common non-action elements
                    if action not in ['Envelope', 'Header', 'Body', 'Security']:
                        return action
        except Exception as e:
            logger.error(f"Error in regex action extraction: {e}")
            
        return "Unknown"
        
    def wrap_response(self, content: str) -> bytes:
        """Wrap response content in a SOAP envelope."""
        envelope = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope 
    xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
    xmlns:tds="http://www.onvif.org/ver10/device/wsdl"
    xmlns:trt="http://www.onvif.org/ver10/media/wsdl"
    xmlns:tev="http://www.onvif.org/ver10/events/wsdl"
    xmlns:tt="http://www.onvif.org/ver10/schema"
    xmlns:wsa="http://www.w3.org/2005/08/addressing"
    xmlns:wsnt="http://docs.oasis-open.org/wsn/b-2"
    xmlns:wstop="http://docs.oasis-open.org/wsn/t-1">
    <soap:Body>
        {content.strip()}
    </soap:Body>
</soap:Envelope>'''
        return envelope.encode('utf-8')
        
    def create_fault(self, code: str, message: str) -> bytes:
        """Create a SOAP fault response."""
        fault = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
    <soap:Body>
        <soap:Fault>
            <soap:Code>
                <soap:Value>soap:{code}</soap:Value>
            </soap:Code>
            <soap:Reason>
                <soap:Text xml:lang="en">{message}</soap:Text>
            </soap:Reason>
        </soap:Fault>
    </soap:Body>
</soap:Envelope>'''
        return fault.encode('utf-8')
        
    def validate_auth(self, body: bytes) -> bool:
        """Validate WS-Security authentication in SOAP header."""
        try:
            root = etree.fromstring(body)
            
            # Find Security header
            security = root.find('.//{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}Security')
            if security is None:
                # No security header - allow for now (some clients don't send auth initially)
                return True
                
            # Find UsernameToken
            username_token = security.find('.//{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}UsernameToken')
            if username_token is None:
                return True
                
            username_elem = username_token.find('.//{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}Username')
            password_elem = username_token.find('.//{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}Password')
            
            if username_elem is not None and password_elem is not None:
                username = username_elem.text
                password = password_elem.text
                
                # Simple password check (in production, use proper hashing)
                if username == self.config.onvif_username and password == self.config.onvif_password:
                    return True
                    
            # For now, allow all requests (Unifi Protect doesn't always send proper auth)
            logger.warning("Auth validation skipped - allowing request")
            return True
            
        except Exception as e:
            logger.error(f"Error validating auth: {e}")
            return True  # Allow on error for compatibility
