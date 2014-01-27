import os
import re
import struct
import StringIO

from base64 import b64encode
from hashlib import sha1

class Websockets(object):

  def __init__(self):
    '''
    '''
    self.__magic = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

    self.__query_viewer_regex = re.compile('^/dojo/.*$')

    self.__clients = {}

  def handshake(self, request):
    '''
    '''
    key = request.find_input_header('sec-websocket-key')
    digest = b64encode(sha1(key + self.__magic).hexdigest().decode('hex'))
    request.add_output_header('Upgrade', 'websocket')
    request.add_output_header('Connection', 'Upgrade')
    request.add_output_header('Access-Control-Allow-Origin', '*')
    request.add_output_header('Sec-WebSocket-Accept', digest)

    request.send_reply(101, "Switching Protocols", '')

    self.__clients[request.remote] = request

    print 'Connected to ', request.remote

  def send(self, request, message):
    '''
    '''
    r = self.__clients[request.remote]

    r.send_reply_chunk(chr(129))
    length = len(message)
    if length <= 125:
        r.send_reply_chunk(chr(length))
    elif length >= 126 and length <= 65535:
        r.send_reply_chunk(126)
        r.send_reply_chunk(struct.pack(">H", length))
    else:
        r.send_reply_chunk(127)
        r.send_reply_chunk(struct.pack(">Q", length))
    r.send_reply_chunk(message)    


    self.__clients[request.remote].send_reply_chunk(message)

    print 'sent'

  def handle(self, request):
    '''
    '''

    if not self.__query_viewer_regex.match(request.uri):
      # this is not a valid request for websockets
      return False

    if not request.remote in self.__clients:
      self.handshake(request)
      self.send(request, 'test2')
    else:
      self.send(request, 'test')

    return True
