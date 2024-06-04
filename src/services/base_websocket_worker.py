import asyncio
import enum
from functools import partial
import json
import traceback
from typing import Any
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from pydantic import BaseModel
from websockets import ConnectionClosedOK
from services.dtos import EventBase
from asyncio import Queue

from services.exceptions import AppException


class WebsocketDataBase(EventBase):
	pass

class DataMode(enum.IntEnum):
	Text = 0
	Binary = 1


class BaseWebsocketWorker:
	def __init__(self, data_models: list[WebsocketDataBase] = [], data_mode=DataMode.Text):
		self.data_models: dict[str, WebsocketDataBase] = {model.model_fields["type"].default: model for model in data_models}
		self.data_mode = data_mode
		self.websocket = None
		self.should_exit = False
		self.queue = Queue()
		self.queue_task = None

	@property
	def is_connected(self):
		return self.websocket is not None and self.websocket.application_state == WebSocketState.CONNECTED

	async def process_queue(self):
		while not self.should_exit:
			coro_func = await self.queue.get()
			await coro_func()
			self.queue.task_done()
	
	async def process_json_message(self, text: str):
		try:
			json_data = json.loads(text)

			if "type" not in json_data:
				raise AppException(f"No type field in message: {json_data}")
			
			model = self.data_models.get(json_data["type"], None)
			if model is None:
				raise AppException(f"Invalid data model in message: {json_data}")

			data = model(**json_data)
			task_creator = partial(self.on_json_data, data)
			self.queue.put_nowait(task_creator)
		
		# Handle pydantic validation errors
		except (json.JSONDecodeError, AppException) as e:
			traceback.print_exc()
			error_resp = {
				"message": f"{e.__class__.__name__}: {e}",
				"type": "error"
			}
			await self.websocket.send_json(error_resp)
	
	async def process_binary_message(self, data: bytes):
		task_creator = partial(self.on_binary_data, data)
		self.queue.put_nowait(task_creator)

	async def begin(self, websocket: WebSocket):
		self.websocket = websocket
		self.should_exit = False
			
		if websocket.application_state == WebSocketState.DISCONNECTED:
			# This usually means the connection was closed before the handshake was completed
			return

		if self.data_mode == DataMode.Text:
			receive_func = websocket.receive_text
			process_func = self.process_json_message
		else:
			receive_func = websocket.receive_bytes
			process_func = self.process_binary_message
		
		await websocket.accept()

		try:
			await self.on_connected()
			self.queue_task = asyncio.create_task(self.process_queue())
			
			while not self.should_exit:
				data = await websocket.receive()
				text = data.get("text", None)
				if text is not None:
					task_creator = partial(self.process_json_message, text)
					self.queue.put_nowait(task_creator)
				else:
					binary = data.get("bytes", None)
					if binary is not None:
						task_creator = partial(self.process_binary_message, binary)
						self.queue.put_nowait(task_creator)
		
		except WebSocketDisconnect as e:
			pass

		finally:
			await self.close()
			await self.on_disconnected()

	async def close(self):
		if self.queue_task is not None:
			self.queue_task.cancel()
			
		self.should_exit = True
		if self.websocket:
			try:
				await self.websocket.close()

			except RuntimeError:
				# Will be thrown if the connection is already closed
				pass

	async def send(self, data: Any):
		# Verify that the data type inherits from BaseModel:
		# if not issubclass(type(data), BaseModel):
		# 	raise LingoException(f"Data type {type(data)} does not inherit from BaseModel")
		
		if self.websocket and self.websocket.application_state == WebSocketState.CONNECTED:
			# print(f"ACTUALLY Sending: {data}")
			try:
				await self.websocket.send_json(data)
			except ConnectionClosedOK as e:
				pass

			return True
		else:
			return False
	
	async def send_json(self, data: BaseModel):
		# Verify that the data type inherits from BaseModel:
		if not issubclass(type(data), BaseModel):
			raise AppException(f"Data type {type(data)} does not inherit from BaseModel")
		
		if self.websocket and self.websocket.application_state == WebSocketState.CONNECTED:
			try:
				await self.websocket.send_text(json.dumps(data.model_dump()))
			except ConnectionClosedOK as e:
				pass

			return True
		else:
			return False
	
	async def send_binary(self, data: bytes):
		if self.websocket and self.websocket.application_state == WebSocketState.CONNECTED:
			try:
				await self.websocket.send_bytes(data)
			except ConnectionClosedOK as e:
				pass

			return True
		else:
			return False
		
	def add_data_models_in(self, models: dict[str, BaseModel]):
		self.data_models.update(models)

	async def on_connected(self):
		pass

	async def on_disconnected(self):
		pass

	async def on_json_data(self, data: WebsocketDataBase):
		pass

	async def on_binary_data(self, data: bytes):
		pass



class ConnectionManager:
	def __init__(self, connection_type: str):
		self.connection_type = connection_type
		self.connections: dict[str, BaseWebsocketWorker] = {}
	

	async def begin_unique(self, websocket: WebSocket, client_id: str, **kwargs: Any):
		existing_connection = self.connections.get(client_id, None)

		# Close the connection
		if existing_connection is not None:
			print(f"Connected: {client_id} (Replacement {self.connection_type})")
			connection = self.create_connection(client_id, websocket, **kwargs)
			self.connections[client_id] = connection

			await existing_connection.close()
			await connection.begin()

		else:
			print(f"Connected: {client_id} ({self.connection_type})")
			connection = self.create_connection(client_id, websocket, **kwargs)
			self.connections[client_id] = connection
			await connection.begin()

		# Remove the client from the list of clients only if it owns the websocket connection:
		if connection == self.connections[client_id]:
			print(f"Disconnected: {client_id} ({self.connection_type})")
			del self.connections[client_id]
	

	def create_connection(self, client_id: str, websocket: WebSocket) -> BaseWebsocketWorker:
		raise NotImplementedError()
