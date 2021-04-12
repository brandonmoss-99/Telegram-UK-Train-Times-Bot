import json
from tMsgSender import tMsgSender
from tMsgTextParser import tMsgTextParser
from rData import rData
from rTimesParser import rTimesParser
from rNoticesParser import rNoticesParser

class tCallbackQuery:
	def __init__(self, message, rData, tMsgSender):
		self.callbackQuery = message
		self.rData = rData
		self.tMsgSender = tMsgSender
		self.rTimesParser = rTimesParser()
		self.rNoticesParser = rNoticesParser()
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
			self.tMsgSender.sendRequest(["answerCallbackQuery", "callback_query_id", str(self.query_id) + 'answerSuccess'])
			# edit message for new times
			textParse = tMsgTextParser().parseText(self.query_data[:3])
			if textParse[0]:
				self.reply(self.rData.getData(textParse[1]), self.query_data[3:])
			else:
				self.reply(textParse, None)


		elif self.query_data[3:] == 'Notices':
			# have to respond with an answerCallbackQuery, otherwise the button stays on loading wheel
			self.tMsgSender.sendRequest(["answerCallbackQuery", "callback_query_id", str(self.query_id) + 'answerSuccess'])

			textParse = tMsgTextParser().parseText(self.query_data[:3])
			if textParse[0]:
				self.reply(self.rData.getData(textParse[1]), self.query_data[3:])
			else:
				self.reply(textParse, None)

		else:
			# have to respond with an answerCallbackQuery, otherwise the button stays on loading wheel
			self.tMsgSender.sendRequest(["answerCallbackQuery", "callback_query_id", str(self.query_id) + 'answerFail'])

	def reply(self, data, queryType):
		if queryType == 'Refresh':
			if data[1]['nrccMessages'] is None:
				verifyPrompt = json.dumps({
				"inline_keyboard":[[{"text": "Refresh", "callback_data": self.query_data[:3]+"Refresh"}]]})
			else:
				verifyPrompt = json.dumps({
				"inline_keyboard":[[{"text": "Refresh", "callback_data": self.query_data[:3]+"Refresh"}, {"text": "See Station Notices", "callback_data": self.query_data[:3]+"Notices"}]]})

			newTextMessageRequest = self.tMsgSender.sendRequest(["editMessageText", "message_id", self.query_message['message_id'], "chat_id", self.query_message['chat']['id'], "text", self.rTimesParser.parseTimes(data), "parse_mode", "HTML", "reply_markup", verifyPrompt])

		elif queryType == 'Notices':
			verifyPrompt = json.dumps({
			"inline_keyboard":[[{"text": "See times", "callback_data": self.query_data[:3]+"Refresh"}]]})

			newTextMessageRequest = self.tMsgSender.sendRequest(["editMessageText", "message_id", self.query_message['message_id'], "chat_id", self.query_message['chat']['id'], "text", self.rNoticesParser.parseNotices(data), "parse_mode", "HTML", "reply_markup", verifyPrompt])
