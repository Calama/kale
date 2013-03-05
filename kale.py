# -*- coding: utf-8 -*-
"""
    kale


    lightweight model base class inspired by minimongo


    so should the Model base class inherit from Collection? If yes, then Model
    should cover a subset of Collection: a set of sets of documents. And then
    an instance of a Model would be a set of documents. That makes no sense. A
    model instance is analogous to a document (clearly!).

    It almost feels right because a Collection is a collection of things, and a
    python class is kind of like a collection of possible instances of things.
    But it's off a step: a pymongo Collection _instance_ is a collection of
    things, with Collection being a sort of collection of possible collection
    instances. A Model instance inheriting from collection should then be a
    a collection of things. ... ... ...

    So then... does the standard python ORM convention of Model.find even make
    sense? No. Document.find should not query a collection. It's convenient and
    looks ok on the surface, but is actually quite weird.

    So... how should a model be connected it the connection its document
    belongs to? I think it's fine to keep a _reference_ to the collection on
    the model.


    As a result:

     * Collection-level operations are accessible though the `.collection`,
       eg. `MyModel.collection.find_one()`. It's verbose, but explicit is
       better than implicit.

     * Document-level operations are ported down directly to the model, eg.
       `m = MyModel(); m.save()`.

    That feels right to me.


    Implications:

     * You can't access top-level document keys though dot notation on the
       models after they've been retrieved from the database. urmurmurm.


    Questions and to-do:

    :requires: pymongo
    :copyright: Calama Consulting, written and maintained by uniphil
    :license: :) see http://license.visualidiot.com/
"""


from abc import ABCMeta, abstractproperty
from pymongo import Connection
#from pymongo.collection import Collection


DATABASE_NAME = 'database'


class LazyThing(object):

    def __init__(self, cls, *args, **kwargs):
        self._cls = cls
        self._inst_args = args
        self._inst_kwargs = kwargs

    def __getattr__(self, key):
        if not hasattr(self, '_thing'):
            inst = self._cls(*self._inst_args, **self._inst_kwargs)
            setattr(self, '_thing', inst)
        return getattr(self._thing, key)


db = LazyThing(Connection)  # you can monkey patch this!


class WrongLevel(AttributeError):
    pass


class GetClassProperty(property):
    """Make a property-like thing that works on classes and instances.

    It's nice to have access to the collection as a property. It's nice not to
    have to instantiate the model just to get that property.

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


class Model(AttrDict):
    """Helper methods and properties."""

    __metaclass__ = ABCMeta

    @abstractproperty
    def _collection_name(cls):
        """The MongoDB collection name to use. Kale won't guess for you."""
        return

    @GetClassProperty
    @classmethod
    def collection(cls):
        """Return the pymongo collection storing instances of the model."""
        return db[cls._collection_name]

    def save(self, *args, **kwargs):
        """Create or update the instance in the database. Returns the pymongo
        ObjectId. See :meth: pymongo.collection.Collection.save.
        """
        return self.collection.save(self, *args, **kwargs)

    def insert(self, *args, **kwargs):
        """Save as a new document in the database. Wraps collection.insert"""
        return self.collection.insert(self, *args, **kwargs)

    def update(self, spec=None, document=None, *args, **kwargs):
        """Update the current document (only!) in the database."""
        if spec or document:
            raise WrongLevel('Collection-level updates should be called on '
                             'Model.collection.update(...), not Model.updat()')
        spec = {'_id': self._id}
        return self.collection.update(spec=spec, document=self)

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

    # @classmethod
    # def find_one(cls, *args, **kwargs):
    #     """Wrap pymongo's find_one to return an instance of the model.
    #     """
    #     json = cls.collection.find_one(*args, **kwargs)
    #     instance = cls.inflate(json)
    #     return instance

    # def find(cls, *args, **kwargs):
    #     pass

#     @classmethod
#     def find(cls, *args, **kwargs):
#         """Iterable of instances of this model from the query."""
#         cursor = cls.collection.find(*args, **kwargs)
#         iterable = inflate_cursor(cursor, cls)
#         return iterable


class M(Model):
    pass


m = M()
print m
print dir(m)
