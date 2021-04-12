import urllib

class rTimesParser:

	def parseTimes(self, data):
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
					return "Error parsing data!"