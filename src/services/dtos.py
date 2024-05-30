from __future__ import annotations
from dataclasses import dataclass
import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field



class OrmBaseModel(BaseModel):
	model_config = ConfigDict(from_attributes=True)
	
class UserDto(OrmBaseModel):
	id: str
	email_address: str

class RefreshTokenDto(BaseModel):
	refresh_token: str

class LoginRequest(BaseModel):
	email_address: str
	password: str

class LoginResponse(BaseModel):
	access_token: str
	refresh_token: str

class RefreshTokenResponse(BaseModel):
	access_token: str
