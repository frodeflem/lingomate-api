from typing import Any, Callable, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select


class BaseRepository:
	def __init__(self, session: AsyncSession):
		self.session: AsyncSession = session
	
	def create_getter(self, model: Type, field_name: str) -> Callable[[Any], Any]:
		if not hasattr(model, field_name):
			raise AttributeError(f"Model {model.__name__} does not have field {field_name}")
		
		async def getter(value: Any):
			query = select(model).where(getattr(model, field_name) == value)
			result = await self.select_first(query)
			
			return result

		return getter

	def create_deleter(self, model: Type, field_name: str) -> Callable[[Any], Any]:
		if not hasattr(model, field_name):
			raise AttributeError(f"Model {model.__name__} does not have field {field_name}")
		
		async def deleter(value: Any):
			statement = delete(model).where(getattr(model, field_name) == value)
			await self.delete(statement)

		return deleter

	async def get_by(self, model: Type, field_name: str, value: Any) -> Any:
		query = select(model).where(getattr(model, field_name) == value)
		result = await self.select_first(query)
		
		return result

	async def insert(self, instance: object, _warn: bool = True):
		self.session.add(instance, _warn)
		await self.session.flush()
	
	async def delete(self, statement):
		await self.session.execute(statement)

	async def select_first(self, statement):
		return (await self.session.scalars(statement)).first()
	
	async def select_all(self, statement):
		return (await self.session.scalars(statement)).all()

	async def select_all_unique(self, statement):
		return (await self.session.execute(statement)).unique().scalars().all()
