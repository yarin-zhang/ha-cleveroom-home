from typing import Dict, List, Callable, Any
import logging
from collections import defaultdict


class KLWEventEmitter:
    """
    Event emitter class, implementing event subscription, unsubscription, and triggering functions
    """

    def __init__(self):
        """Initialize the event emitter"""
        self._events: Dict[str, List[Callable]] = defaultdict(list)
        self._async_events: Dict[str, List[Callable]] = defaultdict(list)
        self.logger = logging.getLogger(__name__)

    def on(self, event_name: str, callback: Callable) -> Callable:
        """
        Subscribe to synchronous event
        Args:
            event_name: Event name
            callback: Callback function

        Returns:
            Function to unsubscribe
        """
        self._events[event_name].append(callback)

        def unsubscribe():
            self._events[event_name].remove(callback)

        return unsubscribe

    async def on_async(self, event_name: str, callback: Callable) -> Callable:
        """
        Subscribe to asynchronous event

        Args:
            event_name: Event name
            callback: Asynchronous callback function

        Returns:
            Function to unsubscribe
        """
        self._async_events[event_name].append(callback)

        def unsubscribe():
            self._async_events[event_name].remove(callback)

        return unsubscribe

    def emit(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        """
        Trigger synchronous event

        Args:
            event_name: Event name
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        if event_name not in self._events:
            # self.logger.debug(f"No listeners for event: {event_name}")
            return

        for callback in self._events[event_name]:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Error in event {event_name} callback: {e}")

    async def emit_async(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        """
        Trigger asynchronous event

        Args:
            event_name: Event name
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        if event_name not in self._async_events:
            self.logger.debug(f"No async listeners for event: {event_name}")
            return

        for callback in self._async_events[event_name]:
            try:
                await callback(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Error in async event {event_name} callback: {e}")

    def remove_all_listeners(self, event_name: str = None) -> None:
        """
        Remove all listeners

        Args:
            event_name: Optional, specifies the event name. If not specified, listeners for all events are removed
        """
        if event_name:
            self._events[event_name].clear()
            self._async_events[event_name].clear()
        else:
            self._events.clear()
            self._async_events.clear()
