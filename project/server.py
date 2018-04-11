import sys
import asyncio
from serverhelper import Server
import config

def main():
	if len(sys.argv) == 1:
		print('Server.py takes one argument')
		exit(0)
	startServer(sys.argv[1])

def startServer(name):
	port = validName(name)
	if port != -1: 
		server = Server(name, port)
		loop = asyncio.get_event_loop()
		c = asyncio.start_server(server.client_read, config.SERVER_HOST, port, loop=loop)
		server = loop.run_until_complete(c)
		print('Running', name)
		try:
			loop.run_forever()
		except KeyboardInterrupt:
			pass
		server.close()
		loop.run_until_complete(server.wait_closed())
		loop.close()
	else:
		print("Server name not valid")
		exit(0)

def validName(name):
	 	if name == 'Goloman':
	 		return config.GOLOMAN_P
	 	elif name == 'Hands':
	 		return config.HANDS_P 
	 	elif name == 'Holiday':
	 		return config.HOLIDAY_P
	 	elif name == 'Wilkes':
	 		return config.WILKES_P 
	 	elif name == 'Welsh':
	 		return config.WELSH_P
	 	else: return -1

if __name__ == '__main__':
	main()