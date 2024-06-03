import traceback
from fastapi import Depends, FastAPI, HTTPException
from services.exceptions import AppException
from services.static_data_service import StaticDataService


class StaticDataController:
	def handle_exception(self, e: AppException):
		traceback.print_exc()
		raise HTTPException(status_code=400, detail=str(e))
	

	def __init__(self, app: FastAPI):
		@app.get("/test-data")
		async def get_test_data(
			static_data_service: StaticDataService = Depends()
		):
			try:
				return await static_data_service.get_test_data()
			except AppException as e:
				self.handle_exception(e)