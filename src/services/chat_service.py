from fastapi import WebSocket
from services.base_websocket_worker import BaseWebsocketWorker, WebsocketDataBase



class AudioData(WebsocketDataBase):
	type: str = "audio_data"
	audio: bytes

class VoiceChatWorker(BaseWebsocketWorker):
	def __init__(self):
		data_models = [
			AudioData
		]

		super().__init__(data_models)
	
	async def on_connected(self):
		print("WebSocket: VoiceChatWorker connected")

	async def on_disconnected(self):
		print("WebSocket: VoiceChatWorker disconnected")

	async def on_data(self, data: WebsocketDataBase):
		print(f"WebSocket: VoiceChatWorker data: {data}")


class ChatService:
	async def start_voice_chat(self, websocket: WebSocket):
		worker = VoiceChatWorker()
		await worker.begin(websocket)
	