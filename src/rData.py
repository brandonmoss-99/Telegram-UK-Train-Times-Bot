import time
from rMsgFetcher import rMsgFetcher

class rData:

	def __init__(self, numberNextTrains, rMsgFetcher, staleThreshold):
		# dictionary to hold rail data
		self.stationData = {}
		self.numberNextTrains = numberNextTrains
		self.rMsgFetcher = rMsgFetcher
		self.staleThreshold = staleThreshold

	def getData(self, stationToCheck):
		# if data isn't classed as 'stale' yet
		if stationToCheck in self.stationData and time.time() - self.stationData[stationToCheck]['lastUpdated'] < self.staleThreshold:
			# return data from the dictionary instead of fetching again from API
			return [True, self.stationData[stationToCheck]['data']]
		else:
			# not found in dictionary/stale, go fetch from API and update dictionary, returning that
			fetchRequest = self.rMsgFetcher.fetchTrains(stationToCheck, self.numberNextTrains)
			if fetchRequest[0]:
				self.stationData[stationToCheck] = {'lastUpdated':time.time(), 'data':fetchRequest[1]}
				return [True, self.stationData[stationToCheck]['data']]
			else:
				return [False, "Invalid Code!"]