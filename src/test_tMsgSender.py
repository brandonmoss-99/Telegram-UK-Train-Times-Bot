import unittest
from tMsgSender import tMsgSender

class testGenerator(unittest.TestCase):
    def setUp(self):
        self.testToken = "1234:abcd"
        self.tMsgSender = tMsgSender(self.testToken)

    def testGetMeUrlGeneration(self):
        self.assertEqual("https://api.telegram.org/bot1234:abcd/getMe", self.tMsgSender.generateRequest(["getMe"]))

    def testUrlGeneration(self):
        self.assertEqual("https://api.telegram.org/bot1234:abcd/sendMessage?chat_id=123456789", self.tMsgSender.generateRequest(["sendMessage", "chat_id", 123456789]))

    def testUrlMultiGeneration(self):
        self.assertEqual("https://api.telegram.org/bot1234:abcd/sendMessage?chat_id=123456789&text=testMessage", self.tMsgSender.generateRequest(["sendMessage", "chat_id", 123456789, "text", "testMessage"]))
