import traceback
from fastapi import Depends, FastAPI, HTTPException
from auth import Token, get_token
from services.exceptions import LingoException
from services.user_service import UserService



class UserController:
	def handle_exception(self, e: LingoException):
		traceback.print_exc()
		raise HTTPException(status_code=400, detail=str(e))
	
	def __init__(self, app: FastAPI):
		@app.get("/user")
		async def get_user_details(
			token: Token = Depends(get_token),
			user_service: UserService = Depends()
		):
			try:
				return await user_service.get_user(token.sub)
			except LingoException as e:
				self.handle_exception(e)
