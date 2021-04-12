from zeep import Client
from zeep import xsd
from zeep.plugins import HistoryPlugin

class rMsgFetcher:
	def __init__(self, token):
		self.token = token

		# current WSDL version. Available from 
		# https://lite.realtime.nationalrail.co.uk/OpenLDBWS/
		self.WSDL = ('https://lite.realtime.nationalrail.co.uk/'
			'OpenLDBWS/wsdl.aspx?ver=2017-10-01')

		self.history = HistoryPlugin()

		self.client = Client(wsdl=self.WSDL, plugins=[self.history])

		self.header = xsd.Element(
			'{http://thalesgroup.com/RTTI/2013-11-28/Token/types}AccessToken',
			xsd.ComplexType([
				xsd.Element(
					'{http://thalesgroup.com/'
					'RTTI/2013-11-28/Token/types}TokenValue',
					xsd.String()),
			])
		)
		self.header_value = self.header(TokenValue=token)


	def fetchTrains(self, stationToCheck, numberNextTrains):
		# attempt connection to the API, return the API response on success,
		# otherwise return an error message
		try:
			res = (self.client.service.GetDepBoardWithDetails(
				numRows=numberNextTrains,
				crs=stationToCheck, _soapheaders=[self.header_value]))
			return [True, res]
		except:
			return [False, []]