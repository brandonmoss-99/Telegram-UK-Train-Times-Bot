import time, logging
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
			logging.info("Returning the train data from the cache")
			return [True, self.stationData[stationToCheck]['data']]
		else:
			# not found in dictionary/stale, go fetch from API and update dictionary, returning that
			logging.info("Cache is stale, fetching new train data from the API")
			fetchRequest = self.rMsgFetcher.fetchTrains(stationToCheck, self.numberNextTrains)
			if fetchRequest[0]:
				self.stationData[stationToCheck] = {'lastUpdated':time.time(), 'data':fetchRequest[1]}
				logging.debug("Updated the cache with the new API data")
				return [True, self.stationData[stationToCheck]['data']]
			else:
				logging.error("Failed to update the cache with the new API data")
				return [False, "Invalid Code!"]