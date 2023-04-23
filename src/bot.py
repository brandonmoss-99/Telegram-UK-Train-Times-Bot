import time, sys, requests, json, random, logging, os
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

	DEFAULT_NEXT_TRAINS = 5
	DEFAULT_STALE_THRESHOLD = 30

	# Values could be of type "None" or str
	bottoken = os.environ.get("T_TOKEN") # Telegram bot API token
	railtoken = os.environ.get("RAIL_TOKEN") # National Rail OpenLDBWS token
	numberNextTrains = os.environ.get("NEXT_TRAINS_COUNT") # Max number of trains to fetch
	staleThreshold = os.environ.get("CACHE_TIME") # Time to cache data before re-requesting from API (secs)

	# Check the variables have been set
	if bottoken != None:
		logging.debug("Attempting to validate the provided Telegram bot token")
		try:
			# connect to Telegram API with their getMe test method for checking API works
			testResponse = requests.get("https://api.telegram.org/bot%s/getMe" % (str(bottoken)))
			# set the token to be used if we get a 2xx response code back
			if testResponse.ok:
				logging.info("Provided Telegram token was validated successfully")
				bottoken = str(bottoken)
			else:
				logging.error("Telegram bot token validation failed")
				getHelp()
		except Exception as ex:
			logging.error(f"There was an error trying to validate the Telegram bot token {ex}")
			getHelp()
	else:
		logging.error("Telegram bot API token is missing")
		getHelp()
	

	if railtoken == None:
		logging.error("Rail API token is missing")
		getHelp()


	if numberNextTrains != None:
		try:
			numberNextTrains = int(numberNextTrains)
			# make sure the no. trains to fetch isn't abusing any OpenLDBWS limits
			if numberNextTrains < 1:
				numberNextTrains = 1
				logging.info(f"Specified next trains value is below min threshold. Set to min of {numberNextTrains}")
			elif numberNextTrains > 10:
				numberNextTrains = 10
				logging.info(f"Specified next trains value exceeds max threshold. Set to max of {numberNextTrains}")
			else:
				logging.info(f"Set number of next trains to {numberNextTrains}")
		except:
			numberNextTrains = DEFAULT_NEXT_TRAINS
			logging.info(f"Set number of next trains to the default value of {numberNextTrains}")
	else:
		# Set a default value
		numberNextTrains = DEFAULT_NEXT_TRAINS
		logging.info(f"Set number of next trains to the default value of {numberNextTrains}")
	

	if staleThreshold != None:
		try:
			staleThreshold = int(staleThreshold)
			logging.info(f"Set the cache time to {staleThreshold} seconds")
		except:
			staleThreshold = DEFAULT_STALE_THRESHOLD
			logging.info(f"Set the cache time to the default {DEFAULT_STALE_THRESHOLD} seconds ")
	else:
		# Set a default value
		staleThreshold = DEFAULT_STALE_THRESHOLD
		logging.info(f"Set the cache time to the default {DEFAULT_STALE_THRESHOLD} seconds ")

	logging.info(f"Initial configuration finished")

	if railtoken is not None and bottoken is not None:
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
