from controller import Controller

from SimpleWebSocketServer import WebSocket, SimpleWebSocketServer

class WebSocketHandler(WebSocket):

  controller = Controller()

  def handleMessage(self):
    if self.data is None:
        self.data = ''

    print 'received', self.data

    self.controller.on_message(str(self.data))

  def handleConnected(self):
    print self.address, 'connected' 
    for client in self.server.connections.itervalues():
      if client != self:
        
        try:
          client.sendMessage(str('aaaa'))  
        except Exception as e:
          print e    #self.controller.handshake(self)
      else:
        print 'self'

  def handleClose(self):
    for client in self.server.connections.itervalues():
      if client != self:
        print client, 'closed'

  def send(self, message):
    print 'sending', message
    for client in self.server.connections.itervalues():
      if client != self:
        try:
          client.sendMessage(str(message))  
        except Exception as e:
          print e

