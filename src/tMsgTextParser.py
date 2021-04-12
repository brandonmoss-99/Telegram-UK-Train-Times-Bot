class tMsgTextParser:

	def parseText(self,text):
			# check if text sent is 3 characters long (rail code length)
			if len(text.strip()) == 3:
				return [True, text.strip().upper()]
			else:
				return [False, "Incorrect format"]