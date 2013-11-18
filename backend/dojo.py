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
    self.__segmentation.handle(request)
    self.__image.handle(request)


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
