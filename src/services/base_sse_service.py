import asyncio
import json
from typing import Any, Callable, Mapping, Optional
from fastapi import Depends, Response
from starlette.background import BackgroundTask
from starlette.types import Receive, Scope, Send
import anyio
from anyio.abc import TaskStatus


class FunctionWrapper:
	def __init__(self, func: Callable[[Any], Any] = lambda: None):
		self.func = func

	async def __call__(self, *args, **kwargs):
		self.func(*args, **kwargs)


class AsyncStreamingResponse(Response):
	def __init__(
		self,
		status_code: int = 200,
		headers: Optional[Mapping[str, str]] = None,
		media_type: Optional[str] = None,
		background: Optional[BackgroundTask] = None,
	) -> None:
		self.coroutine_function: Optional[Callable] = None
		self.status_code = status_code
		self.media_type = self.media_type if media_type is None else media_type
		self.background = background
		self.init_headers(headers)
	
	async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
		if self.coroutine_function is None:
			raise Exception("coroutine_function must be set before the __call__ method of AsyncStreamingResponse is invoked")
		
		async with anyio.create_task_group() as task_group:
			self.send = send
			self.receive = receive
			self.task_group = task_group
			await task_group.start(self.connect)

			self.sleep_task = asyncio.create_task(self.coroutine_function())
			self.disconnect_listener_task = asyncio.create_task(self.listen_for_disconnect())

			try:
				await self.sleep_task

			except asyncio.CancelledError:
				pass

			finally:
				await send({"type": "http.response.body", "body": b"", "more_body": False})
				task_group.cancel_scope.cancel()

	async def connect(self, task_status: TaskStatus):
		task_status.started()

		await self.send({
			"type": "http.response.start",
			"status": self.status_code,
			"headers": self.raw_headers,
		})

		# Apparently, a message must be sent in addition to http.response.start in order to trigger
		# onevent on the client side:
		chunk = f":\n\n"
		await self.send({"type": "http.response.body", "body": chunk.encode(self.charset), "more_body": True})
	
	def close(self):
		self.sleep_task.cancel()

	async def send_json(self, content: Any) -> None:
		json_payload = json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        )

		await self.send({
			"type": "http.response.body",
			"body": f"data: {json_payload}\n\n".encode(self.charset),
			"more_body": True,
		})

	def set_coroutine_function(self, coroutine_function: Callable):
		self.coroutine_function = coroutine_function

	async def listen_for_disconnect(self) -> None:
		is_open = True
		
		while is_open:
			message = await self.receive()
			if message["type"] == "http.disconnect":
				is_open = False
		
		self.close()

		
class SSEResponse:
	def __new__(cls, coroutine_function: Callable) -> AsyncStreamingResponse:
		class_of_method = coroutine_function.__self__.__class__

		if not issubclass(class_of_method, BaseSSEService):
			raise TypeError(f"Class {class_of_method} must inherit from BaseSSEService")

		sse: AsyncStreamingResponse = class_of_method.sse.__get__(coroutine_function.__self__)
		sse.set_coroutine_function(coroutine_function)
		return sse


async def get_cleanup_callback():
	cleanup_callback = FunctionWrapper()
	yield cleanup_callback
	await cleanup_callback()


class BaseSSEService:
	@property
	def sse(self):
		if not hasattr(self, "_sse"):
			self._sse = AsyncStreamingResponse(media_type="text/event-stream")
			self.cleanup_callback.func = self._sse.close
		return self._sse

	def __init__(self, cleanup_callback: FunctionWrapper = Depends(get_cleanup_callback)):
		self.cleanup_callback = cleanup_callback

	def response(self, stream_coro: Callable):
		asyncio.create_task(stream_coro)
		return self.sse

	async def send_json(self, data: any):
		await self.sse.send_json(data)
	
	def close(self):
		self.cleanup_callback.func = lambda: None
		self.sse.close()


class ConcreteSSEService(BaseSSEService):
	async def send_lol(self):
		print("send_lol start")
		await asyncio.sleep(1)
		await self.send_json({"lol": "1"})
		await asyncio.sleep(1)
		await self.send_json({"lol": "2"})
		print("send_lol end")
