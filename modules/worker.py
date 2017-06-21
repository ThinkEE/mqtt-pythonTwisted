################################################################################
# MIT License
#
# Copyright (c) 2017 Jean-Charles Fosse & Johann Bigler
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
################################################################################

from twisted.internet.defer import inlineCallbacks, returnValue

from twisted.application.internet import ClientService, backoffPolicy
from twisted.internet.endpoints   import clientFromString
from twisted.internet.protocol import Factory

from protocol import MQTTProtocol
from definitions import *

class MQTTWorker(ClientService):

    def __init__(self, reactor, config):

        self.endpoint = clientFromString(reactor, config["endpoint"])
        self.factory = Factory.forProtocol(MQTTProtocol)
        self.version = VERSION[config["version"]]
        self.clientId = config["client_id"]
        self.username = config["username"]
        self.appKey = config["app_key"]

        self.protocol = None

        # In flight subscribe request
        self.subscribe_requests = {}

        # Map topic and related function
        self.topics = {}

        # Map of publish waiting for ack
        self.publish_requests = {}

        ClientService.__init__(self, self.endpoint, self.factory, retryPolicy=backoffPolicy())

    def start(self):
        print("INFO: Starting MQTT Client")

        self.whenConnected().addCallback(self.connected)
        self.startService()

    def connected(self, protocol):
        print("INFO: Client Connected")
        self.protocol = protocol
        protocol.connect(self)

    def joined(self):
        print("INFO: MQTT joined")

    @inlineCallbacks
    def subscribe(self, topic, function, qos=0):
        yield self.protocol.subscribe(topic, function, qos)

    @inlineCallbacks
    def publish(self, topic, message, qos=0):
        yield self.protocol.publish(topic, message, qos)

    def addSubscribeRequest(self, request, d):
        # XXX To Do: Add boolean to know if a timer should be start
        if not request._id in self.subscribe_requests:
            self.subscribe_requests[request._id] = d

    def getSubscribeRequest(self, _id, remove=False):
        res = None
        if _id in self.subscribe_requests:
            res = self.subscribe_requests[_id]
            if remove:
                del self.subscribe_requests[_id]
        return res

    def addTopic(self, topic, function):
        if not topic in self.topics:
            self.topics[topic] = function

    def getTopic(self, topic):
        res = None
        if topic in self.topics:
            res = self.topics[topic]
        return res

    def addPublishRequest(self, request, d):
        # XXX To Do: Add boolean to know if a timer should be start
        if not request._id in self.publish_requests:
            self.publish_requests[request._id] = d

    def getPublishRequest(self, _id, remove=False):
        res = None
        if _id in self.publish_requests:
            res = self.publish_requests[_id]
            if remove:
                del self.publish_requests[_id]
        return res
