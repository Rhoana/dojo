import json

class Controller(object):

  def __init__(self):
    '''
    '''
    self.__websocket = None

    self.__merge_table = {}

    self.__lock_table = {}

  def handshake(self, websocket):
    '''
    '''
    self.__websocket = websocket

    # always send the merge table first thing
    self.send_merge_table('SERVER')
    # then the lock table
    self.send_lock_table('SERVER')

    # then send the redraw command
    self.send_redraw('SERVER')


  def send_redraw(self, origin):
    '''
    '''
    output = {}
    output['name'] = 'REDRAW'
    output['origin'] = origin
    output['value'] = ''

    self.__websocket.send(json.dumps(output))

  def get_merge_table(self):
    '''
    '''
    return self.__merge_table

  def get_lock_table(self):
    '''
    '''
    return self.__lock_table

  def send_merge_table(self, origin):
    '''
    '''

    output = {}
    output['name'] = 'MERGETABLE'
    output['origin'] = origin
    output['value'] = self.get_merge_table()

    self.__websocket.send(json.dumps(output))

  def send_lock_table(self, origin):
    '''
    '''

    output = {}
    output['name'] = 'LOCKTABLE'
    output['origin'] = origin
    output['value'] = self.get_lock_table()

    self.__websocket.send(json.dumps(output))

  def on_message(self, message):
    '''
    '''
    print message
    input = json.loads(message)

    if input['name'] == 'MERGETABLE':
      self.__merge_table = input['value']

      self.send_merge_table(input['origin'])

      self.send_redraw(input['origin'])

    elif input['name'] == 'LOCKTABLE':
      self.__lock_table = input['value']

      self.send_lock_table(input['origin'])

      self.send_redraw(input['origin'])

    elif input['name'] == 'LOG':
      # just echo it
      self.__websocket.send(json.dumps(input))
