import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn



class Server(uvicorn.Server):
	def install_signal_handlers(self) -> None:
		pass


class ApiApplication():
	def __init__(self, host: str, port: int, app: FastAPI = FastAPI()):
		app.add_middleware(
			CORSMiddleware,
			allow_origins=["*"], # TODO: Do not use this for production
			allow_credentials=True,
			allow_methods=["*"],
			allow_headers=["*"],
		)

		config = uvicorn.Config(app=app, host=host, port=port)
		self.server = Server(config=config)
		self.running = False
		self.app = app


	async def stop(self):
		self.server.should_exit = True
		while self.running:
			await asyncio.sleep(0.1)


	async def run_async(self):
		try:
			self.running = True
			await self.server.serve()
			self.running = False
		
		finally:
			pass
