# -*- coding: utf-8 -*-
"""
    kale

    A convenient superclass for stuff you want to keep in mongodb.

        In [1]: class User(kModel):
           ...:     def __init__(self, username):
           ...:         self.username = username
           ...: 

        In [2]: joe = User('joe')

        In [3]: joe.save()
        Out[3]: ObjectId('5127ef70c7b7e814a1a4405f')

        In [4]: del joe

        In [5]: joe = User.find_one({'username': 'joe'})

        In [6]: joe.__class__
        Out[6]: User

    :requires: pymongo, jsonpickle
    :copyright: none, but put together by uniphil
    :license: :) see http://license.visualidiot.com/
"""

from abc import ABCMeta
from pymongo import Connection
from jsonpickle import Pickler, Unpickler

DATABASE_NAME = 'kale'

db = Connection().DATABASE_NAME
jsonify = Pickler().flatten
unjson = Unpickler().restore


class GetClassProperty(property):
    """Make a property-like thing that works on classes and instances.
    
    It's nice to have access to the collection as a property. It's nice not to
    have to instantiate the model just to get that property.

    Json R. Coombs on StackOverflow: http://stackoverflow.com/a/1383402/1299695
    """
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


class kModel(object):
    """Easy-access json object flatten/restore with mongodb helpers built in!

    Do not instantiate this directly. Subclass it. Store properties on your
    subclasses n stuff. Save. Restore. Magic.

    If you want to specify a collection where your objects will be saved, just
    set the class-level property `_collection_name` to something.
    """

    __metaclass__ = ABCMeta # I'm expressing intent here. Since there are no
                            # abstract methods, this does nothing.

    @GetClassProperty
    @classmethod
    def _collection_name(cls):
        """You can just define this straight-up as a normal attribute
        
        >>> class MyModel(kModel):
        ...     _collection_name = 'mymodels'
        ...

        etc.
        """
        return cls.__name__.lower() + 's'

    @GetClassProperty
    @classmethod
    def collection(cls):
        return mongo.db[cls._collection_name]

    @property
    def flat(self):
        """Return a flattened representation of the model instance.
        The mongo _id property, if present, will still be a pymongo.ObjectId.
        """
        
        if hasattr(self, '_id'):
            # jsonpickle </3 pymongo.ObjectIDs. pull it out before flattening.
            _id = self._id
            del self._id
            json_repr = jsonify(self)
            # aaaaaand back
            json_repr['_id'] = _id
            self._id = _id
        else:
            json_repr = jsonify(self)

        return json_repr

    def save(self):
        """Create or update the instance in the database. Returns the
        pymongo.ObjectId if it's new.
        """
        mongo_json = self.flat
        if '_id' in mongo_json:
            # updating an old object
            self.collection.update({'_id': mongo_json['_id']}, mongo_json)
        else:
            # inserting a new one!
            _id = self.collection.insert(mongo_json)
            self._id = _id
            return _id

    @classmethod
    def inflate(cls, json_repr):
        """Given a jsonpickled dict, instantiate an instance of this class.
        
        If you use model.collection.[some pymongo method], you will want to
        inflate the result with this method.

        If the dict doesn't reference this model, try to cast it (and probably
        fail).
        """
        obj = unjson(json_repr)
        if not isinstance(obj, cls):
            # not a member of this class? try to cast it...
            try:
                return cls(obj)
            except TypeError:
                # c'mon, that was a pretty terrible plan man.
                return None
        return obj

    # @classmethod
    # def find(cls, dict_query):
    #     """Lazy iterable attempt at inflation of results.
    #     """
        
    #     flat_jsons = cls.collection.find(dict_query)
    #     instances = [cls.inflate(j) for j in flat_json
    #     return instance

    @classmethod
    def find_one(cls, dict_query):
        """Thin pymongo wrapper that will inflate the result into an actual
        instance for you.
        """
        flat_json = cls.collection.find_one(dict_query)
        instance = cls.inflate(flat_json)
        return instance
