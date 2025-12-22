"""ONVIF Device Service implementation."""

import logging
from datetime import datetime, timezone
from lxml import etree

from src.config import Config
from src.utils.soap_utils import SoapHandler

logger = logging.getLogger(__name__)


class DeviceService:
    """ONVIF Device Service for Profile S."""
    
    def __init__(self, config: Config, soap_handler: SoapHandler):
        self.config = config
        self.soap = soap_handler
        
        # Map of actions to handlers
        self.actions = {
            'GetDeviceInformation': self._get_device_information,
            'GetCapabilities': self._get_capabilities,
            'GetServices': self._get_services,
            'GetServiceCapabilities': self._get_service_capabilities,
            'GetSystemDateAndTime': self._get_system_date_time,
            'GetScopes': self._get_scopes,
            'GetHostname': self._get_hostname,
            'GetNetworkInterfaces': self._get_network_interfaces,
            'GetDNS': self._get_dns,
            'GetNTP': self._get_ntp,
            'GetUsers': self._get_users,
            'GetWsdlUrl': self._get_wsdl_url,
        }
        
    async def handle_request(self, body: bytes) -> bytes:
        """Handle incoming SOAP request."""
        action = self.soap.get_action(body)
        logger.info(f"Device Service action: {action}")
        
        handler = self.actions.get(action)
        if handler:
            return handler(body)
        else:
            logger.warning(f"Unknown action: {action}")
            return self.soap.create_fault("ActionNotSupported", f"Action {action} not supported")
            
    def _get_device_information(self, body: bytes) -> bytes:
        """Handle GetDeviceInformation request."""
        response = f'''
        <tds:GetDeviceInformationResponse xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
            <tds:Manufacturer>{self.config.camera_manufacturer}</tds:Manufacturer>
            <tds:Model>{self.config.camera_model}</tds:Model>
            <tds:FirmwareVersion>{self.config.camera_firmware}</tds:FirmwareVersion>
            <tds:SerialNumber>{self.config.camera_serial}</tds:SerialNumber>
            <tds:HardwareId>{self.config.hardware_id}</tds:HardwareId>
        </tds:GetDeviceInformationResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _get_capabilities(self, body: bytes) -> bytes:
        """Handle GetCapabilities request."""
        response = f'''
        <tds:GetCapabilitiesResponse xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
            <tds:Capabilities>
                <tt:Device xmlns:tt="http://www.onvif.org/ver10/schema">
                    <tt:XAddr>{self.config.device_service_url}</tt:XAddr>
                    <tt:Network>
                        <tt:IPFilter>false</tt:IPFilter>
                        <tt:ZeroConfiguration>false</tt:ZeroConfiguration>
                        <tt:IPVersion6>false</tt:IPVersion6>
                        <tt:DynDNS>false</tt:DynDNS>
                    </tt:Network>
                    <tt:System>
                        <tt:DiscoveryResolve>false</tt:DiscoveryResolve>
                        <tt:DiscoveryBye>true</tt:DiscoveryBye>
                        <tt:RemoteDiscovery>false</tt:RemoteDiscovery>
                        <tt:SystemBackup>false</tt:SystemBackup>
                        <tt:SystemLogging>false</tt:SystemLogging>
                        <tt:FirmwareUpgrade>false</tt:FirmwareUpgrade>
                        <tt:SupportedVersions>
                            <tt:Major>2</tt:Major>
                            <tt:Minor>0</tt:Minor>
                        </tt:SupportedVersions>
                    </tt:System>
                    <tt:IO>
                        <tt:InputConnectors>0</tt:InputConnectors>
                        <tt:RelayOutputs>0</tt:RelayOutputs>
                    </tt:IO>
                    <tt:Security>
                        <tt:TLS1.1>false</tt:TLS1.1>
                        <tt:TLS1.2>false</tt:TLS1.2>
                        <tt:OnboardKeyGeneration>false</tt:OnboardKeyGeneration>
                        <tt:AccessPolicyConfig>false</tt:AccessPolicyConfig>
                        <tt:X.509Token>false</tt:X.509Token>
                        <tt:SAMLToken>false</tt:SAMLToken>
                        <tt:KerberosToken>false</tt:KerberosToken>
                        <tt:RELToken>false</tt:RELToken>
                    </tt:Security>
                </tt:Device>
                <tt:Media xmlns:tt="http://www.onvif.org/ver10/schema">
                    <tt:XAddr>{self.config.media_service_url}</tt:XAddr>
                    <tt:StreamingCapabilities>
                        <tt:RTPMulticast>false</tt:RTPMulticast>
                        <tt:RTP_TCP>true</tt:RTP_TCP>
                        <tt:RTP_RTSP_TCP>true</tt:RTP_RTSP_TCP>
                    </tt:StreamingCapabilities>
                </tt:Media>
                <tt:Events xmlns:tt="http://www.onvif.org/ver10/schema">
                    <tt:XAddr>{self.config.events_service_url}</tt:XAddr>
                    <tt:WSSubscriptionPolicySupport>false</tt:WSSubscriptionPolicySupport>
                    <tt:WSPullPointSupport>true</tt:WSPullPointSupport>
                    <tt:WSPausableSubscriptionManagerInterfaceSupport>false</tt:WSPausableSubscriptionManagerInterfaceSupport>
                </tt:Events>
            </tds:Capabilities>
        </tds:GetCapabilitiesResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _get_services(self, body: bytes) -> bytes:
        """Handle GetServices request."""
        response = f'''
        <tds:GetServicesResponse xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
            <tds:Service>
                <tds:Namespace>http://www.onvif.org/ver10/device/wsdl</tds:Namespace>
                <tds:XAddr>{self.config.device_service_url}</tds:XAddr>
                <tds:Version>
                    <tt:Major xmlns:tt="http://www.onvif.org/ver10/schema">2</tt:Major>
                    <tt:Minor xmlns:tt="http://www.onvif.org/ver10/schema">0</tt:Minor>
                </tds:Version>
            </tds:Service>
            <tds:Service>
                <tds:Namespace>http://www.onvif.org/ver10/media/wsdl</tds:Namespace>
                <tds:XAddr>{self.config.media_service_url}</tds:XAddr>
                <tds:Version>
                    <tt:Major xmlns:tt="http://www.onvif.org/ver10/schema">2</tt:Major>
                    <tt:Minor xmlns:tt="http://www.onvif.org/ver10/schema">0</tt:Minor>
                </tds:Version>
            </tds:Service>
            <tds:Service>
                <tds:Namespace>http://www.onvif.org/ver10/events/wsdl</tds:Namespace>
                <tds:XAddr>{self.config.events_service_url}</tds:XAddr>
                <tds:Version>
                    <tt:Major xmlns:tt="http://www.onvif.org/ver10/schema">2</tt:Major>
                    <tt:Minor xmlns:tt="http://www.onvif.org/ver10/schema">0</tt:Minor>
                </tds:Version>
            </tds:Service>
        </tds:GetServicesResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _get_service_capabilities(self, body: bytes) -> bytes:
        """Handle GetServiceCapabilities request."""
        response = '''
        <tds:GetServiceCapabilitiesResponse xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
            <tds:Capabilities>
                <tds:Network DHCPv6="false" NTP="0" HostnameFromDHCP="false" Dot11Configuration="false" 
                    Dot1XConfigurations="0" DynDNS="false" IPVersion6="false" ZeroConfiguration="false" IPFilter="false"/>
                <tds:Security TLS1.0="false" TLS1.1="false" TLS1.2="false" OnboardKeyGeneration="false" 
                    AccessPolicyConfig="false" DefaultAccessPolicy="false" Dot1X="false" RemoteUserHandling="false" 
                    X.509Token="false" SAMLToken="false" KerberosToken="false" UsernameToken="true" 
                    HttpDigest="true" RELToken="false"/>
                <tds:System DiscoveryResolve="false" DiscoveryBye="true" RemoteDiscovery="false" 
                    SystemBackup="false" SystemLogging="false" FirmwareUpgrade="false" HttpFirmwareUpgrade="false" 
                    HttpSystemBackup="false" HttpSystemLogging="false" HttpSupportInformation="false"/>
            </tds:Capabilities>
        </tds:GetServiceCapabilitiesResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _get_system_date_time(self, body: bytes) -> bytes:
        """Handle GetSystemDateAndTime request."""
        now = datetime.now(timezone.utc)
        response = f'''
        <tds:GetSystemDateAndTimeResponse xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
            <tds:SystemDateAndTime>
                <tt:DateTimeType xmlns:tt="http://www.onvif.org/ver10/schema">NTP</tt:DateTimeType>
                <tt:DaylightSavings xmlns:tt="http://www.onvif.org/ver10/schema">false</tt:DaylightSavings>
                <tt:TimeZone xmlns:tt="http://www.onvif.org/ver10/schema">
                    <tt:TZ>UTC0</tt:TZ>
                </tt:TimeZone>
                <tt:UTCDateTime xmlns:tt="http://www.onvif.org/ver10/schema">
                    <tt:Time>
                        <tt:Hour>{now.hour}</tt:Hour>
                        <tt:Minute>{now.minute}</tt:Minute>
                        <tt:Second>{now.second}</tt:Second>
                    </tt:Time>
                    <tt:Date>
                        <tt:Year>{now.year}</tt:Year>
                        <tt:Month>{now.month}</tt:Month>
                        <tt:Day>{now.day}</tt:Day>
                    </tt:Date>
                </tt:UTCDateTime>
                <tt:LocalDateTime xmlns:tt="http://www.onvif.org/ver10/schema">
                    <tt:Time>
                        <tt:Hour>{now.hour}</tt:Hour>
                        <tt:Minute>{now.minute}</tt:Minute>
                        <tt:Second>{now.second}</tt:Second>
                    </tt:Time>
                    <tt:Date>
                        <tt:Year>{now.year}</tt:Year>
                        <tt:Month>{now.month}</tt:Month>
                        <tt:Day>{now.day}</tt:Day>
                    </tt:Date>
                </tt:LocalDateTime>
            </tds:SystemDateAndTime>
        </tds:GetSystemDateAndTimeResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _get_scopes(self, body: bytes) -> bytes:
        """Handle GetScopes request."""
        response = f'''
        <tds:GetScopesResponse xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
            <tds:Scopes>
                <tt:ScopeDef xmlns:tt="http://www.onvif.org/ver10/schema">Fixed</tt:ScopeDef>
                <tt:ScopeItem xmlns:tt="http://www.onvif.org/ver10/schema">onvif://www.onvif.org/type/video_encoder</tt:ScopeItem>
            </tds:Scopes>
            <tds:Scopes>
                <tt:ScopeDef xmlns:tt="http://www.onvif.org/ver10/schema">Fixed</tt:ScopeDef>
                <tt:ScopeItem xmlns:tt="http://www.onvif.org/ver10/schema">onvif://www.onvif.org/type/Network_Video_Transmitter</tt:ScopeItem>
            </tds:Scopes>
            <tds:Scopes>
                <tt:ScopeDef xmlns:tt="http://www.onvif.org/ver10/schema">Fixed</tt:ScopeDef>
                <tt:ScopeItem xmlns:tt="http://www.onvif.org/ver10/schema">onvif://www.onvif.org/Profile/Streaming</tt:ScopeItem>
            </tds:Scopes>
            <tds:Scopes>
                <tt:ScopeDef xmlns:tt="http://www.onvif.org/ver10/schema">Fixed</tt:ScopeDef>
                <tt:ScopeItem xmlns:tt="http://www.onvif.org/ver10/schema">onvif://www.onvif.org/hardware/{self.config.camera_model}</tt:ScopeItem>
            </tds:Scopes>
            <tds:Scopes>
                <tt:ScopeDef xmlns:tt="http://www.onvif.org/ver10/schema">Configurable</tt:ScopeDef>
                <tt:ScopeItem xmlns:tt="http://www.onvif.org/ver10/schema">onvif://www.onvif.org/name/{self.config.camera_name.replace(' ', '_')}</tt:ScopeItem>
            </tds:Scopes>
            <tds:Scopes>
                <tt:ScopeDef xmlns:tt="http://www.onvif.org/ver10/schema">Configurable</tt:ScopeDef>
                <tt:ScopeItem xmlns:tt="http://www.onvif.org/ver10/schema">onvif://www.onvif.org/location/</tt:ScopeItem>
            </tds:Scopes>
        </tds:GetScopesResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _get_hostname(self, body: bytes) -> bytes:
        """Handle GetHostname request."""
        response = f'''
        <tds:GetHostnameResponse xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
            <tds:HostnameInformation>
                <tt:FromDHCP xmlns:tt="http://www.onvif.org/ver10/schema">false</tt:FromDHCP>
                <tt:Name xmlns:tt="http://www.onvif.org/ver10/schema">onvif-bridge</tt:Name>
            </tds:HostnameInformation>
        </tds:GetHostnameResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _get_network_interfaces(self, body: bytes) -> bytes:
        """Handle GetNetworkInterfaces request."""
        response = f'''
        <tds:GetNetworkInterfacesResponse xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
            <tds:NetworkInterfaces token="eth0">
                <tt:Enabled xmlns:tt="http://www.onvif.org/ver10/schema">true</tt:Enabled>
                <tt:Info xmlns:tt="http://www.onvif.org/ver10/schema">
                    <tt:Name>eth0</tt:Name>
                    <tt:HwAddress>00:00:00:00:00:00</tt:HwAddress>
                    <tt:MTU>1500</tt:MTU>
                </tt:Info>
                <tt:IPv4 xmlns:tt="http://www.onvif.org/ver10/schema">
                    <tt:Enabled>true</tt:Enabled>
                    <tt:Config>
                        <tt:Manual>
                            <tt:Address>{self.config.server_ip}</tt:Address>
                            <tt:PrefixLength>24</tt:PrefixLength>
                        </tt:Manual>
                        <tt:DHCP>false</tt:DHCP>
                    </tt:Config>
                </tt:IPv4>
            </tds:NetworkInterfaces>
        </tds:GetNetworkInterfacesResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _get_dns(self, body: bytes) -> bytes:
        """Handle GetDNS request."""
        response = '''
        <tds:GetDNSResponse xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
            <tds:DNSInformation>
                <tt:FromDHCP xmlns:tt="http://www.onvif.org/ver10/schema">false</tt:FromDHCP>
            </tds:DNSInformation>
        </tds:GetDNSResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _get_ntp(self, body: bytes) -> bytes:
        """Handle GetNTP request."""
        response = '''
        <tds:GetNTPResponse xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
            <tds:NTPInformation>
                <tt:FromDHCP xmlns:tt="http://www.onvif.org/ver10/schema">false</tt:FromDHCP>
            </tds:NTPInformation>
        </tds:GetNTPResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _get_users(self, body: bytes) -> bytes:
        """Handle GetUsers request."""
        response = f'''
        <tds:GetUsersResponse xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
            <tds:User>
                <tt:Username xmlns:tt="http://www.onvif.org/ver10/schema">{self.config.onvif_username}</tt:Username>
                <tt:UserLevel xmlns:tt="http://www.onvif.org/ver10/schema">Administrator</tt:UserLevel>
            </tds:User>
        </tds:GetUsersResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _get_wsdl_url(self, body: bytes) -> bytes:
        """Handle GetWsdlUrl request."""
        response = f'''
        <tds:GetWsdlUrlResponse xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
            <tds:WsdlUrl>{self.config.device_service_url}?wsdl</tds:WsdlUrl>
        </tds:GetWsdlUrlResponse>
        '''
        return self.soap.wrap_response(response)
