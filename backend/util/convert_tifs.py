#!/usr/bin/env python

#
# this script converts all .tif files in a directory to the pyramid tif format
# this uses 'convert' of imagemagick
#
import os
import sys

SIZE='256x256'


class ConvertLogic():
  '''
  '''
  def __init__( self ):
    '''
    '''

  def run( self, directory ):
    '''
    '''
    for root, dirs, files in os.walk(directory):

      fullpaths = [(os.path.join(root, name)) for name in files]

      for f in fullpaths:
        d_name = os.path.split(f)[0]
        f_name = os.path.split(f)[1]
        print '>>> converting ' + f_name + ' to ' + 'p_' + f_name
        os.system('convert '+f+' -define tiff:tile-geometry='+SIZE+' ptif:'+os.path.join(d_name, 'p_' + f_name))
        print '>>> converted ' + f_name + ' to ' + 'p_' + f_name


def print_help( scriptName ):
  '''
  '''
  description = 'Convert all .tif files in a directory to the pyramid tif format'
  print description
  print
  print 'Usage: ' + scriptName + ' DIR'
  print


#
# entry point
#
if __name__ == "__main__":

  # always show the help if no arguments were specified
  if len( sys.argv ) < 2:
    print_help( sys.argv[0] )
    sys.exit( 1 )

  logic = ConvertLogic()
  logic.run( sys.argv[1] )