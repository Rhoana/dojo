import json

class Controller(object):

  def __init__(self):
    '''
    '''
    self.__websocket = None

    self.__merge_table = {}

  def handshake(self, websocket):
    '''
    '''
    self.__websocket = websocket

    # always send the merge table first thing
    self.send_merge_table('SERVER')

  def get_merge_table(self):
    '''
    '''
    return self.__merge_table

  def send_merge_table(self, origin):
    '''
    '''

    output = {}
    output['name'] = 'MERGETABLE'
    output['origin'] = origin
    output['value'] = self.get_merge_table()

    print 'sending', output

    self.__websocket.send_message(json.dumps(output))

  def on_message(self, message):
    '''
    '''
    print message
    input = json.loads(message)

    if input['name'] == 'MERGETABLE':
      self.__merge_table = input['value']

      self.send_merge_table(input['origin'])
