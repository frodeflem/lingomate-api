import asyncio
import os
import signal
from dotenv import load_dotenv
from fastapi import FastAPI
from api_application import ApiApplication
from controllers.chat_controller import ChatController
from controllers.static_data_controller import StaticDataController
from controllers.auth_controller import AuthController
from controllers.user_controller import UserController
from seed_database import SeedDatabaseService
from services.base_database_service import BaseDatabaseService



class Main:
	def __init__(self):
		self.setup_done = False
	
	async def setup(self, app: FastAPI = FastAPI()):
		env_path = os.environ.get("DOTENV_PATH", ".env")
		load_dotenv(override=True, dotenv_path=env_path)

		# Set up database
		await BaseDatabaseService.configure(
			host=os.environ.get("DATABASE_HOST"),
			port=os.environ.get("DATABASE_PORT"),
			database_name=os.environ.get("DATABASE_NAME"),
			user=os.environ.get("DATABASE_USER"),
			password=os.environ.get("DATABASE_PASSWORD")
		)
		
		await BaseDatabaseService.init_models()
		await SeedDatabaseService().seed_database()
   
		# Set up API application
		UVICORN_HOST = os.environ.get("UVICORN_HOST")
		UVICORN_PORT = int(os.environ.get("UVICORN_PORT"))
		self.api = ApiApplication(UVICORN_HOST, UVICORN_PORT, app)

		# Set up controllers'
		auth_controller = AuthController(app)
		static_data_controller = StaticDataController(app)
		user_controller = UserController(app)
		chat_controller = ChatController(app)

		# Register Ctrl+C signal handler to stop the event loop
		signal.signal(signal.SIGINT, lambda signum, frame: asyncio.create_task(self.shutdown(signum, frame)))
		signal.signal(signal.SIGTERM, lambda signum, frame: asyncio.create_task(self.shutdown(signum, frame)))

		self.setup_done = True

	async def run(self):
		if not self.setup_done:
			await self.setup()
		
		self.api_task = asyncio.create_task(self.api.run_async(), name="FastAPITask")

		while True:
			await asyncio.sleep(1)


	async def shutdown(self, signum, frame):
		print(f"Received exit signal {signum}...")

		uvicorn_coro_name = "LifespanOn.main"
		main_coro_name = "Main.run"
		main_test_coro_name = "MainTest.run"

		tasks = [t for t in asyncio.all_tasks() if True
		   and t is not asyncio.current_task()
		   and t.get_coro().__qualname__ != uvicorn_coro_name
		   and t.get_coro().__qualname__ != main_coro_name
		   and t.get_coro().__qualname__ != main_test_coro_name
		   and t.get_name() != "FastAPITask"
		]

		[task.cancel() for task in tasks]

		# Stop uvicorn manually, because it doesn't properly handle CancelledError
		if hasattr(self, "api"):
			await self.api.stop()
		
		tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
		[task.cancel() for task in tasks]

		print(f"Cancelling {len(tasks)} outstanding tasks")
		await asyncio.gather(*tasks, return_exceptions=True)



if __name__ == '__main__':
	main = Main()

	try:
		asyncio.run(main.run())
	except asyncio.exceptions.CancelledError:
		# No cleanup needed (?)
		pass
