"""
Abstract interface for notification services.
Follows the Dependency Inversion Principle.
"""
from abc import ABC, abstractmethod
from typing import Optional


class INotificationService(ABC):
    """Interface for sending notifications (Pushbullet, email, SMS, etc.)"""
    
    @abstractmethod
    def send_notification(self, message: str, title: str) -> bool:
        """
        Send a notification to the user.
        
        Args:
            message: The notification message content
            title: The notification title
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        pass


class PushbulletNotificationService(INotificationService):
    """Concrete implementation using Pushbullet"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Pushbullet notification service.
        
        Args:
            api_key: Pushbullet API key. If None, notifications are disabled.
        """
        self.api_key = api_key
    
    def send_notification(self, message: str, title: str) -> bool:
        """Send notification via Pushbullet"""
        if not self.api_key:
            return False
        
        from src.lib.pushbullet_notify import send_pushbullet_notification
        return send_pushbullet_notification(self.api_key, message, title)


class NoOpNotificationService(INotificationService):
    """Null object pattern - does nothing"""
    
    def send_notification(self, message: str, title: str) -> bool:
        """No-op implementation"""
        return True
