import json
from fastapi import WebSocket
from services.base_websocket_worker import BaseWebsocketWorker, DataMode, WebsocketDataBase



class AudioData(WebsocketDataBase):
	type: str = "audio_data"
	audio: bytes

class TestData(WebsocketDataBase):
	type: str = "test_data"
	data: str

class VoiceChatWorker(BaseWebsocketWorker):
	def __init__(self):
		data_models = [
			AudioData,
			TestData,
		]

		super().__init__(data_models, data_mode=DataMode.Binary)
	
	async def on_connected(self):
		print("WebSocket: VoiceChatWorker connected")

	async def on_disconnected(self):
		print("WebSocket: VoiceChatWorker disconnected")

	async def on_json_data(self, data: WebsocketDataBase):
		print(f"WebSocket: VoiceChatWorker data: {data}")
		await self.send_json(data)
	
	async def on_binary_data(self, data: bytes):
		print(f"WebSocket: VoiceChatWorker binary data.")
		await self.send_binary(data)


class ChatService:
	async def start_voice_chat(self, websocket: WebSocket):
		worker = VoiceChatWorker()
		await worker.begin(websocket)
	