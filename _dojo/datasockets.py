
import struct
import SocketServer
from base64 import b64encode
from hashlib import sha1
from mimetools import Message
from StringIO import StringIO

import tornado
import tornado.websocket

cl = []

class Datasockets(tornado.websocket.WebSocketHandler):

  def initialize(self, logic):
    '''
    '''
    self.__logic = logic

  def open(self):
    '''
    '''
    if self not in cl:
      cl.append(self)

  def on_close(self):
    '''
    '''
    if self in cl:
      cl.remove(self)

  def on_message(self, message):
    '''
    '''
    print message

  def send(self, message):
    '''
    '''
    for c in cl:
      c.write_message(message)