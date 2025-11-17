"""
Abstract interface for calendar repositories.
Follows the Dependency Inversion Principle.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from src.models.calendar_data import ParsedEvent


class ICalendarRepository(ABC):
    """Interface for calendar data storage (CalDAV, local files, etc.)"""
    
    @abstractmethod
    def get_events(self) -> Dict[str, Any]:
        """
        Fetch all events from the calendar.
        
        Returns:
            Dictionary mapping event identifiers to event objects
        """
        pass
    
    @abstractmethod
    def put_event(self, uid: str, ical_data: str) -> bool:
        """
        Create or update an event in the calendar.
        
        Args:
            uid: Unique identifier for the event
            ical_data: iCalendar formatted event data
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def delete_event(self, event_id: str) -> bool:
        """
        Delete an event from the calendar.
        
        Args:
            event_id: Unique identifier for the event
            
        Returns:
            True if successful, False otherwise
        """
        pass
