# -*- coding: utf-8 -*-
"""
    kale

    A convenient superclass for stuff you want to keep in mongodb built on
    pymongo and jsonpickle.

    Add and remove properties all you like. They'll be there.

        In [1]: class User(KaleModel):
           ...:     def __init__(self, username):
           ...:         self.username = username
           ...: 

        In [2]: joe = User('joe')

        In [3]: joe.password = 'security now!'

        In [4]: joe.save()
        Out[4]: ObjectId('5127ef70c7b7e814a1a4405f')

        In [5]: del joe

        In [6]: joe = User.find_one({'username': 'joe'})

        In [7]: joe.__class__
        Out[7]: User

        In [8]: joe.password
        Out[8]: 'security now!'


    By default, kale will try to use a connection on localhost to a database
    called kale. To set this yourself instead, monkey-patch db.

    :requires: pymongo, jsonpickle
    :copyright: Calama Consulting, written and maintained by uniphil
    :license: :) see http://license.visualidiot.com/
"""


from abc import ABCMeta
from pymongo import Connection
from jsonpickle import Pickler, Unpickler


jsonify = Pickler().flatten
unjson = Unpickler().restore
# for now, monkey-patch db. there may be a better api for this later.
db = None
try:
    DATABASE_NAME = 'kale'
    db = Connection().DATABASE_NAME
except:
    pass


def inflate(flat, model=None):
    """Restore a flat json representation to an actual object.

    If it was flattened with jsonpickle, it will already have a 'py/object'
    property, which will be used to instantiate.

    :param model: the importable class you want to restore to.
    """
    if model:
        # check if it's an instance or a class
        cls = model if isinstance(model, type) else model.__class__
        module = cls.__module__
        name = cls.__name__
        # format from jsonpickle.pickler.Pickler._flatten_obj_instance
        pyobjstr = '{module}.{name}'.format(module=module, name=name)
        flat['py/object'] = pyobjstr

    obj = unjson(flat)
    return obj


def inflate_cursor(cursor, model=None):
    """Wrap a the inflator around a pymongo cursor (or any iterable of
    jsonpickle objects).
    """
    while True:
        flat = cursor.next()
        obj = inflate(flat, model)
        yield obj


class GetClassProperty(property):
    """Make a property-like thing that works on classes and instances.
    
    It's nice to have access to the collection as a property. It's nice not to
    have to instantiate the model just to get that property.

    Json R. Coombs on StackOverflow: http://stackoverflow.com/a/1383402/1299695
    """
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


class KaleModel(object):
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
        
        >>> class MyModel(KaleModel):
        ...     _collection_name = 'anycollection'
        """
        return cls.__name__.lower() + 's'

    @GetClassProperty
    @classmethod
    def collection(cls):
        return db[cls._collection_name]

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
    def find(cls, *args, **kwargs):
        """Iterable of instances of this model from the query."""
        cursor = cls.collection.find(*args, **kwargs)
        iterable = inflate_cursor(cursor, cls)
        return iterable

    @classmethod
    def find_one(cls, *args, **kwargs):
        """Return a single instance of the class given a mongodb query.
        """
        flat_json = cls.collection.find_one(*args, **kwargs)
        instance = inflate(flat_json, cls)
        return instance
