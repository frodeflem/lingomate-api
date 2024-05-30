import bcrypt
from sqlalchemy import select
from auth import TokenUtils
from data.base_repository import BaseRepository
from data.models import User
from services.base_database_service import BaseDatabaseService, Depend
from services.dtos import LoginResponse, RefreshTokenResponse, UserDto
from services.exceptions import LingoException


class UserRepository(BaseRepository):
	async def get_user(self, id: str) -> User:
		return await self.select_first(
			select(User).
			where(User.id == id)
		)
	
	async def get_user_by_email(self, email_address: str) -> User:
		return await self.select_first(
			select(User).
			where(User.email_address == email_address)
		)


class UserService(BaseDatabaseService):
	user_repository = Depend(UserRepository)

	
	async def get_user(self, id: str):
		user = await self.user_repository.get_user(id)
		dto = UserDto.model_validate(user)
		return dto
