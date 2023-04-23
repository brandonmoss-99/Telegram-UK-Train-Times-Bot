import json, logging
from tMsgSender import tMsgSender
from tMsgTextParser import tMsgTextParser
from rData import rData
from rTimesParser import rTimesParser

class tMsgText:
	def __init__(self, message, rData, tMsgSender):
		self.message = message
		self.getInfo()
		self.tMsgTextParser = tMsgTextParser()
		self.rTimesParser = rTimesParser()
		self.tMsgSender = tMsgSender
		# rData object from main file,
		# makes sure data is accessible
		self.rData = rData

		# if message isn't "/start" from new telegram convo
		if self.message['text'] != "/start":
			# check the text passed in is valid
			textParse = self.tMsgTextParser.parseText(self.message['text'])
			if textParse[0] == True:
				# if valid, get train info for that train code
				logging.info(f"Telegram id {self.chat['id']} sent \"{self.message['text']}\"")
				trainInfo = self.rData.getData(textParse[1])
				self.reply(trainInfo)
			else:
				# if not valid, reply with returned info
				self.reply(textParse)
		else:
			# what to say when a new person talks to the bot
			logging.info(f"Telegram id {self.chat['id']} sent /start, sending initial msg")
			newTextMessageRequest = self.tMsgSender.sendRequest(["sendMessage", "chat_id", self.chat['id'], "text", "Hi! Please send a 3 character station code to get started!"])

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

			newTextMessageRequest = self.tMsgSender.sendRequest(["sendMessage", "chat_id", self.chat['id'], "text", self.rTimesParser.parseTimes(data), "parse_mode", "HTML", "reply_markup", verifyPrompt])

		else:
			newTextMessageRequest = self.tMsgSender.sendRequest(["sendMessage", "chat_id", self.chat['id'], "text", "Failed! " + data[1]])