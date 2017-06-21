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

import struct

from definitions import *

__all__ = ( "Connect", "Connack", "Publish", "Puback", "Pubrec", "Pubrel",
            "Pubcomp", "Subscribe", "Suback", "Unsubscribe", "Unsuback",
            "Pingreq", "Pingresp", "Disconnect")

# ---------------------------- Utils Function ----------------------------------
def encodeString(string):
    '''
    Encode an UTF-8 string into MQTT format.
    Returns a string
    '''
    string = string.encode("utf-8")
    return struct.pack(">H", len(string)) + string

def decodeString(encoded):
    '''
    Decodes an UTF-8 string from an encoded MQTT bytearray.
    Returns the decoded string and renaining bytearray to be parsed
    '''
    length = encoded[0]*256 + encoded[1]
    return (encoded[2:2+length].decode('utf-8'), encoded[2+length:])

def encodeLength(value):
    '''
    Encodes value into a multibyte sequence defined by MQTT protocol.
    Used to encode packet length fields.
    '''
    encoded = ""
    while True:
        digit = value % 128
        value //= 128
        if value > 0:
            digit |= 128
        encoded += struct.pack("B", digit)
        if value <= 0:
            break
    return encoded

def decodeLength(encoded):
    '''
    Decodes a variable length value defined in the MQTT protocol.
    This value typically represents remaining field lengths
    '''
    value      = 0
    multiplier = 1
    for i in encoded:
        value += (i & 0x7F) * multiplier
        multiplier *= 0x80
        if (i & 0x80) != 0x80:
            break
    return value

def getLength(packet):
    lenLen = 1
    while packet[lenLen] & 0x80:
        lenLen += 1
    return lenLen

class Connect(object):

    def __init__ (self, clientId, version, keepalive=0, willTopic=None,
                        willMessage=None, willQoS=0, willRetain=False,
                        username=None, password=None, cleanStart=True):

        self.encoded     = None
        self.clientId    = clientId
        self.keepalive   = keepalive
        self.willTopic   = willTopic
        self.willMessage = willMessage
        self.willQoS     = willQoS
        self.willRetain  = willRetain
        self.username    = username
        self.password    = password
        self.cleanStart  = cleanStart
        self.version     = version

    def pack(self):
        header    = struct.pack("B", 0x10)
        varHeader = ""
        payload   = ""

        # ---- Variable header encoding section -----
        varHeader += encodeString(self.version['tag'])
        varHeader += struct.pack("B", self.version['level'])

        flags =  (self.cleanStart << 1)
        if  self.willTopic is not None and self.willMessage is not None:
            flags |= 0x04 | (self.willRetain << 5) | (self.willQoS << 3)
        if self.username is not None:
            flags |= 0x80
        if self.password is not None:
            flags |= 0x40
        varHeader += struct.pack("B", flags)

        varHeader += struct.pack(">H", self.keepalive)

        # ------ Payload encoding section ----
        payload += encodeString(self.clientId)

        if self.willTopic is not None and self.willMessage is not None:
            payload += encodeString(self.willTopic)
            payload += encodeString(self.willMessage)
        if self.username is not None:
            payload += encodeString(self.username)
        if self.password is not None:
            payload += encodeString(self.password)

        # ---- Build the packet once all lengths are known ----
        header += encodeLength(len(varHeader) + len(payload))
        header += varHeader
        header += payload

        self.encoded = header
        return self.encoded

    @classmethod
    def unpack(cls, packet):
        length = getLength(packet)
        packet_remaining = packet[length+1:]

        # Variable Header
        version_str, packet_remaining = decodeString(packet_remaining)
        version_id = int(packet_remaining[0])
        if version_id == VERSION["v31"]['level']:
            version = VERSION["v31"]
        elif version_id == VERSION["v311"]['level']:
            version = VERSION["v311"]
        else:
            print("ERROR: Invalid Version type")

        flags = packet_remaining[1]
        cleanStart = (flags & 0x02) != 0

        willFlag   = (flags & 0x04) != 0
        willQoS    = (flags >> 3) & 0x03 if willFlag else 0
        willRetain = (flags & 0x20) != 0 if willFlag else False

        packet_remaining = packet_remaining[2:]
        keepalive = struct.unpack(">H", packet_remaining[:2])[0]

        # Payload
        packet_remaining = packet_remaining[2:]
        clientId, packet_remaining = decodeString(packet_remaining)

        willTopic = None
        if willFlag:
            willTopic, packet_remaining  = decodeString(packet_remaining)

        willMessage = None
        if willFlag:
            willMessage, packet_remaining = decodeString(packet_remaining)

        userFlag = (flags & 0x80) != 0
        username = None
        if userFlag:
            username, packet_remaining = decodeString(packet_remaining)

        passFlag = (flags & 0x40) != 0
        password = None
        if passFlag:
            l = struct.unpack(">H", packet_remaining[:2])[0]
            password = packet_remaining[2:2+l]

        return cls (clientId, version, keepalive=keepalive, willTopic=willTopic,
                    willMessage=willMessage, willQoS=willQoS, willRetain=willRetain,
                    username=username, password=password, cleanStart=cleanStart)

class Connack(object):

    def __init__(self, session, resultCode):
        self.encoded = None
        self.session = session
        self.resultCode = resultCode

    def pack(self):
        header = struct.pack("B", 0x20)
        varHeader = struct.pack("B", self.session) + struct.pack("B", self.resultCode)

        header += encodeLength(len(varHeader))
        header += varHeader

        self.encoded = header
        return self.encoded

    @classmethod
    def unpack(cls, packet):
        length = getLength(packet)
        packet_remaining = packet[length+1:]

        session = (packet_remaining[0] & 0x01) == 0x01
        resultCode = int(packet_remaining[1])

        return cls (session=session, resultCode=resultCode)

class Publish(object):

    def __init__(self, _id, topic, payload, qos, retain, dup):
        self.encoded = None
        self._id = _id
        self.topic = topic
        self.payload = payload
        self.qos = qos
        self.retain = retain
        self.dup = dup

    def pack(self):
        header    = ""
        varHeader = ""
        payload   = ""

        varHeader += encodeString(self.topic)
        if self.qos > 0:
            qos = 0x30 | self.retain | (self.qos << 1) | (self.dup << 3)
            varHeader += struct.pack(">H", self._id)
        else:
            qos = 0x30 | self.retain

        header += struct.pack("B", qos)
        if isinstance(self.payload, str):
            payload += self.payload
        else:
            print("ERROR: Invalid payload type")

        totalLen = len(varHeader) + len(payload)
        if totalLen > 268435455:
            raise Exception("ERROR PAYLOAD to big")

        header += encodeLength(totalLen)
        header += varHeader
        header += payload
        self.encoded = header

        return self.encoded

    @classmethod
    def unpack(cls, packet):
        length = getLength(packet)
        packet_remaining = packet[length+1:]

        dup = (packet[0] & 0x08) == 0x08
        qos = (packet[0] & 0x06) >> 1
        retain = (packet[0] & 0x01) == 0x01

        topicLen = struct.unpack(">H", packet_remaining[:2])[0]
        topic, packet_remaining = decodeString(packet_remaining)

        if qos:
            _id = struct.unpack(">H", packet_remaining[:2])[0]
            payload = str(packet_remaining[2:])
        else:
            _id = None
            payload = str(packet_remaining[:])

        return cls (_id=_id, topic=topic, payload=payload,
                    qos=qos, retain=retain, dup=dup)

class Puback(object):

    def __init__(self, _id):
        self.encoded = None
        self._id = _id

    def pack(self):
        header = struct.pack("B", 0x40)
        varHeader = struct.pack("B", self._id)

        header += encodeLength(len(varHeader))
        header += varHeader

        self.encoded = header
        return self.encoded

    @classmethod
    def unpack(cls, packet):
        length = getLength(packet)
        packet_remaining = packet[length+1:]

        _id = struct.unpack(">H", packet_remaining[:2])[0]

        return cls (_id=_id)


class Pubrec(object):

    def __init__(self, _id):
        self.encoded = None
        self._id = _id

    def pack(self):
        header = struct.pack("B", 0x50)
        varHeader = struct.pack("B", self._id)

        header += encodeLength(len(varHeader))
        header += varHeader

        self.encoded = header
        return self.encoded

    @classmethod
    def unpack(cls, packet):
        length = getLength(packet)
        packet_remaining = packet[length+1:]

        _id = struct.unpack(">H", packet_remaining[:2])[0]

        return cls (_id=_id)

class Pubrel(object):

    def __init__(self, _id, dup=False):
        self.encoded = None
        self._id = _id
        self.dup = dup

    def pack(self):
        header = struct.pack("B", 0x62) #XXX To Do: packet with QoS=1 Check What happen if not qos = 1
        varHeader = struct.pack("B", self._id)

        header += encodeLength(len(varHeader))
        header += varHeader

        self.encoded = header
        return self.encoded

    @classmethod
    def unpack(cls, packet):
        length = getLength(packet)
        packet_remaining = packet[length+1:]

        _id = struct.unpack(">H", packet_remaining[:2])[0]
        dup = (packet[0] & 0x08) == 0x08

        return cls (_id=_id, dup=dup)

class Pubcomp(object):

    def __init__(self, _id):
        self.encoded = None
        self._id = _id

    def pack(self):
        header = struct.pack("B", 0x72)
        varHeader = struct.pack("B", self._id)

        header += encodeLength(len(varHeader))
        header += varHeader

        self.encoded = header
        return self.encoded

    @classmethod
    def unpack(cls, packet):
        length = getLength(packet)
        packet_remaining = packet[length+1:]

        _id = struct.unpack(">H", packet_remaining[:2])[0]

        return cls (_id=_id)

class Subscribe(object):

    def __init__(self, _id, topics):
        self.encoded = None
        # List of tuples (topic, qos)
        self.topics = topics
        self._id = _id

    def pack(self):
        header    = struct.pack("B", 0x82) #XXX To Do: packet with QoS=1 Check What happen if not qos = 1
        varHeader = struct.pack(">H", self._id)
        payload   = ""

        for topic in self.topics:
            payload += encodeString(topic[0])
            payload += struct.pack("B", topic[1])

        header += (encodeLength(len(varHeader) + len(payload)))
        header += (varHeader)
        header += (payload)
        self.encoded = header

        return self.encoded

    @classmethod
    def unpack(cls, packet):
        length = getLength(packet)
        packet_remaining = packet[length+1:]

        _id = struct.unpack(">H", packet_remaining[:2])[0]
        packet_remaining = packet_remaining[2:]
        topics = []
        while len(packet_remaining):
            topic, packet_remaining = decodeString(packet_remaining)
            qos =  int (packet_remaining[0]) & 0x03
            topics.append( (topic, qos) )
            packet_remaining = packet_remaining[1:]

        return cls (_id=_id, topics=topics)

class Suback(object):

    def __init__(self, _id, subscribed):
        self.encoded = None
        self._id = _id
        # List of tuples (qos, Failure Flag)
        self.subscribed = subscribed

    def pack(self):
        header = struct.pack("B", 0x90)
        varHeader = struct.pack("B", self._id)
        payload = ""

        for code in self.subscribed:
            payload += code[0] | (0x80 if code[1] == True else 0x00)

        header += encodeLength( len(varHeader)+len(payload) )
        header += varHeader
        header += payload

        self.encoded = header
        return self.encoded

    @classmethod
    def unpack(cls, packet):
        length = getLength(packet)
        packet_remaining = packet[length+1:]

        _id = struct.unpack(">H", packet_remaining[:2])[0]
        subscribed = [ (byte & 0x7F, byte & 0x80 == 0x80)
                        for byte in packet_remaining[2:] ]

        return cls (_id=_id, subscribed=subscribed)

class Unsubscribe(object):

    def __init__(self, _id, topics):
        self.encoded = None
        self._id = None
        # List of topics
        self.topics = topics

    def pack(self):
        header    = struct.pack("B", 0xA2) #XXX To Do: packet with QoS=1 Check What happen if not qos = 1
        varHeader = struct.pack(">H", self._id)
        payload   = ""

        for topic in self.topics:
            payload += encodeString(topic)

        header += (encodeLength(len(varHeader) + len(payload)))
        header += (varHeader)
        header += (payload)
        self.encoded = header

        return self.encoded

    @classmethod
    def unpack(cls, packet):
        length = getLength(packet)
        packet_remaining = packet[length+1:]

        _id = struct.unpack(">H", packet_remaining[:2])[0]
        packet_remaining = packet_remaining[2:]
        topics = []
        while len(packet_remaining):
            topic, packet_remaining = decodeString(packet_remaining)
            topics.append(topic)
            packet_remaining = packet_remaining[1:]

        return cls (_id=_id, topics=topics)

class Unsuback(object):

    def __init__(self, _id):
        self.encoded = None
        self._id = _id

    def pack(self):
        header = struct.pack("B", 0xB0)
        varHeader = struct.pack("B", self._id)

        header += encodeLength(len(varHeader))
        header += varHeader

        self.encoded = header
        return self.encoded

    @classmethod
    def unpack(cls, packet):
        length = getLength(packet)
        packet_remaining = packet[length+1:]

        _id = struct.unpack(">H", packet_remaining[:2])[0]

        return cls (_id=_id)

class Pingreq(object):

    def __init__(self, encoded=None):
        self.encoded = None

    def pack(self):
        header = struct.pack("B", 0xC0)

        self.encoded = header
        return self.encoded

    @classmethod
    def unpack(cls, packet):
        return cls (encoded=packet)

class Pingres(object):

    def __init__(self, encoded=None):
        self.encoded = None

    def pack(self):
        header = struct.pack("B", 0xD0)

        self.encoded = header
        return self.encoded

    @classmethod
    def unpack(cls, packet):
        return cls (encoded=packet)

class Disconnect(object):

    def __init__(self, encoded=None):
        self.encoded = encoded

    def pack(self):
        header = struct.pack("B", DISCONNECT)
        self.encoded = header
        return self.encoded

    @classmethod
    def unpack(cls, packet):
        inst = cls(encoded=packet)
        return inst
