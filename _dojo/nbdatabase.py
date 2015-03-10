import pymongo

class NBDatabase(object):

  NB_DATABASE_SERVER = '127.0.0.1'
  NB_DATABASE = 'meteor'

  def __init__(self):
    '''
    '''
    self._connection = pymongo.Connection('mongodb://'+NB_DATABASE_SERVER+'/meteor')
    self._db = self._connection[NB_DATABASE]

  def get_segmentation(self, id):
    '''
    '''
    return self._db.segmentation.find_one({"_id": id})

  def get_segmentation_log(self, id):
    '''
    '''
    return self._db.segmentation_log.find_one({"_id": id})

    