import pymongo

class Neuroblocks(object):

  DATABASE = 'meteor'

  def __init__(self, server):
    '''
    '''
    if server:
      try:
        self._connection = pymongo.Connection('mongodb://'+server+'/meteor')
        self._db = self._connection[Neuroblocks.DATABASE]
        print 'Connected to Neuroblocks.'
      except:
        print 'Connection to Neuroblocks failed.'
        

    else:
      self._connection = None

  def get_segmentation(self, id):
    '''
    '''
    return self._db.segmentation.find_one({"_id": id})

  def get_segmentation_log(self, id):
    '''
    '''
    return self._db.segmentation_log.find_one({"_id": id})

