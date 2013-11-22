#!/usr/bin/env python

#
# DOJO Image Server
#

import json
import os
import socket
import sys

from gevent import http

import _dojo

class ServerLogic:

  def __init__( self ):
    '''
    '''
    pass

  def run( self, mojo_dir ):
    '''
    '''

    # register two data sources
    self.__segmentation = _dojo.Segmentation(mojo_dir)
    self.__image = _dojo.Image(mojo_dir)

    # and the viewer
    self.__viewer = _dojo.Viewer()

    port = 1337
    ip = socket.gethostbyname(socket.gethostname())


    print '*'*80
    print '*', '\033[93m'+'DOJO RUNNING', '\033[0m'
    print '*'
    print '*', 'open', '\033[92m'+'http://' + ip + ':' + str(port) + '/dojo/' + '\033[0m'
    print '*'*80
    http.HTTPServer(('0.0.0.0', port), self.handle).serve_forever()

  def handle( self, request ):
    '''
    '''

    content = None

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
