import time, sys, getopt, requests, random
from tMsgSender import tMsgSender
from tMsgFetcher import tMsgFetcher
from rMsgFetcher import rMsgFetcher
from rNoticesParser import rNoticesParser
from tMsgHandler import tMsgHandler
from tCallbackHandler import tCallbackHandler
from tCallbackQuery import tCallbackQuery
from rData import rData


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
			except Exception as ex:
				print("Error trying to validate your token!", ex)
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
		msgOffset = 0
		pollTimeout = 20

		tMsgSender = tMsgSender(bottoken)
		tMsgFetcher = tMsgFetcher(bottoken, pollTimeout)
		rMsgFetcher = rMsgFetcher(railtoken)
		rData = rData(numberNextTrains, rMsgFetcher, staleThreshold)
		tMsgHandler = tMsgHandler(bottoken, rData, tMsgSender)
		tCallbackHandler = tCallbackHandler(bottoken, rData, tMsgSender)

		botInfo = json.loads(tMsgSender.sendRequest(["getMe"])[2])['result']
		bot_id = botInfo['id']
		bot_username = botInfo['username']

		# loop, run until program is quit
		while True:
			# fetch all the new messages from Telegram servers
			if tMsgFetcher.fetchMessages(msgOffset) == True:
				# for each message in the list of new messages
				for i in range(tMsgFetcher.getMessagesLength()):
					# get the message
					msg = tMsgFetcher.getMessage(i)
					if 'message' in msg:
						# check the message type and hand message off to handler
						tMsgHandler.handleMessage(msg)
					elif 'callback_query' in msg:
						tCallbackHandler.handleCallbackQuery(msg)

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