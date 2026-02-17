"""ONVIF Events Service implementation."""

import logging
from datetime import datetime, timezone, timedelta
from lxml import etree

from onvif_rtsp_bridge.config import Config
from onvif_rtsp_bridge.utils.soap_utils import SoapHandler

logger = logging.getLogger(__name__)


class EventsService:
    """ONVIF Events Service for Profile S."""
    
    def __init__(self, config: Config, soap_handler: SoapHandler):
        self.config = config
        self.soap = soap_handler
        
        # Map of actions to handlers
        self.actions = {
            'GetServiceCapabilities': self._get_service_capabilities,
            'GetEventProperties': self._get_event_properties,
            'CreatePullPointSubscription': self._create_pull_point_subscription,
            'PullMessages': self._pull_messages,
            'Unsubscribe': self._unsubscribe,
            'Renew': self._renew,
            'Subscribe': self._subscribe,
        }
        
    async def handle_request(self, body: bytes) -> bytes:
        """Handle incoming SOAP request."""
        action = self.soap.get_action(body)
        logger.info(f"Events Service action: {action}")
        
        handler = self.actions.get(action)
        if handler:
            return handler(body)
        else:
            logger.warning(f"Unknown action: {action}")
            return self.soap.create_fault("ActionNotSupported", f"Action {action} not supported")
            
    def _get_service_capabilities(self, body: bytes) -> bytes:
        """Handle GetServiceCapabilities request."""
        response = '''
        <tev:GetServiceCapabilitiesResponse xmlns:tev="http://www.onvif.org/ver10/events/wsdl">
            <tev:Capabilities WSSubscriptionPolicySupport="false" WSPullPointSupport="true" 
                WSPausableSubscriptionManagerInterfaceSupport="false" MaxNotificationProducers="1" 
                MaxPullPoints="2" PersistentNotificationStorage="false"/>
        </tev:GetServiceCapabilitiesResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _get_event_properties(self, body: bytes) -> bytes:
        """Handle GetEventProperties request."""
        response = '''
        <tev:GetEventPropertiesResponse xmlns:tev="http://www.onvif.org/ver10/events/wsdl"
            xmlns:wsnt="http://docs.oasis-open.org/wsn/b-2"
            xmlns:wstop="http://docs.oasis-open.org/wsn/t-1">
            <tev:TopicNamespaceLocation>http://www.onvif.org/onvif/ver10/topics/topicns.xml</tev:TopicNamespaceLocation>
            <wsnt:FixedTopicSet>true</wsnt:FixedTopicSet>
            <wstop:TopicSet>
                <tt:Device xmlns:tt="http://www.onvif.org/ver10/schema">
                    <tt:Trigger wstop:topic="true">
                        <tt:MessageDescription IsProperty="false">
                            <tt:Source>
                                <tt:SimpleItemDescription Name="VideoSourceToken" Type="tt:ReferenceToken"/>
                            </tt:Source>
                        </tt:MessageDescription>
                    </tt:Trigger>
                </tt:Device>
            </wstop:TopicSet>
            <wsnt:TopicExpressionDialect>http://www.onvif.org/ver10/tev/topicExpression/ConcreteSet</wsnt:TopicExpressionDialect>
            <wsnt:TopicExpressionDialect>http://docs.oasis-open.org/wsn/t-1/TopicExpression/Concrete</wsnt:TopicExpressionDialect>
            <tev:MessageContentFilterDialect>http://www.onvif.org/ver10/tev/messageContentFilter/ItemFilter</tev:MessageContentFilterDialect>
            <tev:MessageContentSchemaLocation>http://www.onvif.org/onvif/ver10/schema/onvif.xsd</tev:MessageContentSchemaLocation>
        </tev:GetEventPropertiesResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _create_pull_point_subscription(self, body: bytes) -> bytes:
        """Handle CreatePullPointSubscription request."""
        now = datetime.now(timezone.utc)
        termination = now + timedelta(hours=1)
        
        response = f'''
        <tev:CreatePullPointSubscriptionResponse xmlns:tev="http://www.onvif.org/ver10/events/wsdl"
            xmlns:wsnt="http://docs.oasis-open.org/wsn/b-2"
            xmlns:wsa="http://www.w3.org/2005/08/addressing">
            <tev:SubscriptionReference>
                <wsa:Address>{self.config.events_service_url}</wsa:Address>
            </tev:SubscriptionReference>
            <wsnt:CurrentTime>{now.isoformat()}</wsnt:CurrentTime>
            <wsnt:TerminationTime>{termination.isoformat()}</wsnt:TerminationTime>
        </tev:CreatePullPointSubscriptionResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _pull_messages(self, body: bytes) -> bytes:
        """Handle PullMessages request - returns empty (no events)."""
        now = datetime.now(timezone.utc)
        termination = now + timedelta(hours=1)
        
        response = f'''
        <tev:PullMessagesResponse xmlns:tev="http://www.onvif.org/ver10/events/wsdl">
            <tev:CurrentTime>{now.isoformat()}</tev:CurrentTime>
            <tev:TerminationTime>{termination.isoformat()}</tev:TerminationTime>
        </tev:PullMessagesResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _unsubscribe(self, body: bytes) -> bytes:
        """Handle Unsubscribe request."""
        response = '''
        <wsnt:UnsubscribeResponse xmlns:wsnt="http://docs.oasis-open.org/wsn/b-2">
        </wsnt:UnsubscribeResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _renew(self, body: bytes) -> bytes:
        """Handle Renew request."""
        now = datetime.now(timezone.utc)
        termination = now + timedelta(hours=1)
        
        response = f'''
        <wsnt:RenewResponse xmlns:wsnt="http://docs.oasis-open.org/wsn/b-2">
            <wsnt:TerminationTime>{termination.isoformat()}</wsnt:TerminationTime>
            <wsnt:CurrentTime>{now.isoformat()}</wsnt:CurrentTime>
        </wsnt:RenewResponse>
        '''
        return self.soap.wrap_response(response)
        
    def _subscribe(self, body: bytes) -> bytes:
        """Handle Subscribe request."""
        now = datetime.now(timezone.utc)
        termination = now + timedelta(hours=1)
        
        response = f'''
        <wsnt:SubscribeResponse xmlns:wsnt="http://docs.oasis-open.org/wsn/b-2"
            xmlns:wsa="http://www.w3.org/2005/08/addressing">
            <wsnt:SubscriptionReference>
                <wsa:Address>{self.config.events_service_url}</wsa:Address>
            </wsnt:SubscriptionReference>
            <wsnt:CurrentTime>{now.isoformat()}</wsnt:CurrentTime>
            <wsnt:TerminationTime>{termination.isoformat()}</wsnt:TerminationTime>
        </wsnt:SubscribeResponse>
        '''
        return self.soap.wrap_response(response)
