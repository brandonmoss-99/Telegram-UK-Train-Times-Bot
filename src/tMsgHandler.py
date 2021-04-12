from tMsgText import tMsgText

class tMsgHandler:
	def __init__(self, token, rData, tMsgSender):
		self.token = token
		self.rData = rData
		self.tMsgSender = tMsgSender

	def handleMessage(self, message):
		if 'text' in message['message']:
			newMessage = tMsgText(message['message'], self.rData, self.tMsgSender)