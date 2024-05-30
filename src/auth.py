import base64
from datetime import datetime, timedelta
import traceback
from typing import Any, Optional
from fastapi import Depends, HTTPException, Request
import jwt
from pydantic import BaseModel

from services.dtos import RefreshTokenDto
from services.exceptions import LingoException



class Token(BaseModel):
	sub: str
	exp: int

class RefreshToken(BaseModel):
	sub: str
	exp: int


class TokenUtils:
	algorithm = "HS256"
	algorithms = [algorithm]
	
	@classmethod
	def key(cls):
		if not hasattr(cls, "_key"):
			cls._key = "secret-poop-that-is-not-very-secret-but-who-cares-in-2024"
		return cls._key
	
	@staticmethod
	def create_access_token(user_id: str):
		payload = {
			"sub": user_id,
			"exp": round((datetime.now() + timedelta(hours=2)).timestamp(), 0),
		}
		token = jwt.encode(payload, key=TokenUtils.key(), algorithm=TokenUtils.algorithm)
		return token

	@staticmethod
	def create_refresh_token(user_id: str):
		payload = {
			"sub": user_id,
			"exp": round((datetime.now() + timedelta(days=30)).timestamp(), 0),
		}
		token = jwt.encode(payload, key=TokenUtils.key(), algorithm=TokenUtils.algorithm)
		return token

	@staticmethod
	def decode_access_token(token: str, *args, **kwargs):
		payload = jwt.decode(jwt=token, key=TokenUtils.key(), algorithms=TokenUtils.algorithms, *args, **kwargs)
		return Token(sub=payload["sub"], exp=payload["exp"])
	
	@staticmethod
	def decode_refresh_token(token: str, *args, **kwargs):
		payload = jwt.decode(jwt=token, key=TokenUtils.key(), algorithms=TokenUtils.algorithms, *args, **kwargs)
		return RefreshToken(sub=payload["sub"], exp=payload["exp"])
	
	@staticmethod
	def get_bearer_token(request: Request):
		authorization = request.headers.get("Authorization")
		if not authorization:
			raise HTTPException(status_code=401)
		
		scheme, token = authorization.split()
		if scheme.lower() != "bearer":
			raise HTTPException(status_code=401)
		
		return token
	
	@staticmethod
	def get_refresh_token(dto: RefreshTokenDto):
		return dto.refresh_token

	@staticmethod
	def unvalidated_token(token = Depends(get_bearer_token)):
		try:
			payload = TokenUtils.decode_access_token(token, options={"verify_signature": False})
		except Exception as e:
			traceback.print_exc()
			raise HTTPException(status_code=403)
		
		return payload
	
	@staticmethod
	def validated_access_token(token = Depends(get_bearer_token)):
		try:
			payload = TokenUtils.decode_access_token(token)
		except Exception as e:
			traceback.print_exc()
			raise HTTPException(status_code=403)
		
		return payload
	
	@staticmethod
	def validated_refresh_token(token = Depends(get_refresh_token)):
		try:
			payload = TokenUtils.decode_refresh_token(token)
		except Exception as e:
			traceback.print_exc()
			raise HTTPException(status_code=403)
		
		return payload


def get_token(token: Token = Depends(TokenUtils.validated_access_token)):
	return token

def get_refresh_token(token: Token = Depends(TokenUtils.validated_refresh_token)):
	return token
