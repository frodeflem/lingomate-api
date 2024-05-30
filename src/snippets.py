if False:
			while True:
				async with SessionService() as session_service:
					travian_service = TravianService(session_service.session, await session_service.get_session_by_name_host(username, host))
					
					if False:
						resources = await travian_service.get_resources()
						print(f"resources: {resources.currently_constructing}")
					
					elif False:
						await travian_service.upgrade_building(6, True)
					
					elif True:
						## Repeatedly send farm lists every 4-6 minutes:
						
							print("Sending farm lists...")
							await travian_service.send_farm_lists()
							# Sleep random duration between 4-6 minutes
						
					else:
						# Load the HTML file
						with open("response.html", "r", encoding="utf-8") as file:
							html_content = file.read()

							if False:
								# Parse the HTML content
								soup = BeautifulSoup(html_content, "html.parser")
								resources_parsed = parse_resources(soup)
								print(f"troops: {resources_parsed.troops}")
							else:
								# Parse the HTML content
								soup = BeautifulSoup(html_content, "html.parser")
								href = "/build.php?id=29"
								building_parsed = parse_building(soup, href)
								print(f"building: {building_parsed}")
								
				await asyncio.sleep(4*60 + random.randint(0, 120))
		
		elif False:
			# Test map info (attack markers)
			async with SessionService() as session_service:
				travian_service = TravianService(session_service.session, await session_service.get_session_by_name_host(username, host))
				data = {"data":[{"position":{"x0":-100,"y0":-200,"x1":-1,"y1":-101}},{"position":{"x0":0,"y0":-200,"x1":99,"y1":-101}},{"position":{"x0":-200,"y0":-200,"x1":-101,"y1":-101}},{"position":{"x0":-100,"y0":0,"x1":-1,"y1":99}},{"position":{"x0":0,"y0":0,"x1":99,"y1":99}},{"position":{"x0":-200,"y0":0,"x1":-101,"y1":99}},{"position":{"x0":-100,"y0":-100,"x1":-1,"y1":-1}},{"position":{"x0":0,"y0":-100,"x1":99,"y1":-1}},{"position":{"x0":-200,"y0":-100,"x1":-101,"y1":-1}}],"zoomLevel":3}
				data = {"data":[{"position":{"x0":-40,"y0":-80,"x1":-31,"y1":-71}},{"position":{"x0":-30,"y0":-80,"x1":-21,"y1":-71}},{"position":{"x0":-20,"y0":-80,"x1":-11,"y1":-71}}],"zoomLevel":1}
				response = await travian_service.travian.post("/api/v1/map/info", data=data)
				travian_service.travian.save_response(response, "response_map_info.json")
		
		elif False:
			if False:
				# Refresh map data
				async with SessionService() as session_service:
					travian_service = TravianService(session_service.session, await session_service.get_session_by_name_host(username, host))
					# await travian_service.get_map_data(-44, 101)
					await travian_service.get_map_data(-24, -67)
				
			with open("response_map_position.json", "r", encoding="utf-8") as file:
				data = json.load(file)
				
			with open("response_map_position_pretty.json", "w", encoding="utf-8") as file:
				file.write(json.dumps(data, indent=4))
			
			map_parsed = parse_map(data)
			# print(f"map_parsed: {map_parsed}")
		
		elif False:
			async with SessionService() as session_service:
				travian_service = TravianService(session_service.session, await session_service.get_session_by_name_host(username, host))
				await travian_service.get_map_data(11, -188)