import traceback
from fastapi import Depends, FastAPI, HTTPException, WebSocket
from auth import Token, get_token, get_ws_token
from services.exceptions import AppException
from services.chat_service import ChatService



class ChatController:
	def handle_exception(self, e: AppException):
		traceback.print_exc()
		raise HTTPException(status_code=400, detail=str(e))
	
	def __init__(self, app: FastAPI):
		@app.websocket("/chat")
		async def chat(
			websocket: WebSocket,
			token: Token = Depends(get_ws_token),
			chat_service: ChatService = Depends()
		):
			try:
				return await chat_service.start_voice_chat(websocket)
			except AppException as e:
				self.handle_exception(e)
