# -*- coding: utf-8 -*-
"""
    kale

    lightweight model base class inspired by minimongo

    :requires: pymongo
    :copyright: Calama Consulting, written and maintained by uniphil
    :license: :) see http://license.visualidiot.com/
"""


from abc import ABCMeta, abstractproperty
from pymongo import Connection
from pymongo.collection import Collection as PyMongoCollection
from pymongo.cursor import Cursor as PyMongoCursor


class LazyThing(object):
    """Delay something's instantiation until an attribute is requested"""
    def __init__(self, class_):
        self.class_ = class_

    def __getattr__(self, key):
        if not hasattr(self, '_thing'):
            setattr(self, '_thing', self.class_())
        return getattr(self._thing, key)


connection = LazyThing(Connection)  # you can monkey patch this!
DATABASE_NAME = 'database'  # and this!


class WrongLevel(AttributeError):
    pass


class GetClassProperty(property):
    """A property. On a class. Yep.
    Json R. Coombs on StackOverflow: http://stackoverflow.com/a/1383402/1299695
    """
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


class AttrDict(dict):
    """A dictionary whose keys are accessible with dot notation
    cool __setitem__ -> http://stackoverflow.com/a/2588648/1299695
    """

    def __init__(self, *args, **kwargs):
        self.__update(*args, **kwargs)

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            value = AttrDict(value)
        super(AttrDict, self).__setitem__(key, value)

    def __update(self, *args, **kwargs):
        if len(args) > 1:
            raise TypeError("yo. one argument. not {}".format(len(args)))
        other = dict(*args, **kwargs)
        for key in other:
            self[key] = other[key]

    update = __update

    def setdefault(self, key, value=None):
        if key not in self:  # ... uh... python's default behavior is weird
            self[key] = value
        return self[key]

    def __getattr__(self, attr):
        """Access items with dot notation"""
        try:
            return super(AttrDict, self).__getitem__(attr)
        except KeyError as e:
            raise AttributeError(e)  # it was accessed as an attribute!

    def __setattr__(self, attr, value):
        """Set items with dot notation"""
        try:
            self[attr] = value
        except KeyError as e:
            raise AttributeError(e)  # it was accessed as an attribute!

    def __delattr__(self, key):
        """Delete items with dot notation"""
        try:
            return super(AttrDict, self).__delitem__(key)
        except KeyError as e:  # it was accessed as an attribute.
            raise AttributeError(e)


class Cursor(PyMongoCursor):
    """inflatable"""
    def __init__(self, collection, *args, **kwargs):
        super(Cursor, self).__init__(collection, *args, **kwargs)
        self._model_class = collection._model_class

    def next(self):
        print "nexting"
        document = super(Cursor, self).next()
        model_instance = self._model_class.inflate(document)
        return model_instance

    def __getitem__(self, index):
        print "getting"
        if isinstance(index, slice):
            # pymongo will return an iterator, so next will be called.
            return super(Cursor, self).__getitem__(index)
        elif isinstance(index, (int, long)):
            # get a particular item by index
            document = super(Cursor, self).__getitem__(index)
            model_instance = self._model_class.inflate(document)
            return model_instance


class Collection(PyMongoCollection):
    """Subclass pymongo.collection.Collection
    So we can hijack returned documents and make them instances of a model."""

    def __init__(self, model, database, name, *args, **kwargs):
        """database is not a name...."""
        super(Collection, self).__init__(database, name, *args, **kwargs)
        self._model_class = model

    def find(self, *args, **kwargs):
        pymongo_cursor = Cursor(collection=self, *args, **kwargs)
        return pymongo_cursor

    def find_one(self, *args, **kwargs):
        print 'finding one from', self.collection
        document = super(Collection, self).find_one(*args, **kwargs)
        if document:
            model_instance = self._model_class.inflate(document)
            return model_instance
        return None


class Model(AttrDict):
    """Helper methods and properties."""

    __metaclass__ = ABCMeta

    @GetClassProperty
    @classmethod
    def _database(cls):
        return connection.DATABASE_NAME

    @abstractproperty
    def _collection_name(cls):
        print 'asdfasfdasdfasf'
        """The MongoDB collection name to use. Kale won't guess for you."""
        return

    @GetClassProperty
    @classmethod
    def collection(cls):
        """Return the pymongo collection storing instances of the model."""
        if not hasattr(cls, '_collection'):
            cls._collection = Collection(cls, cls._database,
                                         cls._collection_name)
        return cls._collection

    def save(self, *args, **kwargs):
        """Create or update the instance in the database. Returns the pymongo
        ObjectId. See :meth: pymongo.collection.Collection.save.
        """
        return self.collection.save(self, *args, **kwargs)

    def insert(self, *args, **kwargs):
        """Save as a new document in the database. Wraps collection.insert"""
        return self.collection.insert(self, *args, **kwargs)

    def remove(self, spec=None, *args, **kwargs):
        """Remove this document from the databse."""
        if spec:
            raise WrongLevel('Collection-level removes blah blah blah use '
                             'Model.collection.remove(spec)')
        spec = {'_id': self._id}
        return self.collection.remove(spec=spec)

    @classmethod
    def inflate(cls, json):
        """Return a model instance given its MongoDB json representation"""
        instance = cls.__new__(cls)
        Model.__init__(instance, json)
        return instance
