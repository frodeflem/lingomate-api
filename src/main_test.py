import asyncio
from contextlib import asynccontextmanager
import traceback
from typing import Callable
from fastapi import Depends, FastAPI, HTTPException
import httpx
from auth import TokenUtils
from main import Main
from services.exceptions import AppException



class TestController:
	def handle_exception(self, e: AppException):
		traceback.print_exc()
		raise HTTPException(status_code=400, detail=str(e))
	
	def __init__(self, app: FastAPI):
		@app.get("/test-controller/test")
		async def test_controller_test():
			print("Test controller test")
			return "Test controller test"
		


class MainTest:
	def __init__(self):
		self.main = Main()

	async def test_frode(self):
		user_token = TokenUtils.create_access_token(2143, None)
		headers = {
			"Authorization": f"Bearer {user_token}"
		}
		
		if False:
			async with httpx.AsyncClient() as client:
				response = await client.get(f"http://127.0.0.1:8013/test-controller/test", headers=headers)
	
	async def try_wrap(self, coro_function: Callable):
		try:
			await coro_function()
		except Exception as e:
			traceback.print_exc()

	async def run(self):
		@asynccontextmanager
		async def lifespan(app: FastAPI):
			asyncio.create_task(self.try_wrap(self.test_frode))
			yield
			
		app = FastAPI(lifespan=lifespan)

		session_controller = TestController(app)
		
		await self.main.setup(app)
		await self.main.run()


if __name__ == '__main__':
	main = MainTest()

	try:
		asyncio.run(main.run())
	except asyncio.exceptions.CancelledError:
		# No cleanup needed (?)
		pass
