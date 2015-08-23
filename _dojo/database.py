import numpy as np
import time
import sqlite3

MAX_SEGMENTS = 2147483647

class Database(object):

  def __init__(self, file):
    '''
    '''
    self.__connection = sqlite3.connect(file)
    self.__cursor = self.__connection.cursor()

    self._orphans = None
    self._potential_orphans = None

    self._merge_table = None
    self._lock_table = None

  def get_segment_info(self):
    '''
    '''
    self.__cursor.execute('SELECT * FROM segmentInfo')

    result = self.__cursor.fetchall()

    output = [None] * (len(result) + 1)

    for r in result:
      output[r[0]] = r[1:]

    return output

  def get_lock_table(self):
    '''
    '''
    try:
      self.__cursor.execute('SELECT * FROM segmentInfo WHERE confidence=100')

      result = self.__cursor.fetchall()

      output = {'0':True}

      for r in result:
        output[r[0]] = True
    except:
      output = {'0':True}

    return output


  def get_largest_id(self):
    '''
    '''
    self.__cursor.execute('SELECT * FROM segmentInfo ORDER BY id DESC')

    result = self.__cursor.fetchone()[0]

    try:
      self.__cursor.execute('SELECT * FROM relabelMap ORDER BY fromId DESC')

      result2 = self.__cursor.fetchone()
      if result2:
        result2 = result2[0]
      else:
        result2 = -1

    except:
      return result

    # output = [None] * (len(result) + 1)

    # for r in result:
    #   output[r[0]] = r[1:]

    if result > result2:
      return result

    if result2 > result:
      return result2

    return result 

  def get_id_tile_index(self,tile_id):
    '''
    '''
    self.__cursor.execute('SELECT * FROM idTileIndex WHERE id='+tile_id)

    result = self.__cursor.fetchall()

    output = []

    for r in result:
      output.append(r[1:])

    # w, z, y, x
    return output

  def lookup_label(self, lut, label):
    if lut[label] != label:
      lut[label] = self.lookup_label(lut, lut[label])
    return lut[label]

  def get_merge_table(self):
    '''
    '''
    lut = np.arange(MAX_SEGMENTS)

    try:
      self.__cursor.execute('SELECT * FROM relabelMap')

      result = self.__cursor.fetchall()
      result_list = list(result)

      print 'Creating lookup table buffer..'

      lut[[r[0] for r in result]] = [r[1] for r in result]

      print 'Start hardening the lookup table..'
      percent = 0
      st = time.time()
      for i, r in enumerate(result_list):
        if (i + 1) % (len(result_list) // 10) == 0:
          percent += 10
          print "{}% DONE, {} seconds".format(percent, int(time.time() - st))
        lut[r[0]] = self.lookup_label(lut, r[0])

        # print output

    except:
      return lut

    return lut

  def insert_lock(self, id):
    '''
    '''
    try:
      self.__connection.execute('SELECT * FROM segmentInfo WHERE id='+str(id))
      result = self.__cursor.fetchone()
      if result:
        self.__connection.execute('UPDATE segmentInfo SET confidence=100 WHERE id='+str(id))
      else:
        self.__connection.execute('INSERT INTO segmentInfo VALUES (?,?,?,?,?,?)', (id, 'newone', 0, 100, 'None', 'None'))
    
    except:
      print 'ERROR WHEN LOCKING', id

  def insert_merge(self, id1, id2):
    '''
    '''
    try:
      self.__connection.execute('INSERT INTO relabelMap VALUES (?,?)', (id1, id2))
    

    except:
      print 'ERROR WHEN MERGING', id1, id2

    # self.get_merge_table()


  def store(self):
    '''
    '''
    self.__connection.commit()
    # self.__connection.close()
      
  def get_orphans(self):
    '''
    '''
    return self._orphans

  def get_potential_orphans(self):
    '''
    '''
    return self._potential_orphans
    