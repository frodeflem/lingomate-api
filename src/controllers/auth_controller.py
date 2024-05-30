import traceback
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException
from auth import Token, get_refresh_token, get_token
from services.dtos import LoginRequest
from services.exceptions import LingoException
from services.auth_service import AuthService



class AuthController:
	def handle_exception(self, e: LingoException):
		traceback.print_exc()
		raise HTTPException(status_code=400, detail=str(e))
	
	def __init__(self, app: FastAPI):
		@app.post("/login")
		async def login(
			dto: LoginRequest,
			account_service: AuthService = Depends()
		):
			try:
				return await account_service.login(dto.email_address, dto.password)
			except LingoException as e:
				self.handle_exception(e)
		
		@app.post("/refresh-token")
		async def refresh_token(
			token: Token = Depends(get_refresh_token),
			account_service: AuthService = Depends()
		):
			try:
				return await account_service.refresh_token(token.sub)
			except LingoException as e:
				self.handle_exception(e)
