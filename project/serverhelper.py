import asyncio, aiohttp, time, json
import logging
import config

class Server:
	port = 0
	name = ""
	data = {}
	loop = None

	def __init__(self, name, port):
	 	self.name = name
	 	self.port = port
	 	logging.basicConfig(filename=name, level = logging.DEBUG)
	 	logging.debug('Creating {0}'.format(name))

	async def client_read(self, reader, writer):
		command = ""
		try:
			comm = await reader.readline()
			command = comm.decode()
			logging.debug('Running command {0}'.format(command))
		finally:
			if not(await self.isValid(command)):
				key = "? {0}".format(command)
				writer.write(key.encode())
				logging.error("Command not valid: {0}".format(key))
			else:
				x = command.split()
				if x[0] == 'WHATSAT':
					e = self.data.get(x[1])
					if e == None:
						key = "? {0}".format(command)
						writer.write(key.encode())
					else:
						writer.write(e.encode())
						writer.write('\n'.encode())
						radius = int(x[2]) * 1000
						bound = int(x[3])
						param = e.split()
						geo_string = param[4]
						ll = await self.getLatLong(geo_string)
						maps_key = config.API_KEY
						location = "{0},{1}".format(ll[0], ll[1])
						#js = {'location': location, 'radius': radius, 'key': maps_key}
						url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={0}&radius={1}&key={2}'.format(location, radius, maps_key)
						loop = asyncio.get_event_loop()
						async with aiohttp.ClientSession(connector =aiohttp.TCPConnector(verify_ssl=False), loop=loop) as client:
							async with client.get(url) as response:
								 js = await response.json()
								 if len(js['results']) > bound:
								 	js['results'] = js['results'][:bound]
								 dumpjs = json.dumps(js, indent = 2)
								 writer.write(dumpjs.encode())
								 logging.debug("{1} \n {0}".format(js, e))
						await client.close()
						writer.write('\n\n'.encode())
				elif x[0] == 'IAMAT':
					t = float(time.time()) - float(x[3]) 
					tt = ''
					if t > 0:
						tt = '+'
						tt += str(t)
					else:
						tt = str(t)
					val = "AT {0} {1} {2} {3} {4}".format(self.name, tt, x[1], x[2], x[3])
					self.data[x[1]] = val
					writer.write(val.encode())
					e = await self.client_message(val)
					for port in e[1]:
						try: 
							loop = asyncio.get_event_loop()
							transport, protocol = await loop.create_connection(Client, config.SERVER_HOST, port)
							transport.write(e[0].encode())
							nam = await self.validName(port)
							logging.debug("Sending AT to".format(nam))
							transport.close()
						except ConnectionRefusedError:
							nam = await self.validName(port)
							logging.debug("Server {0} not set up yet".format(nam))

					logging.debug("Command Produced: {0}".format(val))
				else:
					m = command.split()
					message = "{0} {1} {2} {3} {4} {5}".format(m[0], m[1], m[2], m[3], m[4], m[5])
					self.data[x[3]] = message
					logging.debug("Got AT {0} from {1}".format(message, m[1]))
					e = await self.client_message(command)
					for port in e[1]:
						try: 
							loop = asyncio.get_event_loop()
							# c = loop.create_connection()
							transport, protocol = await loop.create_connection(Client, config.SERVER_HOST, port)
							transport.write(e[0].encode())
							nam = await self.validName(port)
							logging.debug("Sending AT to".format(nam))
							#print(e[0])
							transport.close()
						except ConnectionRefusedError:
							nam = await self.validName(port)
							logging.debug("Server {0} not set up yet".format(nam))
					#print(message)
			logging.debug("End of Client call")
			await writer.drain()
			writer.write_eof()


	async def getLatLong(self, geo_string):
		lat = ''
		lon = ''
		sec = False
		first = False
		for c in geo_string:
			if (c == '+' or c == '-') and first:
				sec = True
			elif c == '+' or c == '-':
				first = True
			elif sec:
				lon += c
			else:
				lat += c
		return [lat, lon]

	async def isValid(self, command):
		if command == '':
			return False
		x = command.split()
		if len(x) == 0:
			return False

		if x[0] == 'WHATSAT':
			if len(x) != 4:
				return False
			else: 
				try:
					x_2 = int(x[2])
					x_3 = int(x[3])
					if x_2 > 50 or x_2 < 0:
						return False
					elif x_3 > 20 or x_3 < 0:
						return False
					return True
				except ValueError:
					return False
		elif x[0] == 'IAMAT':
			if len(x) != 4:
				return False
			geo_string = await self.getLatLong(x[2])
			try:
				lat = float(geo_string[0])
				lon = float(geo_string[1])
				if lat > 90 or lat < -90: return False
				if lon > 180 or lon < -180: return False
				float(x[3])
				return True
			except ValueError:
				return False
		elif x[0] == 'AT':
			return True
		elif x[0] == 'GET':
			return True
		else:
			return False

	async def client_message(self, message):
		x = message.split()
		ports = []
		c_Wilkes = False
		c_Hands = False
		c_Holiday = False
		c_Goloman = False
		c_Welsh = False
		i = 6
		name = self.name
		if name == 'Goloman':
			while i < len(x):
				if x[i] == 'Hands':
					c_Hands = True
				if x[i] == 'Holiday':
					c_Holiday = True
				if x[i] == 'Wilkes':
					c_Wilkes = True
				i = i + 1

			if not c_Hands:
				ports.append(config.HANDS_P)
			if not c_Holiday:
				ports.append(config.HOLIDAY_P)
			if not c_Wilkes:
				ports.append(config.WILKES_P)	
			message += ' Goloman'
		elif name == 'Hands':
			while i < len(x):
				if x[i] == 'Wilkes':
					c_Wilkes = True
				if x[i] == 'Goloman':
					c_Goloman = True
				i = i+1

			if not c_Wilkes:
				ports.append(config.WILKES_P)
			if not c_Goloman:
				ports.append(config.GOLOMAN_P)

			message+=' Hands'
		elif name == 'Holiday':
			while i < len(x):
				if x[i] == 'Welsh':
					c_Welsh = True
				if x[i] == 'Wilkes':
					c_Wilkes = True
				if x[i] == 'Goloman':
					c_Goloman = True
				i = i + 1
			if not c_Wilkes:
				ports.append(config.WILKES_P)
			if not c_Goloman:
				ports.append(config.GOLOMAN_P)
			if not c_Welsh:
				ports.append(config.WELSH_P)
			message+=' Holiday'
		elif name == 'Wilkes':
			while i < len(x):
				if x[i] == 'Hands':
					c_Hands = True
				if x[i] == 'Holiday':
					c_Holiday = True
				if x[i] == 'Goloman':
					c_Goloman = True
				i = i + 1

			if not c_Hands:
				ports.append(config.HANDS_P)
			if not c_Holiday:
				ports.append(config.HOLIDAY_P)
			if not c_Goloman:
				ports.append(config.GOLOMAN_P)

			message+=' Wilkes'
		elif name == 'Welsh':
			while i < len(x):
				if x[i] == 'Hands':
					c_Hands = True
				i = i+1
			if not c_Hands:
				ports.append(config.HANDS_P)
			message+=' Welsh'

		return [message, ports]

	async def validName(self, n):
		if n == config.GOLOMAN_P:
	 		return 'Goloman'
		elif n == config.HANDS_P:
	 		return 'Hands' 
		elif n == config.HOLIDAY_P:
	 		return 'Holiday'
		elif n == config.WILKES_P:
	 		return 'Wilkes' 
		elif n == config.WELSH_P:
	 		return 'Welsh'
		else: return ""

	async def fetch(self, client, url):
		async with client.get(url) as response:
			return await response.json()

class Client(asyncio.Protocol):
	def connection_made(self, transport):
		self.transport = transport

	def data_receieved(self, data):
		self.transport.write(data)
		self.transport.close()

	def shutdown(self, *args):
		self.transport.close()
		loop.stop()
