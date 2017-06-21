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

from twisted.internet.protocol import Protocol
from twisted.internet.defer import Deferred, succeed

from definitions import *
from utils import IdGenerator
from messages import decodeLength, \
                     Connect, \
                     Connack, \
                     Subscribe, \
                     Suback, \
                     Publish

class MQTTProtocol(Protocol):
    worker = None

    IDLE        = 0
    CONNECTING  = 1
    CONNECTED   = 2

    def __init__(self):
        self._buffer = bytearray()
        self.state = self.IDLE

        self.idGenerator = IdGenerator()

    def connect(self, worker):
        print("INFO: Connecting Protocol")

        self.worker = worker
        self.state = self.CONNECTING

        msg = Connect(self.worker.clientId,
                      self.worker.version,
                      username=self.worker.username,
                      password=self.worker.appKey)

        self.transport.write(msg.pack())

    def joined(self):
        d = self.worker.joined()

    def dataReceived(self, data):
        print("************ Data Received ***************", data)
        self._buffer.extend(data)

        length = None

        while len(self._buffer):
            if length is None:
                # Start on a new packet

                # Haven't got enough data to start a new packet, wait for some more
                if len(self._buffer) < 2:
                    break

                lenLen = 1
                # Calculate the length of the length field
                while lenLen < len(self._buffer):
                    if not self._buffer[lenLen] & 0x80:
                        break
                    lenLen += 1

                # We still haven't got all of the remaining length field
                if lenLen < len(self._buffer) and self._buffer[lenLen] & 0x80:
                    return

                length = decodeLength(self._buffer[1:])

            if len(self._buffer) >= length + lenLen + 1:
                chunk = self._buffer[:length + lenLen + 1]
                self._processPacket(chunk)
                self._buffer = self._buffer[length + lenLen + 1:]
                length = None

            else:
                break

    def _processPacket(self, packet):
        """
        Generic MQTT packet decoder
        """
        packet_type = (packet[0] & 0xF0) >> 4
        packet_flags = (packet[0] & 0x0F)

        if packet_type == CONNECT:
            self._handleConnect(packet)
        elif packet_type == CONNACK:
            self._handleConnack(packet)
        elif packet_type == PUBLISH:
            self._handlePublish(packet)
        elif packet_type == PUBACK:
            self._handlePuback(packet)
        elif packet_type == PUBREC:
            self._handlePubrec(packet)
        elif packet_type == PUBREL:
            self._handlePubrel(packet)
        elif packet_type == PUBCOMP:
            self._handlePubcomp(packet)
        elif packet_type == SUBSCRIBE:
            self._handleSubscribe(packet)
        elif packet_type == SUBACK:
            self._handleSuback(packet)
        elif packet_type == UNSUBSCRIBE:
            self._handleUnsubscribe(packet)
        elif packet_type == UNSUBACK:
            self._handleUnsuback(packet)
        elif packet_type == PINGREQ:
            self._handlePingreq(packet)
        elif packet_type == PINGRESP:
            self._handlePingresp(packet)
        elif packet_type == DISCONNECT:
            self._handleDisconnect(packet)
        else:
            print("ERROR: Invalid Packet Type: %s -- Aborting Connection" %(packet_type))
            self.transport.abortConnection()

    def _handleConnect(self, packet):
        print("DEBUG: Received CONNECT")

    def _handleConnack(self, packet):
        print("DEBUG: Received CONNACK")
        res = Connack.unpack(packet)
        if res.resultCode == 0:
            self.state = self.CONNECTED
            # XXX To Do implement keepAlive
            self.joined()
        else:
            self.state = self.IDLE
            print("ERROR: Connection Refused -- Aborting Connection")
            self.transport.abortConnection()

    def _handlePublish(self, packet):
        print("DEBUG: Received PUBLISH")
        res = Publish.unpack(packet)
        func = self.worker.getTopic(res.topic)
        if func:
            func(res.payload)

    def _handlePuback(self, packet):
        print("DEBUG: Received PUBACK")

    def _handlePubrec(self, packet):
        print("DEBUG: Received PUBREC")

    def _handlePubrel(self, packet):
        print("DEBUG: Received PUBREL")

    def _handlePubcomp(self, packet):
        print("DEBUG: Received PUBCOMP")

    def _handleSubscribe(self, packet):
        print("DEBUG: Received SUBSCRIBE")

    def _handleSuback(self, packet):
        print("DEBUG: Received SUBACK")
        res = Suback.unpack(packet)
        d = self.worker.getSubscribeRequest(res._id, remove=True)
        if d:
            d.callback(res.subscribed)

    def _handleUnsubscribe(self, packet):
        print("DEBUG: Received UNSUBSCRIBE")

    def _handleUnsuback(self, packet):
        print("DEBUG: Received UNSUBACK")

    def _handlePingreq(self, packet):
        print("DEBUG: Received PINGREQ")

    def _handlePingresp(self, packet):
        print("DEBUG: Received PINGRESP")

    def _handleDisconnect(self, packet):
        print("DEBUG: Received DISCONNECT")

    def subscribe(self, topic, function, qos=0):
        print("DEBUG: Subscribing to topic %s"%(topic))

        # XXX Check if number of in fligth suscribe is not > than window
        # if len(self.factory.windowSubscribe[self.addr]) == self._window:
        #     raise MQTTWindowError("subscription requests exceeded limit", self._window)

        if not ( 0<= qos < 3):
            raise Exception("Invalid QOS")

        # XXX To do Add time out check.
        _id = self.idGenerator.next()
        msg = Subscribe(_id=_id, topics=[(topic, qos)])
        d = Deferred()

        self.worker.addSubscribeRequest(msg, d)
        self.worker.addTopic(topic, function)
        self.transport.write(msg.pack())

        return d

    def publish(self, topic, message, qos=0, retain=False):

        if not ( 0<= qos < 3):
            raise Exception("Invalid QOS")

        _id = self.idGenerator.next()
        msg = Publish(_id=_id, topic=topic, payload=message, qos=qos, retain=retain, dup=False)

        if msg.qos == QOS_0:
            d = succeed(None)
        else:
            d = Deferred()
            # XXX To DO: Add timer to check timeout
            self.worker.addPublishRequest(msg, d)

        self.transport.write(msg.pack())
        return d
