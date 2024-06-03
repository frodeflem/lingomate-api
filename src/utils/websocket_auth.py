import base64
import json
from fastapi import WebSocket, WebSocketException
from jwt import PyJWT
from pydantic import BaseModel
from fastapi import Depends, WebSocket, WebSocketException, status


class Token(BaseModel):
	sub: str
	user_role_id: int


class WoitWebSocketMiddleware:
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


	def websocket_headers(
		websocket: WebSocket,
	):
		if "ws_headers" in websocket.state.__dict__:
			return
		websocket.state.__setattr__("ws_headers", True)

		if "sec-websocket-protocol" not in websocket.headers:
			return

		data = WoitWebSocketMiddleware.decode_sec_websocket_protocol(websocket.headers["sec-websocket-protocol"])
		if data is None:
			return
		
		# Update request headers:
		for key, value in data["headers"].items():
			header = key.lower().encode(), value.encode()
			websocket.headers.__dict__["_list"].append(header)


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


def get_ws_token(websocket: WebSocket, token: str = Depends(WoitWebSocketMiddleware.validate_bearer_token)) -> Token:
	jwt = PyJWT()
	key = "secret"
	
	try:
		token = jwt.decode(token, algorithms=["HS256"], key=key)
	except Exception as e:
		print(f"Failed to decode JWT: token={token}")
		raise

	return Token(**token)
