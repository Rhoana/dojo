#!/usr/bin/env python

#
# DOJO Image Server
#

import json
import os
import socket
import sys
import tornado
import tornado.websocket
import tempfile

import _dojo

#
# websocket handler
#
class SocketHandler(tornado.websocket.WebSocketHandler):

  def open(self):
    if self not in cl:
      cl.append(self)

  def on_close(self):
    if self in cl:
      cl.remove(self)

#
# default handler
#
class DojoHandler(tornado.web.RequestHandler):

  def initialize(self, logic):
    self.__logic = logic

  def get(self, uri):
    '''
    '''
    self.__logic.handle(self)





class ServerLogic:

  def __init__( self ):
    '''
    '''
    pass

  def run( self, mojo_dir, out_dir, port ):
    '''
    '''

    #monkey.patch_thread()

    # create temp folder
    tmpdir = tempfile.mkdtemp()

    # register two data sources
    self.__segmentation = _dojo.Segmentation(mojo_dir, tmpdir)
    self.__image = _dojo.Image(mojo_dir, tmpdir)

    # and the viewer
    self.__viewer = _dojo.Viewer()

    # and the controller
    self.__controller = _dojo.Controller(mojo_dir, out_dir, tmpdir, self.__segmentation.get_database())

    ip = socket.gethostbyname(socket.gethostname())


    print '*'*80
    print '*', '\033[93m'+'DOJO RUNNING', '\033[0m'
    print '*'
    print '*', 'open', '\033[92m'+'http://' + ip + ':' + str(port) + '/dojo/' + '\033[0m'
    print '*'*80

    dojo = tornado.web.Application([
      # viewer
      # (r'/', web.RedirectHandler, {'url':'/dojo/'}),
      # (r'/dojo', web.RedirectHandler, {'url':'/dojo/'}),


      # # image
      # (r'/image/(.*)', _dojo.Image(mojo_dir)),
      (r'/ws', _dojo.Websockets, dict(controller=self.__controller)),
      (r'/(.*)', DojoHandler, dict(logic=self))
  
    ])

    dojo.listen(port)
    tornado.ioloop.IOLoop.instance().start()


  def handle( self, r ):
    '''
    '''
    
    content = None

    # if request.find_input_header('upgrade'):
    #   # special case for websockets
    #   self.__websockets.handle(request)
    #   return

    # the access to the viewer
    content, content_type = self.__viewer.handle(r.request)

    # let the data sources handle the request
    if not content:
      content, content_type = self.__segmentation.handle(r.request)

    if not content:
      content, content_type = self.__image.handle(r.request)


    # invalid request
    if not content:
      content = 'Error 404'
      content_type = 'text/html'

    r.set_header('Access-Control-Allow-Origin', '*')
    r.set_header('Content-Type', content_type)
    r.write(content)
    

def print_help( scriptName ):
  '''
  '''
  description = ''
  print description
  print
  print 'Usage: ' + scriptName + ' MOJO_DIRECTORY OUTPUT_DIRECTORY PORT'
  print

#
# entry point
#
if __name__ == "__main__":

  # always show the help if no arguments were specified
  if len( sys.argv ) < 4:
    print_help( sys.argv[0] )
    sys.exit( 1 )

  logic = ServerLogic()
  logic.run( sys.argv[1], sys.argv[2], sys.argv[3] )
