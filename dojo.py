#!/usr/bin/env python

#
# DOJO Image Server
#

import json
import os
import socket
import sys

from tornado import websocket, web, ioloop

import _dojo

class IndexHandler(web.RequestHandler):
  def get(self):
    self.render("index.html")

class SocketHandler(websocket.WebSocketHandler):

  def open(self):
    if self not in cl:
      cl.append(self)

  def on_close(self):
    if self in cl:
      cl.remove(self)

class ServerLogic:

  def __init__( self ):
    '''
    '''
    pass

  def run( self, mojo_dir ):
    '''
    '''

    #monkey.patch_thread()

    # register two data sources
    self.__segmentation = _dojo.Segmentation(mojo_dir)
    self.__image = _dojo.Image(mojo_dir)

    # and the viewer
    self.__viewer = _dojo.Viewer()

    port = 1337
    port_websocket = 31337
    ip = socket.gethostbyname(socket.gethostname())


    print '*'*80
    print '*', '\033[93m'+'DOJO RUNNING', '\033[0m'
    print '*'
    print '*', 'open', '\033[92m'+'http://' + ip + ':' + str(port) + '/dojo/' + '\033[0m'
    print '*'*80

    app = web.Application([
      # viewer
      (r'/', web.RedirectHandler, {'url':'/dojo/'}),
      (r'/dojo', web.RedirectHandler, {'url':'/dojo/'}),
      (r'/dojo/(.*)', web.StaticFileHandler, {'path': './_web'}),

      # image
      (r'/image/', web.RequestHandler, )

      (r'/ws', SocketHandler)
    ])

    app.listen(port)
    ioloop.IOLoop.instance().start()


    # # start the http server as the main thread
    # http_server = http.HTTPServer(('0.0.0.0', port), self.handle)
    
    # # start the websocket server as a separate process
    # websocket_server = _dojo.websockets.WSServer(('0.0.0.0', port_websocket), _dojo.websockets.Handler)
    # websocket_server_process = Process( target = websocket_server.serve_forever)
    # websocket_server_process.start()
    
    # # start serving HTTP
    # http_server.serve_forever()


  def handle( self, request ):
    '''
    '''
    
    content = None

    if request.find_input_header('upgrade'):
      # special case for websockets
      self.__websockets.handle(request)
      return

    # the access to the viewer
    content, content_type = self.__viewer.handle(request)

    # let the data sources handle the request
    if not content:
      content, content_type = self.__segmentation.handle(request)

    if not content:
      content, content_type = self.__image.handle(request)


    # invalid request
    if not content:
      content = 'Error 404'
      content_type = 'text/html'

    request.add_output_header('Access-Control-Allow-Origin', '*')
    request.add_output_header('Content-Type', content_type)

    request.send_reply(200, "OK", content)

def print_help( scriptName ):
  '''
  '''
  description = ''
  print description
  print
  print 'Usage: ' + scriptName + ' MOJO_DIRECTORY'
  print

#
# entry point
#
if __name__ == "__main__":

  # always show the help if no arguments were specified
  if len( sys.argv ) < 2:
    print_help( sys.argv[0] )
    sys.exit( 1 )

  logic = ServerLogic()
  logic.run( sys.argv[1] )
