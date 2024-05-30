import datetime

import pytz
from data.models import User
from services.base_database_service import BaseDatabaseService
from sqlalchemy.ext.asyncio import AsyncSession
from services.auth_service import UserRepository, AuthService


class SeedDatabaseService:
	async def try_add_user(self, user: User):
		current = await self.user_repository.get_user_by_email(user.email_address)
		if current is None:
			self.session.add(user)
			await self.session.commit()
			await self.session.refresh(user)
		else:
			user = current

		return user
	
	async def seed_database(self):
		async with BaseDatabaseService.get_session_maker("lingomate-db")() as session:
			self.session: AsyncSession = session
			self.account_service: AuthService = AuthService(self.session)
			self.user_repository: UserRepository = self.account_service.user_repository

			await self.seed_accounts()

	async def seed_accounts(self):
		if True:
			await self.try_add_user(User(id="Frod-c549abab-4753-853f-e205668dbb95", email_address="frode_flodhest@hotmail.com", password=self.account_service._hash_password("1234"), created_at=datetime.datetime.now(pytz.UTC)))
			await self.try_add_user(User(id="Huss-c549abab-4753-853f-e205668dbb95", email_address="hussein_united@hotmail.com", password=self.account_service._hash_password("1234"), created_at=datetime.datetime.now(pytz.UTC)))
