from data.base_repository import BaseRepository
from services.base_database_service import BaseDatabaseService, Depend


class StaticDataRepository(BaseRepository):
	pass


class StaticDataService(BaseDatabaseService):
	static_data_repository = Depend(StaticDataRepository)

	async def get_test_data(self):
		return {
			"meaning_of_life": 42
		}
