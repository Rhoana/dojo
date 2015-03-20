import pymongo
from bson.objectid import ObjectId

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
    return self._db.segmentationLog.find_one({"_id": id})

  def save_state(self, state):
    '''
    '''

    return self._db.appStates.insert(state)

  def save_pick2d(self, values):
    '''
    '''
    return self._db.appPickSegment.insert(values)

  def save_action(self, values):
    '''
    '''

    db = self._db

    project_id = values['projectId']
    user_id = values['userId']
    segmentId1 = values['values'][0]
    segmentId2 = values['values'][1]
    date = values['on']


    segment1 = db.segmentation.find_one({"projectId":project_id, "id":segmentId1});

    segment2 = db.segmentation.find_one({"projectId":project_id, "id":segmentId2});

    db.segmentationLog.insert({'objId':segment1['_id'],
                               'projectId':project_id,
                               'operation':'merge',
                               'by':user_id,
                               'on': date,
                               'obj': segment1,
                               'objId2': segment2['_id'],
                               'obj2':segment2 });

    voxelsSum = segment1['voxels'] + segment2['voxels'];
    db.segmentation.update({'_id':segment1['_id']},
      {'$set':{'voxels': voxelsSum, 'merged':0, 'lastUpdateOn': date, 'lastUpdateBy':user_id}});
    db.segmentation.update({'_id':segment2['_id']},
      {'$set':{ 'merged':1, 'lastUpdateOn': date, 'lastUpdateBy':user_id}});

    print 'stored neuroblocks action'


  def get_state(self, state_id):
    '''
    '''

    state = self._db.appStates.find_one({"_id": ObjectId(state_id)})
    state['_id'] = str(state['_id'])
    state['on'] = str(state['on'])

    return state
