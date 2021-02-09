from zeep import Client
from zeep import xsd
from zeep.plugins import HistoryPlugin
import time, sys, getopt, requests, json, urllib, re, random

def fetchTrains(stationToCheck, railtoken, numberNextTrains):
	# current WSDL version. Available from 
	# https://lite.realtime.nationalrail.co.uk/OpenLDBWS/
	WSDL = ('https://lite.realtime.nationalrail.co.uk/'
		'OpenLDBWS/wsdl.aspx?ver=2017-10-01')

	history = HistoryPlugin()

	client = Client(wsdl=WSDL, plugins=[history])

	header = xsd.Element(
		'{http://thalesgroup.com/RTTI/2013-11-28/Token/types}AccessToken',
		xsd.ComplexType([
			xsd.Element(
				'{http://thalesgroup.com/'
				'RTTI/2013-11-28/Token/types}TokenValue',
				xsd.String()),
		])
	)
	header_value = header(TokenValue=railtoken)

	# attempt connection to the API, return the API response on success,
	# otherwise return an error message
	try:
		res = (client.service.GetDepBoardWithDetails(
			numRows=numberNextTrains,
			crs=stationToCheck, _soapheaders=[header_value]))
		return [True, res]
	except:
		return [False, []]

def returnTrains(stationToCheck, railtoken):
	# if data isn't classed as 'stale' yet
	if stationToCheck in stationData and time.time() - stationData[stationToCheck]['lastUpdated'] < staleThreshold:
		# return data from the dictionary instead of fetching again from API
		return [True, stationData[stationToCheck]['data']]
	else:
		# not found in dictionary/stale, go fetch from API and update dictionary, returning that
		fetchRequest = fetchTrains(stationToCheck, railtoken, numberNextTrains)
		if fetchRequest[0]:
			stationData[stationToCheck] = {'lastUpdated':time.time(), 'data':fetchRequest[1]}
			return [True, stationData[stationToCheck]['data']]
		else:
			return [False, "Invalid Code!"]

def getHelp():
	# print help information, then quit
	print("\nList of options:\n\n"+
		"(t)oken to use for telegram bot API [token]\n"+
		"Token to use for Network (r)ail API [token]\n"+
		"max (n)umber of next trains to fetch [1-10], default=5\n"+
		"\nExample of usage:\n\n"+
		"bot.py -r aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee -t 123456:123456754g -n 10\n"+
		"Gets up to 10 trains for given station")
	sys.exit(0)

# handles fetching of messages, returning basic message info
class messageFetcher:
	def __init__(self, token, pollTimeout=20):
		self.token = token
		self.pollTimeout = pollTimeout
		self.messages = None
		self.messagesParsed = None

	# get new messages, pass in offset of last message to fetch only new ones
	# and mark to telegram servers it can remove messages older than that
	def fetchMessages(self):
		# get updates via long polling (sends HTTPS request, won't hear anything back from API server)
		# until there is a new update to send back, may hang here for a while
		# define which updates want telegram to send us, ignore every other update type
		updatesToFetch = '["message", "callback_query"]'
		updateRequest = sendRequest(["getUpdates", "offset", msgOffset, "timeout", self.pollTimeout, "allowed_updates", updatesToFetch])
		if updateRequest[0] == True:
			self.messagesParsed = json.loads(updateRequest[2])
			return True
		else:
			print("timestamp:", int(time.time()), "Failed to fetch new messages!", updateRequest[2])
			return False

	# loop through each parsed message stored in the messageFetcher
	def printAllMessages(self):
		for i in range(0, len(self.messagesParsed['result'])):
			print(self.messagesParsed['result'][i],'\n\n')

	def getMessagesLength(self):
		return len(self.messagesParsed['result'])

	# return all messages stored in class
	def getMessages(self):
		return self.messagesParsed

	# return specific message stored in class by position
	def getMessage(self, pos):
		return self.messagesParsed['result'][pos]

	# print specific message stored in class by position
	def printMessage(self, pos):
		print(self.messagesParsed['result'][pos])


class messageHandler:
	def __init__(self, token):
		self.token = token

	def handleMessage(self, message):
		if 'text' in message['message']:
			newMessage = message_new_text(message['message'])


class message_new_text:
	def __init__(self, message):
		self.message = message
		self.getInfo()

		# if message isn't "/start" from new telegram convo
		if self.message['text'] != "/start":
			# check the text passed in is valid
			textParse = parseText(self.message['text'])
			if textParse[0] == True:
				# if valid, get train info for that train code
				trainInfo = returnTrains(textParse[1], railtoken)
				self.reply(trainInfo)
			else:
				# if not valid, reply with returned info
				self.reply(textParse)
		else:
			# what to say when a new person talks to the bot
			newTextMessageRequest = sendRequest(["sendMessage", "chat_id", self.chat['id'], "text", "Hi! Please send a 3 character station code to get started!"])

	def getInfo(self):
		# extract always included message data
		self.message_id = self.message['message_id']
		self.date = self.message['date']
		self.chat = self.message['chat']
		# include optional message data
		self.isfrom = self.message['from']

	def reply(self, data):
		# if succeeded in fetching data for valid station code, reply with info
		if data[0] == True:
			# if there's no station info to optionally show
			if 'nrccMessages' not in data[1] or data[1]['nrccMessages'] is None:
				verifyPrompt = json.dumps({
				"inline_keyboard":[[{"text": "Refresh", "callback_data": self.message['text']+"Refresh"}]]})
			else:
				verifyPrompt = json.dumps({
				"inline_keyboard":[[{"text": "Refresh", "callback_data": self.message['text']+"Refresh"}, {"text": "See Station Notices", "callback_data": self.message['text']+"Notices"}]]})

			newTextMessageRequest = sendRequest(["sendMessage", "chat_id", self.chat['id'], "text", parseResponseTimes(data), "parse_mode", "HTML", "reply_markup", verifyPrompt])

		else:
			newTextMessageRequest = sendRequest(["sendMessage", "chat_id", self.chat['id'], "text", "Failed! " + data[1]])


class callback_queryHandler:
	def __init__(self, token):
		self.token = token

	def handleCallbackQuery(self, message):
		newCallbackQuery = message_new_callback_query(message['callback_query'])


class message_new_callback_query:
	def __init__(self, message):
		self.callbackQuery = message
		self.getInfo()
		self.processQuery()

	def getInfo(self):
		self.query_id = self.callbackQuery['id']
		self.query_from = self.callbackQuery['from']
		self.query_chat_instance = self.callbackQuery['chat_instance']
		self.query_message = self.callbackQuery['message']

		if 'data' in self.callbackQuery:
			self.query_data = self.callbackQuery['data']

	def processQuery(self):

		if self.query_data[3:] == 'Refresh':
			# have to respond with an answerCallbackQuery, otherwise the button stays on loading wheel
			sendRequest(["answerCallbackQuery", "callback_query_id", str(self.query_id) + 'answerSuccess'])
			# edit message for new times
			textParse = parseText(self.query_data[:3])
			if textParse[0]:
				self.reply(returnTrains(textParse[1], railtoken), self.query_data[3:])
			else:
				self.reply(textParse, None)


		elif self.query_data[3:] == 'Notices':
			# have to respond with an answerCallbackQuery, otherwise the button stays on loading wheel
			sendRequest(["answerCallbackQuery", "callback_query_id", str(self.query_id) + 'answerSuccess'])

			textParse = parseText(self.query_data[:3])
			if textParse[0]:
				self.reply(returnTrains(textParse[1], railtoken), self.query_data[3:])
			else:
				self.reply(textParse, None)

		else:
			# have to respond with an answerCallbackQuery, otherwise the button stays on loading wheel
			sendRequest(["answerCallbackQuery", "callback_query_id", str(self.query_id) + 'answerFail'])

	def reply(self, data, queryType):
		if queryType == 'Refresh':
			if data[1]['nrccMessages'] is None:
				verifyPrompt = json.dumps({
				"inline_keyboard":[[{"text": "Refresh", "callback_data": self.query_data[:3]+"Refresh"}]]})
			else:
				verifyPrompt = json.dumps({
				"inline_keyboard":[[{"text": "Refresh", "callback_data": self.query_data[:3]+"Refresh"}, {"text": "See Station Notices", "callback_data": self.query_data[:3]+"Notices"}]]})

			newTextMessageRequest = sendRequest(["editMessageText", "message_id", self.query_message['message_id'], "chat_id", self.query_message['chat']['id'], "text", parseResponseTimes(data), "parse_mode", "HTML", "reply_markup", verifyPrompt])

		elif queryType == 'Notices':
			verifyPrompt = json.dumps({
			"inline_keyboard":[[{"text": "See times", "callback_data": self.query_data[:3]+"Refresh"}]]})

			newTextMessageRequest = sendRequest(["editMessageText", "message_id", self.query_message['message_id'], "chat_id", self.query_message['chat']['id'], "text", parseResponseNotices(data), "parse_mode", "HTML", "reply_markup", verifyPrompt])


def parseResponseTimes(data):
	textResponse = ""

	if data[1] is not None:
		try:
			services = data[1].trainServices.service
		except AttributeError:
			textResponse = "There are no trains currently running at this station!"
			return "<b>Departures from " + data[1].locationName + "</b>%0A--------------------------------%0A" + textResponse
		else:
			try:
				for i in range(0, len(services)):
					destInfo = ""
					platInfo = ""
					callingInfo = ""

					callingPoints = services[i].subsequentCallingPoints.callingPointList

					destInfo += (str(services[i].std) + " to " + str(services[i].destination.location[0].locationName))
					if isinstance(services[i].destination.location[0].via, str):
						destInfo += (" " + str(services[i].destination.location[0].via))
					
					# add train operator to service details
					destInfo += (" (" + str(services[i].operator) + ") ")

					# if the platform number is a string, print it, otherwise just
					# print '-' to represent N/A, unknown or other 
					if isinstance(services[i].platform, str):
						platInfo += ("Plat " + str(services[i].platform) + " ")
					else:
						platInfo += ("Plat - ")
					if services[i].etd != "On time":
						platInfo += ("Exp: ")
					platInfo += str(services[i].etd)

					x = 0
					# if more than 1 station, append each but the last to
					# a string to be wrapped at the end
					if len(callingPoints[0].callingPoint) > 1:
						for x in range(0,
							len(callingPoints[0].callingPoint)-1):
								callingInfo += (str(callingPoints[0].callingPoint[x].
									locationName) + ", ")
					# append the last/only service station to the string
					callingInfo += (str(callingPoints[0].callingPoint[-1].
						locationName) + ".\n")

					serviceDetails = "<b>" + urllib.parse.quote(destInfo) + " - " + urllib.parse.quote(platInfo) + "%0A</b>Calling at: " + urllib.parse.quote(callingInfo)

					textResponse = textResponse + "%0A" + serviceDetails
				
				return "<b>Departures from " + data[1].locationName + "</b>%0A--------------------------------" + textResponse
			except:
				textResponse = "Error parsing data!"


def parseResponseNotices(data):
	textResponse = ""

	if data[1] is not None:
		try:
			messages = data[1].nrccMessages.message

			for message in messages:
				# get the message text
				messageText = message._value_1

				# replace any HTML p tags with newlines, as per OpenLDBWS's
				# guidelines
				for r in (("<P>", "\n"), ("<p>", "\n"), ("</P>", "\n"), 
					("</p>", "\n")):
					# *r means to unpack the contents of r, each list item
					# is sent separately instead of together. i.e:
					# (("<P>", "\n"), ("<p>", "\n")) will be sent as
					# ("<P>", "\n") and then ("<p>", "\n") after, instead
					# of as (("<P>", "\n"), ("<p>", "\n"))
					messageText = messageText.replace(*r)

				# use regex to strip any opening HTML a tags with blanks,
				# as per OpenLDBWS's guidelines
				messageText = re.sub(
					r'<A\s+(?:[^>]*?\s+)?href=(["\'])(.*?)\1>',
					"", messageText)
				messageText = messageText.replace("</A>", "")


				textResponse += urllib.parse.quote(messageText)

			return "<b>Notices at " + data[1].locationName + "</b>%0A--------------------------------" + textResponse
		except:
			return "Error parsing station messages!"


def parseText(text):
		# check if text sent is 3 characters long (rail code length)
		if len(text.strip()) == 3:
			return [True, text.strip().upper()]
		else:
			return [False, "Incorrect format"]
			
		#return [True, text.upper()]


def sendRequest(msgParams):
	# if there's multiple parameters, have to append them correctly
	if len(msgParams) > 0:
		requestString = "https://api.telegram.org/bot"+str(bottoken)+"/"+str(msgParams[0])+"?"
		# skip the 0th item, already appended it to the requestString
		for i in range(1, len(msgParams)-1, 2):
			requestString = requestString + str(msgParams[i]) + "=" + str(msgParams[i+1]) + "&"
		requestString = requestString + str(msgParams[-1])
	else:
		requestString = "https://api.telegram.org/bot"+str(bottoken)+"/"+str(msgParams[0])

	try:
		request = requests.get(requestString)
		# return True/False for a status code of 2XX, the status code itself and the response content
		if request.ok:
			return [True, request.status_code, request.content]
		else:
			return [False, request.status_code, request.content]
	except Exception as e:
		return [False, 0, "Error whilst making the request:", requestString, "\nError:",str(e)]


if __name__ == '__main__':

	railtoken = None # National Rail OpenLDBWS token
	numberNextTrains = 5 # fetch 5 next trains by default
	staleThreshold = 20 # max age of data in seconds to fetch from dictionary instead of re-requesting from API (seconds)
	argv = sys.argv[1:]

	# try getting supported parameters and args from command line
	try:
		opts, args = getopt.getopt(argv, "r:t:n:",
			["railtoken=", "bottoken=", "next=", "help"])
	except:
		print("Error parsing options")
		getHelp()

	# assign variables based on command line parameters and args
	for opt, arg in opts:
		if opt in ['-t', '--bottoken']:
			try:
				# connect to Telegram API with their getMe test method for checking API works
				testResponse = requests.get("https://api.telegram.org/bot%s/getMe" % (str(arg)))
				# set the token to be used if we get a 2xx response code back
				if testResponse.ok:
					bottoken = str(arg)
				else:
					print("Error validating your token!")
					getHelp()
			except:
				print("Error trying to validate your token!")
				getHelp()

		if opt in ['-r', '--railtoken']:
			railtoken = arg

		if opt in ['-n', '--next']:
			try:
				numberNextTrains = int(arg)
			except:
				print("Error converting number of next trains to an integer! Using default of", numberNextTrains)

		if opt in ['--help']:
			getHelp()
	print("--------------------------------------\nProgram started at UNIX time:", int(time.time()), "\n")

	# make sure the no. trains to fetch isn't abusing any OpenLDBWS limits
	if numberNextTrains < 1:
		numberNextTrains = 1
	elif numberNextTrains > 10:
		numberNextTrains = 10

	# make sure a token has been given before doing anything
	if railtoken is not None:
		stationData = {}
		msgOffset = 0
		pollTimeout = 20

		botInfo = json.loads(sendRequest(["getMe"])[2])['result']
		bot_id = botInfo['id']
		bot_username = botInfo['username']
		messageFetcher = messageFetcher(bottoken, pollTimeout)
		messageHandler = messageHandler(bottoken)
		callback_queryHandler = callback_queryHandler(bottoken)

		# loop, run until program is quit
		while True:
			# fetch all the new messages from Telegram servers
			if messageFetcher.fetchMessages() == True:
				# for each message in the list of new messages
				for i in range(messageFetcher.getMessagesLength()):
					# get the message
					msg = messageFetcher.getMessage(i)
					if 'message' in msg:
						# check the message type and hand message off to handler
						messageHandler.handleMessage(msg)
					elif 'callback_query' in msg:
						callback_queryHandler.handleCallbackQuery(msg)

					# update the message offset, so it is 'forgotten' by telegram servers
					# and not returned again on next fetch for new messages, as we've
					# (hopefully) dealt with the message now
					msgOffset = msg['update_id'] + 1
			else:
				# failed to fetch new messages, wait for random number of seconds then try again
				# (may reduce strain on telegram servers when requests are randomly distributed if
				# they go down, instead of happening at fixed rate along with many other bots etc)
				time.sleep(random.randint(20, 60))

	else:
		print("Token wasn't given!")




