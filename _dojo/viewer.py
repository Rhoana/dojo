import os
import re
import StringIO

class Viewer(object):

  def __init__(self):
    '''
    '''
    self.__query_viewer_regex = re.compile('^/dojo/.*$')

    self.__web_dir = '_web/'

  def content_type(self, extension):
    '''
    '''
    return {
      '.js': 'text/javascript',
      '.html': 'text/html',
      '.png': 'image/png',
      '.map': 'text/html'
    }[extension]

  def handle(self, request):
    '''
    '''

    if not self.__query_viewer_regex.match(request.uri):
      # this is not a valid request for the viewer
      return None, None

    url = request.uri

    # check if a request goes straight to a folder
    if url.split('/')[-1] == '':
      # add index.html
      url += 'index.html'

    # get filename from query
    requested_file = self.__web_dir + url.replace('/dojo/', '')
    extension = os.path.splitext(requested_file)[1]



    if not os.path.exists(requested_file):
      return 'Error 404', 'text/html'

    with open(requested_file, 'r') as f:
      content = f.read()

    return content, self.content_type(extension)
