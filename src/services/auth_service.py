import bcrypt
from sqlalchemy import select
from auth import TokenUtils
from data.base_repository import BaseRepository
from data.models import User
from services.base_database_service import BaseDatabaseService, Depend
from services.dtos import LoginResponse, RefreshTokenResponse
from services.exceptions import AppException
from services.user_service import UserRepository


class AuthService(BaseDatabaseService):
	user_repository = Depend(UserRepository)

	
	async def login(self, username: str, password: str):
		user = await self.user_repository.get_user_by_email(username)
		if not user or not self._validate_password(password, user.password):
			raise AppException("Incorrect username or password")
		
		access_token = TokenUtils.create_access_token(user.id)
		refresh_token = TokenUtils.create_refresh_token(user.id)
		return LoginResponse(
			access_token=access_token,
			refresh_token=refresh_token,
		)
	
	async def refresh_token(self, user_id: str):
		admin = await self.user_repository.get_user(user_id)
		if not admin:
			raise AppException(f"Failed to refresh access token")

		access_token = TokenUtils.create_access_token(admin.id)
		return RefreshTokenResponse(
			access_token=access_token,
		)

	def _hash_password(self, password: str):
		salt = bcrypt.gensalt()
		return bcrypt.hashpw(password.encode('utf-8'), salt)
	
	def _validate_password(self, password: str, hashed_password: str):
		return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
