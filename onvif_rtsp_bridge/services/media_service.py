"""ONVIF Media Service implementation for Profile S."""

import logging
from lxml import etree

from onvif_rtsp_bridge.config import Config
from onvif_rtsp_bridge.utils.soap_utils import SoapHandler

logger = logging.getLogger(__name__)


class MediaService:
    """ONVIF Media Service for Profile S streaming."""
    
    def __init__(self, config: Config, soap_handler: SoapHandler):
        self.config = config
        self.soap = soap_handler
        
        # Map of actions to handlers
        self.actions = {
            'GetProfiles': self._get_profiles,
            'GetProfile': self._get_profile,
            'GetVideoSources': self._get_video_sources,
            'GetVideoSourceConfigurations': self._get_video_source_configurations,
            'GetVideoSourceConfiguration': self._get_video_source_configuration,
            'GetVideoEncoderConfigurations': self._get_video_encoder_configurations,
            'GetVideoEncoderConfiguration': self._get_video_encoder_configuration,
            'GetStreamUri': self._get_stream_uri,
            'GetSnapshotUri': self._get_snapshot_uri,
            'GetServiceCapabilities': self._get_service_capabilities,
            'GetVideoSourceConfigurationOptions': self._get_video_source_config_options,
            'GetVideoEncoderConfigurationOptions': self._get_video_encoder_config_options,
            'GetCompatibleVideoEncoderConfigurations': self._get_compatible_video_encoder_configs,
            'GetCompatibleVideoSourceConfigurations': self._get_compatible_video_source_configs,
            'GetAudioSources': self._get_audio_sources,
            'GetAudioSourceConfigurations': self._get_audio_source_configurations,
            'GetAudioEncoderConfigurations': self._get_audio_encoder_configurations,
        }
        
    async def handle_request(self, body: bytes) -> bytes:
        """Handle incoming SOAP request."""
        action = self.soap.get_action(body)
        logger.info(f"Media Service action: {action}")
        
        handler = self.actions.get(action)
        if handler:
            return handler(body)
        else:
            logger.warning(f"Unknown action: {action}")
            return self.soap.create_fault("ActionNotSupported", f"Action {action} not supported")
            
    def _get_profiles(self, body: bytes) -> bytes:
        """Handle GetProfiles request - returns available media profiles."""
        response = f'''
        <trt:GetProfilesResponse xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
            <trt:Profiles token="{self.config.profile_token}" fixed="true">
                <tt:Name xmlns:tt="http://www.onvif.org/ver10/schema">{self.config.camera_name}</tt:Name>
                <tt:VideoSourceConfiguration xmlns:tt="http://www.onvif.org/ver10/schema" token="{self.config.video_source_token}">
                    <tt:Name>VideoSourceConfig</tt:Name>
                    <tt:UseCount>1</tt:UseCount>
                    <tt:SourceToken>{self.config.video_source_token}</tt:SourceToken>
                    <tt:Bounds x="0" y="0" width="{self.config.stream_width}" height="{self.config.stream_height}"/>
                </tt:VideoSourceConfiguration>
                <tt:VideoEncoderConfiguration xmlns:tt="http://www.onvif.org/ver10/schema" token="{self.config.video_encoder_token}">
                    <tt:Name>VideoEncoderConfig</tt:Name>
                    <tt:UseCount>1</tt:UseCount>
                    <tt:Encoding>H264</tt:Encoding>
                    <tt:Resolution>
                        <tt:Width>{self.config.stream_width}</tt:Width>
                        <tt:Height>{self.config.stream_height}</tt:Height>
                    </tt:Resolution>
                    <tt:Quality>5</tt:Quality>
                    <tt:RateControl>
                        <tt:FrameRateLimit>{self.config.stream_fps}</tt:FrameRateLimit>
                        <tt:EncodingInterval>1</tt:EncodingInterval>
                        <tt:BitrateLimit>{self.config.stream_bitrate}</tt:BitrateLimit>
                    </tt:RateControl>
                    <tt:H264>
                        <tt:GovLength>30</tt:GovLength>
                        <tt:H264Profile>Main</tt:H264Profile>
                    </tt:H264>
                    <tt:Multicast>
                        <tt:Address>
                            <tt:Type>IPv4</tt:Type>
                            <tt:IPv4Address>0.0.0.0</tt:IPv4Address>
                        </tt:Address>
                        <tt:Port>0</tt:Port>
                        <tt:TTL>0</tt:TTL>
                        <tt:AutoStart>false</tt:AutoStart>
                    </tt:Multicast>
                    <tt:SessionTimeout>PT60S</tt:SessionTimeout>
                </tt:VideoEncoderConfiguration>
            </trt:Profiles>
        </trt:GetProfilesResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _get_profile(self, body: bytes) -> bytes:
        """Handle GetProfile request - returns a specific profile."""
        return self._get_profiles(body)
        
    def _get_video_sources(self, body: bytes) -> bytes:
        """Handle GetVideoSources request."""
        response = f'''
        <trt:GetVideoSourcesResponse xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
            <trt:VideoSources token="{self.config.video_source_token}">
                <tt:Framerate xmlns:tt="http://www.onvif.org/ver10/schema">{self.config.stream_fps}</tt:Framerate>
                <tt:Resolution xmlns:tt="http://www.onvif.org/ver10/schema">
                    <tt:Width>{self.config.stream_width}</tt:Width>
                    <tt:Height>{self.config.stream_height}</tt:Height>
                </tt:Resolution>
            </trt:VideoSources>
        </trt:GetVideoSourcesResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _get_video_source_configurations(self, body: bytes) -> bytes:
        """Handle GetVideoSourceConfigurations request."""
        response = f'''
        <trt:GetVideoSourceConfigurationsResponse xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
            <trt:Configurations token="{self.config.video_source_token}">
                <tt:Name xmlns:tt="http://www.onvif.org/ver10/schema">VideoSourceConfig</tt:Name>
                <tt:UseCount xmlns:tt="http://www.onvif.org/ver10/schema">1</tt:UseCount>
                <tt:SourceToken xmlns:tt="http://www.onvif.org/ver10/schema">{self.config.video_source_token}</tt:SourceToken>
                <tt:Bounds xmlns:tt="http://www.onvif.org/ver10/schema" x="0" y="0" width="{self.config.stream_width}" height="{self.config.stream_height}"/>
            </trt:Configurations>
        </trt:GetVideoSourceConfigurationsResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _get_video_source_configuration(self, body: bytes) -> bytes:
        """Handle GetVideoSourceConfiguration request."""
        response = f'''
        <trt:GetVideoSourceConfigurationResponse xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
            <trt:Configuration token="{self.config.video_source_token}">
                <tt:Name xmlns:tt="http://www.onvif.org/ver10/schema">VideoSourceConfig</tt:Name>
                <tt:UseCount xmlns:tt="http://www.onvif.org/ver10/schema">1</tt:UseCount>
                <tt:SourceToken xmlns:tt="http://www.onvif.org/ver10/schema">{self.config.video_source_token}</tt:SourceToken>
                <tt:Bounds xmlns:tt="http://www.onvif.org/ver10/schema" x="0" y="0" width="{self.config.stream_width}" height="{self.config.stream_height}"/>
            </trt:Configuration>
        </trt:GetVideoSourceConfigurationResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _get_video_encoder_configurations(self, body: bytes) -> bytes:
        """Handle GetVideoEncoderConfigurations request."""
        response = f'''
        <trt:GetVideoEncoderConfigurationsResponse xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
            <trt:Configurations token="{self.config.video_encoder_token}">
                <tt:Name xmlns:tt="http://www.onvif.org/ver10/schema">VideoEncoderConfig</tt:Name>
                <tt:UseCount xmlns:tt="http://www.onvif.org/ver10/schema">1</tt:UseCount>
                <tt:Encoding xmlns:tt="http://www.onvif.org/ver10/schema">H264</tt:Encoding>
                <tt:Resolution xmlns:tt="http://www.onvif.org/ver10/schema">
                    <tt:Width>{self.config.stream_width}</tt:Width>
                    <tt:Height>{self.config.stream_height}</tt:Height>
                </tt:Resolution>
                <tt:Quality xmlns:tt="http://www.onvif.org/ver10/schema">5</tt:Quality>
                <tt:RateControl xmlns:tt="http://www.onvif.org/ver10/schema">
                    <tt:FrameRateLimit>{self.config.stream_fps}</tt:FrameRateLimit>
                    <tt:EncodingInterval>1</tt:EncodingInterval>
                    <tt:BitrateLimit>{self.config.stream_bitrate}</tt:BitrateLimit>
                </tt:RateControl>
                <tt:H264 xmlns:tt="http://www.onvif.org/ver10/schema">
                    <tt:GovLength>30</tt:GovLength>
                    <tt:H264Profile>Main</tt:H264Profile>
                </tt:H264>
                <tt:Multicast xmlns:tt="http://www.onvif.org/ver10/schema">
                    <tt:Address>
                        <tt:Type>IPv4</tt:Type>
                        <tt:IPv4Address>0.0.0.0</tt:IPv4Address>
                    </tt:Address>
                    <tt:Port>0</tt:Port>
                    <tt:TTL>0</tt:TTL>
                    <tt:AutoStart>false</tt:AutoStart>
                </tt:Multicast>
                <tt:SessionTimeout xmlns:tt="http://www.onvif.org/ver10/schema">PT60S</tt:SessionTimeout>
            </trt:Configurations>
        </trt:GetVideoEncoderConfigurationsResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _get_video_encoder_configuration(self, body: bytes) -> bytes:
        """Handle GetVideoEncoderConfiguration request."""
        response = f'''
        <trt:GetVideoEncoderConfigurationResponse xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
            <trt:Configuration token="{self.config.video_encoder_token}">
                <tt:Name xmlns:tt="http://www.onvif.org/ver10/schema">VideoEncoderConfig</tt:Name>
                <tt:UseCount xmlns:tt="http://www.onvif.org/ver10/schema">1</tt:UseCount>
                <tt:Encoding xmlns:tt="http://www.onvif.org/ver10/schema">H264</tt:Encoding>
                <tt:Resolution xmlns:tt="http://www.onvif.org/ver10/schema">
                    <tt:Width>{self.config.stream_width}</tt:Width>
                    <tt:Height>{self.config.stream_height}</tt:Height>
                </tt:Resolution>
                <tt:Quality xmlns:tt="http://www.onvif.org/ver10/schema">5</tt:Quality>
                <tt:RateControl xmlns:tt="http://www.onvif.org/ver10/schema">
                    <tt:FrameRateLimit>{self.config.stream_fps}</tt:FrameRateLimit>
                    <tt:EncodingInterval>1</tt:EncodingInterval>
                    <tt:BitrateLimit>{self.config.stream_bitrate}</tt:BitrateLimit>
                </tt:RateControl>
                <tt:H264 xmlns:tt="http://www.onvif.org/ver10/schema">
                    <tt:GovLength>30</tt:GovLength>
                    <tt:H264Profile>Main</tt:H264Profile>
                </tt:H264>
                <tt:Multicast xmlns:tt="http://www.onvif.org/ver10/schema">
                    <tt:Address>
                        <tt:Type>IPv4</tt:Type>
                        <tt:IPv4Address>0.0.0.0</tt:IPv4Address>
                    </tt:Address>
                    <tt:Port>0</tt:Port>
                    <tt:TTL>0</tt:TTL>
                    <tt:AutoStart>false</tt:AutoStart>
                </tt:Multicast>
                <tt:SessionTimeout xmlns:tt="http://www.onvif.org/ver10/schema">PT60S</tt:SessionTimeout>
            </trt:Configuration>
        </trt:GetVideoEncoderConfigurationResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _get_stream_uri(self, body: bytes) -> bytes:
        """Handle GetStreamUri request - THE KEY METHOD for streaming."""
        # Return the proxied RTSP URL
        stream_uri = self.config.proxy_rtsp_url
        
        response = f'''
        <trt:GetStreamUriResponse xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
            <trt:MediaUri>
                <tt:Uri xmlns:tt="http://www.onvif.org/ver10/schema">{stream_uri}</tt:Uri>
                <tt:InvalidAfterConnect xmlns:tt="http://www.onvif.org/ver10/schema">false</tt:InvalidAfterConnect>
                <tt:InvalidAfterReboot xmlns:tt="http://www.onvif.org/ver10/schema">false</tt:InvalidAfterReboot>
                <tt:Timeout xmlns:tt="http://www.onvif.org/ver10/schema">PT60S</tt:Timeout>
            </trt:MediaUri>
        </trt:GetStreamUriResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _get_snapshot_uri(self, body: bytes) -> bytes:
        """Handle GetSnapshotUri request."""
        # We don't have a snapshot endpoint, return empty/error
        response = f'''
        <trt:GetSnapshotUriResponse xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
            <trt:MediaUri>
                <tt:Uri xmlns:tt="http://www.onvif.org/ver10/schema">http://{self.config.server_ip}:{self.config.onvif_port}/snapshot</tt:Uri>
                <tt:InvalidAfterConnect xmlns:tt="http://www.onvif.org/ver10/schema">false</tt:InvalidAfterConnect>
                <tt:InvalidAfterReboot xmlns:tt="http://www.onvif.org/ver10/schema">false</tt:InvalidAfterReboot>
                <tt:Timeout xmlns:tt="http://www.onvif.org/ver10/schema">PT60S</tt:Timeout>
            </trt:MediaUri>
        </trt:GetSnapshotUriResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _get_service_capabilities(self, body: bytes) -> bytes:
        """Handle GetServiceCapabilities request."""
        response = '''
        <trt:GetServiceCapabilitiesResponse xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
            <trt:Capabilities SnapshotUri="false" Rotation="false" VideoSourceMode="false" OSD="false">
                <trt:ProfileCapabilities MaximumNumberOfProfiles="1"/>
                <trt:StreamingCapabilities RTPMulticast="false" RTP_TCP="true" RTP_RTSP_TCP="true" NonAggregateControl="false"/>
            </trt:Capabilities>
        </trt:GetServiceCapabilitiesResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _get_video_source_config_options(self, body: bytes) -> bytes:
        """Handle GetVideoSourceConfigurationOptions request."""
        response = f'''
        <trt:GetVideoSourceConfigurationOptionsResponse xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
            <trt:Options>
                <tt:BoundsRange xmlns:tt="http://www.onvif.org/ver10/schema">
                    <tt:XRange>
                        <tt:Min>0</tt:Min>
                        <tt:Max>0</tt:Max>
                    </tt:XRange>
                    <tt:YRange>
                        <tt:Min>0</tt:Min>
                        <tt:Max>0</tt:Max>
                    </tt:YRange>
                    <tt:WidthRange>
                        <tt:Min>{self.config.stream_width}</tt:Min>
                        <tt:Max>{self.config.stream_width}</tt:Max>
                    </tt:WidthRange>
                    <tt:HeightRange>
                        <tt:Min>{self.config.stream_height}</tt:Min>
                        <tt:Max>{self.config.stream_height}</tt:Max>
                    </tt:HeightRange>
                </tt:BoundsRange>
                <tt:VideoSourceTokensAvailable xmlns:tt="http://www.onvif.org/ver10/schema">{self.config.video_source_token}</tt:VideoSourceTokensAvailable>
            </trt:Options>
        </trt:GetVideoSourceConfigurationOptionsResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _get_video_encoder_config_options(self, body: bytes) -> bytes:
        """Handle GetVideoEncoderConfigurationOptions request."""
        response = f'''
        <trt:GetVideoEncoderConfigurationOptionsResponse xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
            <trt:Options>
                <tt:QualityRange xmlns:tt="http://www.onvif.org/ver10/schema">
                    <tt:Min>1</tt:Min>
                    <tt:Max>10</tt:Max>
                </tt:QualityRange>
                <tt:H264 xmlns:tt="http://www.onvif.org/ver10/schema">
                    <tt:ResolutionsAvailable>
                        <tt:Width>{self.config.stream_width}</tt:Width>
                        <tt:Height>{self.config.stream_height}</tt:Height>
                    </tt:ResolutionsAvailable>
                    <tt:GovLengthRange>
                        <tt:Min>1</tt:Min>
                        <tt:Max>300</tt:Max>
                    </tt:GovLengthRange>
                    <tt:FrameRateRange>
                        <tt:Min>1</tt:Min>
                        <tt:Max>30</tt:Max>
                    </tt:FrameRateRange>
                    <tt:EncodingIntervalRange>
                        <tt:Min>1</tt:Min>
                        <tt:Max>10</tt:Max>
                    </tt:EncodingIntervalRange>
                    <tt:H264ProfilesSupported>Main</tt:H264ProfilesSupported>
                    <tt:H264ProfilesSupported>Baseline</tt:H264ProfilesSupported>
                    <tt:H264ProfilesSupported>High</tt:H264ProfilesSupported>
                </tt:H264>
            </trt:Options>
        </trt:GetVideoEncoderConfigurationOptionsResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _get_compatible_video_encoder_configs(self, body: bytes) -> bytes:
        """Handle GetCompatibleVideoEncoderConfigurations request."""
        return self._get_video_encoder_configurations(body)
        
    def _get_compatible_video_source_configs(self, body: bytes) -> bytes:
        """Handle GetCompatibleVideoSourceConfigurations request."""
        return self._get_video_source_configurations(body)
        
    def _get_audio_sources(self, body: bytes) -> bytes:
        """Handle GetAudioSources request - no audio support."""
        response = '''
        <trt:GetAudioSourcesResponse xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
        </trt:GetAudioSourcesResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _get_audio_source_configurations(self, body: bytes) -> bytes:
        """Handle GetAudioSourceConfigurations request - no audio support."""
        response = '''
        <trt:GetAudioSourceConfigurationsResponse xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
        </trt:GetAudioSourceConfigurationsResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _get_audio_encoder_configurations(self, body: bytes) -> bytes:
        """Handle GetAudioEncoderConfigurations request - no audio support."""
        response = '''
        <trt:GetAudioEncoderConfigurationsResponse xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
        </trt:GetAudioEncoderConfigurationsResponse>
        '''
        return self.soap.wrap_response(response)
