import io
import json
import os
import traceback
from fastapi import WebSocket
from services.base_websocket_worker import BaseWebsocketWorker, DataMode, WebsocketDataBase
from openai import AsyncOpenAI


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

		try:
			buffer = io.BytesIO(data)
			buffer.name = "audio.m4a"

			client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
			transcription = await client.audio.transcriptions.create(
				model="whisper-1",
				file=buffer,
				response_format="text"
			)

			print(f"Transcription: {transcription}")

			response = await client.chat.completions.create(
				model="gpt-4o",
				messages=[
					{"role": "system", "content": "You are a helpful assistant."},
					{"role": "user", "content": transcription},
				],
				max_tokens=1000,
			)

			gpt_response = response.choices[0].message.content
			print(f"GPT Response: {gpt_response}")

			response = await client.audio.speech.create(
				model="tts-1",
				voice="alloy",
				input=gpt_response,
				response_format="mp3"
			)

			# Convert the response to binary data
			speech = response.content

			print(f"Sending speech data: {len(speech)} bytes")
			await self.send_binary(speech)
			print("Speech data sent")

		except Exception as e:
			traceback.print_exc()
		
			await self.send_binary(data)


class ChatService:
	async def start_voice_chat(self, websocket: WebSocket):
		worker = VoiceChatWorker()
		await worker.begin(websocket)
	