import base64
from datetime import datetime, timedelta
import json
import traceback
from typing import Any, Optional
from fastapi import Depends, HTTPException, Request, WebSocket, WebSocketException, status
import jwt
from pydantic import BaseModel

from services.dtos import RefreshTokenDto
from services.exceptions import AppException



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
			"exp": round((datetime.now() + timedelta(hours=1)).timestamp(), 0),
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

	@staticmethod
	def decode_sec_websocket_protocol(data: str) -> dict:
		data = data.split(",")
		data = [element.strip() for element in data]
		data = next((element for element in data if element.startswith("||")), None)
		if data is None:
			return None
		
		data = data[2:]

		# Replace ['+', '/', '='] -> ['.', '|', '=']
		data = data.replace("+", ".").replace("/", "|").replace("-", "=")
		data = base64.b64decode(data)
		data = json.loads(data)

		return data

	@staticmethod
	def websocket_headers(
		websocket: WebSocket,
	):
		if "ws_headers" in websocket.state.__dict__:
			return
		websocket.state.__setattr__("ws_headers", True)

		if "sec-websocket-protocol" not in websocket.headers:
			return

		data = TokenUtils.decode_sec_websocket_protocol(websocket.headers["sec-websocket-protocol"])
		if data is None:
			return
		
		# Update request headers:
		for key, value in data["headers"].items():
			header = key.lower().encode(), value.encode()
			websocket.headers.__dict__["_list"].append(header)

	@staticmethod
	def validate_bearer_token(websocket: WebSocket, _ = Depends(websocket_headers)):
		authorization_header = websocket.headers.get("authorization")
		if authorization_header is None:
			raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
		
		authorization_header = authorization_header.split(" ")
		if len(authorization_header) != 2:
			raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
		
		if authorization_header[0] != "Bearer":
			raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
		
		token = authorization_header[1]
		return token


def get_token(token: Token = Depends(TokenUtils.validated_access_token)):
	return token

def get_refresh_token(token: Token = Depends(TokenUtils.validated_refresh_token)):
	return token

def get_ws_token(websocket: WebSocket, token: str = Depends(TokenUtils.validate_bearer_token)) -> Token:
	key = TokenUtils.key()
	
	try:
		token = jwt.decode(token, algorithms=["HS256"], key=key)
	except Exception as e:
		print(f"Failed to decode JWT: token={token}")
		raise

	return Token(**token)
