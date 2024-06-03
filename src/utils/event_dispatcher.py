# Decorator for registering event handlers
from typing import Awaitable, Callable, Type

from services.dtos import EventBase
from services.exceptions import AppException


def event_handler(event_type: Type):
	def decorator(func: Callable):
		if not hasattr(func, '_handlers'):
			func._handlers = {}
		func._handlers[event_type] = func
		return func
	return decorator

class EventDispatcher:
	def __init__(self):
		self._event_handlers: dict[Type[EventBase], Awaitable] = {}
		self._register_event_handlers()
	
	async def dispatch(self, event: EventBase, *args, **kwargs):
		handler = self._event_handlers.get(type(event), None)
		if handler is not None:
			await handler(self, event, *args, **kwargs)
	
	def _register_event_handlers(self):
		for key, value in self.__class__.__dict__.items():
			if callable(value) and hasattr(value, "_handlers"):
				for event_type, handler in value._handlers.items():
					if event_type in self._event_handlers:
						raise AppException(f"State event handler for event {event_type} already registered")
					
					self._event_handlers[event_type] = handler
