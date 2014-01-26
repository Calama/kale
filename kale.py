# -*- coding: utf-8 -*-
"""
    kale

    lightweight model base class inspired by minimongo

    :requires: pymongo
    :copyright: Calama Consulting, written and maintained by uniphil
    :license: :) see http://license.visualidiot.com/
"""


import abc
import weakref
import functools
import pymongo


try:
    basestring
except NameError:
    # must by python3
    basestring = (str, bytes)


class WrongLevel(AttributeError):
    pass


class GetClassProperty(property):
    """A property. On a class. Yep.
    Json R. Coombs on StackOverflow: http://stackoverflow.com/a/1383402/1299695
    """
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


classproperty = GetClassProperty


class Cursor(pymongo.cursor.Cursor):
    """inflatable"""
    def __init__(self, collection, *args, **kwargs):
        super(Cursor, self).__init__(collection, *args, **kwargs)
        self._model_class = collection._model_class

    def next(self):
        document = super(Cursor, self).next()
        model_instance = self._model_class.inflate(document)
        return model_instance

    def __getitem__(self, index):
        if isinstance(index, slice):
            # pymongo will return an iterator, so next will be called.
            return super(Cursor, self).__getitem__(index)
        elif isinstance(index, int):
            # get a particular item by index
            document = super(Cursor, self).__getitem__(index)
            model_instance = self._model_class.inflate(document)
            return model_instance


class Collection(pymongo.collection.Collection):
    """Subclass pymongo.collection.Collection
    So we can hijack returned documents and make them instances of a model.
    """

    def __init__(self, model, database, name, *args, **kwargs):
        """make sure database is a pymongo database, not a string name"""
        super(Collection, self).__init__(database, name, *args, **kwargs)
        self._model_class = model
        self.raw = lambda: pymongo.collection.Collection(
            database, name, *args, **kwargs)

    def find(self, *args, **kwargs):
        cursor = Cursor(self, *args, **kwargs)
        return cursor

    def find_one(self, *args, **kwargs):
        document = super(Collection, self).find_one(*args, **kwargs)
        if document:
            model_instance = self._model_class.inflate(document)
            return model_instance


def collectionmethod(fn):
    @classmethod
    @functools.wraps(fn)
    def wrapper(model, *args, **kwargs):
        return fn(model.collection, *args, **kwargs)
    return wrapper


class AttrDict(dict):
    """A dictionary whose keys are accessible with dot notation
    cool __setitem__ -> http://stackoverflow.com/a/2588648/1299695
    """

    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            if not isinstance(value, AttrDict):
                value = AttrDict(value)
        elif not isinstance(value, basestring):
            try:
                value = [AttrDict._try_attrdict(v) for v in value]
            except TypeError:
                """ignore iterables"""
        super(AttrDict, self).__setitem__(key, value)

    @classmethod
    def _try_attrdict(cls, thing):
        """cast a thing to attrdict if possible"""
        if not thing and not isinstance(thing, dict):
            """don't cast empty non-dict iterables"""
            return thing
        try:
            return cls(thing)
        except ValueError:
            return thing

    def update(self, *args, **kwargs):
        if len(args) > 1:
            raise TypeError("yo. one argument. not {}".format(len(args)))
        other = dict(*args, **kwargs)
        for key in other:
            self[key] = other[key]

    def setdefault(self, key, value=None):
        if key not in self:
            self[key] = value
        return self[key]

    def __getattribute__(self, attr):
        """Access items with dot notation."""
        try:
            return object.__getattribute__(self, attr)
        except AttributeError as attr_error:
            try:
                return super(AttrDict, self).__getitem__(attr)
            except KeyError:
                raise attr_error

    def __setattr__(self, attr, value):
        """Set items with dot notation"""
        # check for class stuff, like descripters, before hijacking.
        # http://stackoverflow.com/a/9161707/1299695
        for cls in self.__class__.__mro__ + (self,):
            if attr in cls.__dict__:
                return object.__setattr__(self, attr, value)
        self[attr] = value

    def __delattr__(self, key):
        """Delete items with dot notation"""
        # see AttrDict.__setattr__()
        for cls in self.__class__.__mro__ + (self,):
            if key in cls.__dict__:
                return object.__delattr__(self, key)
        try:
            return super(AttrDict, self).__delitem__(key)
        except KeyError as e:  # it was accessed as an attribute.
            raise AttributeError(e)


class Model(AttrDict):
    """Helper methods and properties."""

    _live_documents = weakref.WeakValueDictionary()

    def __new__(cls, *args, **kwargs):
        """Return an instance of the class.
        ABCMeta isn't enforced because AttrDict screws around with __getattr__,
        so we have to enforce subclass conformance manually.
        """
        if cls is Model:
            raise TypeError('Only instantiate subclasses of kale.Model')
        if isinstance(cls._collection_name, abc.abstractproperty):
            raise TypeError('You had better define a _collection_name...')
        instance = super(Model, cls).__new__(cls, *args, **kwargs)
        return instance

    @abc.abstractproperty
    def _database(cls):
        """The pymongo database"""

    @abc.abstractproperty
    def _collection_name(cls):
        """The MongoDB collection name to use. Kale won't guess for you."""

    @classproperty
    @classmethod
    def collection(cls):
        """Return the pymongo collection storing instances of the model."""
        return Collection(cls, cls._database, cls._collection_name)

    def save(self, *args, **kwargs):
        """Create or update the instance in the database. Returns the pymongo
        ObjectId. See :meth: pymongo.collection.Collection.save.
        """
        _id = self.collection.save(self, *args, **kwargs)
        self._live_documents[_id] = self
        return _id

    def insert(self, *args, **kwargs):
        """Save as a new document in the database. Wraps collection.insert"""
        _id = self.collection.insert(self, *args, **kwargs)
        self._live_documents[_id] = self
        return _id

    def remove(self, spec=None, *args, **kwargs):
        """Remove this document from the databse."""
        if spec:
            raise WrongLevel('Collection-level removes blah blah blah use '
                             'Model.collection.remove(spec)')
        if '_id' in self:
            return self.collection.remove({'_id': self.pop('_id')})

    def is_in_db(self):
        """Does this instance have a record in the database?"""
        return '_id' in self

    @classmethod
    def inflate(cls, json):
        """Return a model instance given its MongoDB json representation"""
        if '_id' in json and json['_id'] in cls._live_documents:
            instance = cls._live_documents[json['_id']]
        else:
            instance = cls.__new__(cls)
            Model.__init__(instance, json)
        return instance

    def __repr__(self):
        dict_repr = dict.__repr__(self)
        return '<{}: {}>'.format(self.__class__.__name__, dict_repr)
