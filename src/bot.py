import time, sys, getopt, requests, json, random, logging
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
	# Create the logger to use
	logging.basicConfig(format='%(asctime)s %(levelname)s - %(message)s', level=logging.INFO)
	
	railtoken = None # National Rail OpenLDBWS token
	numberNextTrains = 5 # fetch 5 next trains by default
	staleThreshold = 20 # max age of data in seconds to fetch from dictionary instead of re-requesting from API (seconds)
	logging.debug(f"Set initial default value for the number of trains to fetch to {numberNextTrains}\n and the max age of the cache to {staleThreshold} seconds")
	argv = sys.argv[1:]

	# try getting supported parameters and args from command line
	try:
		logging.debug("Trying to parse the given arguments")
		opts, args = getopt.getopt(argv, "r:t:n:",
			["railtoken=", "bottoken=", "next=", "help"])
	except:
		logging.error("Failed to parse the given arguments")
		getHelp()

	# assign variables based on command line parameters and args
	for opt, arg in opts:
		if opt in ['-t', '--bottoken']:
			try:
				logging.debug("Attempting to validate the provided Telegram bot token")
				# connect to Telegram API with their getMe test method for checking API works
				testResponse = requests.get("https://api.telegram.org/bot%s/getMe" % (str(arg)))
				# set the token to be used if we get a 2xx response code back
				if testResponse.ok:
					logging.info("Provided Telegram token was validated successfully")
					bottoken = str(arg)
				else:
					logging.error("Telegram bot token validation failed")
					getHelp()
			except Exception as ex:
				logging.error(f"There was an error trying to validate the Telegram bot token {ex}")
				getHelp()

		if opt in ['-r', '--railtoken']:
			railtoken = arg

		if opt in ['-n', '--next']:
			try:
				logging.debug("Attempting to set the max number of the next trains to fetch")
				numberNextTrains = int(arg)
				logging.info(f"Successfully set the max number of next trains to fetch to {numberNextTrains}")
			except:
				logging.warning(f"Failed to convert the given number of next trains to fetch. Using default of {numberNextTrains}")

		if opt in ['--help']:
			getHelp()

	logging.info(f"Initial configuration finished")

	# make sure the no. trains to fetch isn't abusing any OpenLDBWS limits
	if numberNextTrains < 1:
		numberNextTrains = 1
	elif numberNextTrains > 10:
		numberNextTrains = 10

	# make sure a token has been given before doing anything
	logging.debug("Checking rail API token has been provided")
	if railtoken is not None:
		logging.debug("Rail API token has been provided")
		msgOffset = 0
		pollTimeout = 20

		tMsgSender = tMsgSender(bottoken)
		tMsgFetcher = tMsgFetcher(bottoken, pollTimeout)
		rMsgFetcher = rMsgFetcher(railtoken)
		rData = rData(numberNextTrains, rMsgFetcher, staleThreshold)
		tMsgHandler = tMsgHandler(bottoken, rData, tMsgSender)
		tCallbackHandler = tCallbackHandler(bottoken, rData, tMsgSender)

		logging.debug("Getting bot information from Telegram")
		botInfo = json.loads(tMsgSender.sendRequest(["getMe"])[2])['result']
		bot_id = botInfo['id']
		bot_username = botInfo['username']
		logging.info(f"Connected to Telegram bot {bot_username} with ID {bot_id}")

		logging.info("Configuration finished. Program is now running")
		# loop, run until program is quit
		while True:
			# fetch all the new messages from Telegram servers
			logging.debug("Attempting to fetch any new messages from Telegram")
			if tMsgFetcher.fetchMessages(msgOffset) == True:
				# for each message in the list of new messages
				for i in range(tMsgFetcher.getMessagesLength()):
					# get the message, check its type and hand it off to handler
					msg = tMsgFetcher.getMessage(i)
					if 'message' in msg:
						logging.debug("Handling new Telegram message")
						tMsgHandler.handleMessage(msg)
					elif 'callback_query' in msg:
						logging.debug("Handling new Telegram Callback Query")
						tCallbackHandler.handleCallbackQuery(msg)

					# update the message offset, so it is 'forgotten' by telegram servers
					# and not returned again on next fetch for new messages, as we've
					# (hopefully) dealt with the message now
					msgOffset = msg['update_id'] + 1
					logging.debug(f"Set Telegram message offset to {msgOffset}")
			else:
				# failed to fetch new messages, wait for random number of seconds then try again
				# (may reduce strain on telegram servers when requests are randomly distributed if
				# they go down, instead of happening at fixed rate along with many other bots etc)
				sleepTime = random.randint(20, 60)
				logging.warning(f"Failed to fetch new messages from Telegram. Sleeping for {sleepTime} seconds")
				time.sleep(sleepTime)
	else:
		logging.error("Rail API token wasn't given")
