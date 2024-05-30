import asyncio
from functools import wraps
from typing import Type, TypeVar
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from data.models import Base


async def get_database_session():
	async with BaseDatabaseService.create_session() as session:
		yield session


class BaseDatabaseService2:
	def get_session_maker(self) -> sessionmaker:
		raise NotImplementedError  # This should be implemented by the child class

	@classmethod
	async def get_db_session(cls):
		session_maker = cls.get_session_maker()
		async with session_maker() as session:
			session: AsyncSession
			yield session

	def __init__(self, session: AsyncSession = Depends(get_db_session)):
		self.session = session
	
	async def __aenter__(self):
		if type(self.session) is not AsyncSession:
			session = self.get_session_maker()()
			self.__init__(session)
			
		return self
	
	async def __aexit__(self, exc_type, exc_val, exc_tb):
		await self.session.close()


class BaseDatabaseService:
	engines: dict[str, AsyncEngine] = {}
	session_makers: dict[str, sessionmaker] = {}

	@staticmethod
	def get_engine(database: str):
		engine = BaseDatabaseService.engines.get(database)
		if engine is None:
			url = "mysql+aiomysql://" + BaseDatabaseService.user + ":" + BaseDatabaseService.password + "@" + BaseDatabaseService.host + ":" + BaseDatabaseService.port + "/" + database

			engine = create_async_engine(url, future=True, echo=False, pool_size=0, max_overflow=1, pool_recycle=3600, pool_pre_ping=True)
			BaseDatabaseService.engines[database] = engine
		
		return engine

	@staticmethod
	def get_session_maker(database: str):
		session_maker = BaseDatabaseService.session_makers.get(database)
		if session_maker is None:
			engine = BaseDatabaseService.get_engine(database)

			session_maker = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
			BaseDatabaseService.session_makers[database] = session_maker
		
		return session_maker
	
	@staticmethod
	async def configure(host, port, database_name, user, password):
		complete_sql_string = user + ":" + password + "@" + host +":" + port + "/" + database_name
		DATABASE_URL = "mysql+aiomysql://" + complete_sql_string
		# database = databases.Database(DATABASE_URL)
		
		BaseDatabaseService.host = host
		BaseDatabaseService.port = port
		BaseDatabaseService.database = database_name
		BaseDatabaseService.user = user
		BaseDatabaseService.password = password
		# BaseDatabaseService.engine = create_async_engine(DATABASE_URL, future=True, echo=False, pool_size=0, max_overflow=1)
		# BaseDatabaseService.create_session = sessionmaker(BaseDatabaseService.engine, expire_on_commit=False, class_=AsyncSession)
		BaseDatabaseService.engine = BaseDatabaseService.get_engine(database_name)
		BaseDatabaseService.create_session = BaseDatabaseService.get_session_maker(database_name)

		# Run a background task that will ensure that the engine is disposed of before the event loop is closed:
		async def run():
			try:
				while True:
					await asyncio.sleep(86400)
			except asyncio.exceptions.CancelledError:
				for engine in BaseDatabaseService.engines.values():
					await engine.dispose()
		
		asyncio.create_task(run())

	
	async def init_models():
		# Prevent accidental initialization of the database on production
		if BaseDatabaseService.database.startswith("lingomate-db") or BaseDatabaseService.database.startswith("ts"):
			async with BaseDatabaseService.engine.begin() as conn:
				# await conn.run_sync(Base.metadata.drop_all)
				await conn.run_sync(Base.metadata.create_all)
	
	
	def __init__(self, session: AsyncSession = Depends(get_database_session)):
		self.session = session
	
	async def __aenter__(self):
		if type(self.session) is not AsyncSession:
			session = self.create_session()
			self.__init__(session)
			
		return self
	
	async def __aexit__(self, exc_type, exc_val, exc_tb):
		await self.session.close()


T = TypeVar('T')
def Depend(dependency_class: Type[T]) -> T:
	dependency_attr = f"_{dependency_class.__name__}_instance"

	@property
	@wraps(dependency_class)
	def dependency_resolver(self):
		if not hasattr(self, dependency_attr):
			setattr(self, dependency_attr, dependency_class(self.session))
		return getattr(self, dependency_attr)

	return dependency_resolver
