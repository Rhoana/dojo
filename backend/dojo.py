#!/usr/bin/env python

#
# DOJO Image Server
#

import json
import os
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

    print 'Serving on 1337'
    http.HTTPServer(('0.0.0.0', 1337), self.handle).serve_forever()

  def handle( self, request ):
    '''
    '''
    # let the data sources handle the request
    content, content_type = self.__segmentation.handle(request)

    if not content:
      content, content_type = self.__image.handle(request)

    if not content:
      content = 'Error 404'

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
