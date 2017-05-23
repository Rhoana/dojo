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
import signal

import _dojo

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

  def post(self, uri):
    '''
    '''
    self.__logic.handle(self)



class ServerLogic:

  def __init__( self ):
    '''
    '''
    pass

  def run( self, mojo_dir, out_dir, port, orphan_detection, configured ):
    '''
    '''

    signal.signal(signal.SIGINT, self.close)

    #monkey.patch_thread()

    self.__mojo_dir = mojo_dir
    self.__configured = configured
    self.__out_dir = out_dir

    # create temp folder
    tmpdir = out_dir#tempfile.mkdtemp()
    self.__tmpdir = out_dir#tmpdir

    #
    # since we just have an output dir,
    # create it now
    #

    print 'aaa'
    # register two data sources
    self.__segmentation = _dojo.Segmentation(mojo_dir, tmpdir, out_dir, self)
    self.__image = _dojo.Image(mojo_dir, tmpdir)

    print 'bbb'

    # detect orphans
    if orphan_detection:
      self.__segmentation.detect_orphans()

    print 'after orphan'

    # and the controller
    if self.__segmentation:
      db = self.__segmentation.get_database()

    else:
      db = None
    self.__controller = _dojo.Controller(mojo_dir, out_dir, tmpdir, db, self)

    # and the viewer
    self.__viewer = _dojo.Viewer()

    # and the setup
    self.__setup = _dojo.Setup(self,mojo_dir,tmpdir)

    ip = socket.gethostbyname(socket.gethostname())

    dojo = tornado.web.Application([
      # viewer
      # (r'/', web.RedirectHandler, {'url':'/dojo/'}),
      # (r'/dojo', web.RedirectHandler, {'url':'/dojo/'}),


      # # image
      # (r'/image/(.*)', _dojo.Image(mojo_dir)),
      (r'/ws', _dojo.Websockets, dict(controller=self.__controller)),
      (r'/(.*)', DojoHandler, dict(logic=self))
  
    ])

    

    dojo.listen(port,max_buffer_size=1024*1024*150000)

    print '*'*80
    print '*', '\033[93m'+'DOJO RUNNING', '\033[0m'
    print '*'
    print '*', 'open', '\033[92m'+'http://' + ip + ':' + str(port) + '/dojo/' + '\033[0m'
    print '*'*80

    tornado.ioloop.IOLoop.instance().start()


  def get_image(self):
    '''
    '''
    return self.__image


  def get_segmentation(self):
    '''
    '''
    return self.__segmentation

  def get_controller(self):
    '''
    '''
    return self.__controller

  def finish_setup(self):
    '''
    '''

    mojo_dir = self.__mojo_dir
    tmpdir = self.__tmpdir
    out_dir = self.__out_dir


    # register two data sources
    self.__segmentation = _dojo.Segmentation(mojo_dir, tmpdir)
    self.__image = _dojo.Image(mojo_dir, tmpdir)

    # and the controller
    self.__controller = _dojo.Controller(mojo_dir, out_dir, tmpdir, self.__segmentation.get_database())

    self.__configured = True

    print 'Setup finished.'

  def handle( self, r ):
    '''
    '''
    
    content = None

    # if request.find_input_header('upgrade'):
    #   # special case for websockets
    #   self.__websockets.handle(request)
    #   return

    # the access to the viewer
    if not self.__configured:
      content, content_type = self.__setup.handle(r.request)
    else:
      # viewer is ready
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

    # print 'IP',r.request.remote_ip

    r.set_header('Access-Control-Allow-Origin', '*')
    r.set_header('Content-Type', content_type)
    r.write(content)
    

  def close(self, signal, frame):
    '''
    '''
    print 'Sayonara..!!'
    output = {}
    output['origin'] = 'SERVER'
    # self.__controller.save(output)

    sys.exit(0)

def print_help( scriptName ):
  '''
  '''
  description = ''
  print description
  print
  print 'Usage: ' + scriptName + ' MOJO_DIRECTORY OUTPUT_DIRECTORY PORT'
  print '  optional: --skip-orphan-detection'
  print

#
# entry point
#
if __name__ == "__main__":

  # always show the help if no arguments were specified
  if len(sys.argv) != 1 and len( sys.argv ) < 4:
    print_help( sys.argv[0] )
    sys.exit( 1 )

  if len(sys.argv) == 1:
    # dojo was started without parameters
    # so we need to add an input folder
    input_dir = tempfile.mkdtemp()
    # and a output folder
    output_dir = tempfile.mkdtemp()
    # and a free port
    port = 1336
    orphan_detection = False
    result = 0
    import socket;
    while result==0:
      port += 1
      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      result = sock.connect_ex(('127.0.0.1',port))

    configured = False

  else:
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    port = sys.argv[3]
    orphan_detection = len(sys.argv) == 4
    configured = True

  logic = ServerLogic()
  logic.run( input_dir, output_dir, port, orphan_detection, configured )
