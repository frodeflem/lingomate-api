import asyncio
from datetime import timedelta
import traceback
from typing import Callable


class RestartableTimer:
	def __init__(self):
		self._timer_task = None
		self.on_cancel = None
	
	def __enter__(self):
		return self
	
	def __exit__(self, exc_type, exc_val, exc_tb):
		self.cancel()
	
	async def _callback_with_delay(self, delay: timedelta, callback: Callable):
		try:
			await asyncio.sleep(delay.total_seconds())
			
			try:
				result = callback()
				if asyncio.iscoroutine(result):
					await result
			except Exception as e:
				traceback.print_exc()

		except asyncio.CancelledError:
			if self.on_cancel:
				result = callback()
				if asyncio.iscoroutine(result):
					await result
			else:
				raise

	def pending(self):
		return self._timer_task and not self._timer_task.done()

	def cancel(self):
		if self._timer_task:
			self._timer_task.cancel()

	def schedule(self, delay: timedelta, callback: Callable, on_cancel: Callable = None):
		self.on_cancel = on_cancel
		self.cancel()
		self._timer_task = asyncio.create_task(self._callback_with_delay(delay, callback))
	
	def schedule_no_restart(self, delay: timedelta, callback: Callable, on_cancel: Callable = None):
		self.on_cancel = on_cancel
		if not self._timer_task or self._timer_task.done():
			self.schedule(delay, callback)
