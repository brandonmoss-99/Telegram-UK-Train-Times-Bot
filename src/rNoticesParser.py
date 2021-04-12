import re, urllib

class rNoticesParser:
	
	def parseNotices(self, data):
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

				return "<b>Notices at " + data[1].locationName + "</b>%0A--------------------------------%0A" + textResponse
			except:
				return "Error parsing station messages!"