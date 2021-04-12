from tCallbackQuery import tCallbackQuery

class tCallbackHandler:
	def __init__(self, token, rData, tMsgSender):
		self.token = token
		self.rData = rData
		self.tMsgSender = tMsgSender

	def handleCallbackQuery(self, message):
		newCallbackQuery = tCallbackQuery(message['callback_query'], self.rData, self.tMsgSender)