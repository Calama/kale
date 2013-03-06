kale
====

A convenient superclass and some helpers for stuff you want to keep in mongodb.


Motivation
----------

PyMongo is awesome. Object-oriented data through model classes is awesome. kale
tries to bridge those two, and get out of your way.


### Why not just use PyMongo?

You should! It's awesome, and perfectly useable stand-alone. It keeps you
connected to your data, and to mongo itself, and I think that's important.

Kale does not try to stand as a layer to hide PyMongo from you. It simply
changes a couple things around to make more sense in the Model paradigm, and
give you something consistent to build your models on. It extends PyMongo.


### blah blah blah

about the paradigm, why I don't like other ORMs. explicit++; schema
validation--.


Quick, Start!
-------------

This is not a tutorial on PyMongo. There's a decent chance that PyMongo alone
is enough for you. Start there.


```python
Python 2.7.3 (default, Sep 26 2012, 21:51:14) 
[GCC 4.7.2] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> from pymongo import MongoClient
>>> from kale import Model
>>> 
>>> def super_insecure_hash(to_hash):
...     hashed = "".join(str(ord(c)) for c in to_hash)
...     return hashed
... 
>>> class User(Model):
...     _collection_name = 'users'
...     _database = MongoClient().test_database
...     
...     def __init__(self, username, password):
...         self.username = username
...         self.set_password(password)
...     
...     def set_password(self, password):
...         pw_hash = super_insecure_hash(password)
...         self.pw_hash = pw_hash
...     
...     def check_password(self, password_challenge):
...         hashed_challenge = super_insecure_hash(password_challenge)
...         return hashed_challenge == self.pw_hash  # true if they match
... 
>>> alice = User('alice', 'abc123')
>>> alice.save()
ObjectId('5137a57d360e2e139105db4f')
>>> alice
{'username': 'alice', 'pw_hash': '979899495051', '_id': ObjectId('5137a57d360e2e139105db4f')}
>>> del alice
>>> 
>>> def login(username, password):
...     requested_user = User.collection.find_one({'username': username})
...     if requested_user.check_password(password):
...         return requested_user
...     else:
...         return 'Bad login!'
... 
>>> faker = login('alice', '123456')
>>> faker
'Bad login!'
>>> 
>>> real_alice = login('alice', 'abc123')
>>> real_alice
{u'username': u'alice', u'pw_hash': u'979899495051', u'_id': ObjectId('5137a57d360e2e139105db4f')}
>>> type(real_alice)
<class '__main__.User'>
>>> 
>>> real_alice.set_password('password')
>>> real_alice.save()
ObjectId('5137a57d360e2e139105db4f')
```


kale provides you with a base class for your own models. This base class
subclasses python's `dict`, so it can be directly saved to Mongo.

You need to define two things in your models:

 1. `_collection_name`, a string specifying the collection where instances of
    your models should be saved to and loaded from.

 2. '_database', a PyMongo database instance.

Your model will be provided with four attributes you should know about:

 1, 2, 3. `Model.save`, `Model.insert`, `Model.remove`: These functions map
    almost directly to `PyMongo`'s `Collection.save`, etc. However, they are
    inteded for use on _instances of your model_. So you don't need to pass
    anything to them. If you have an instance of something, you can just call
    `save()` on it, and it'll be saved.

 4. `Model.collection`: This attribute gives you a special version of
    `PyMongo`'s `Collection` object, tied to the model's collection (specified
    with `Model._collection_name`!). The special part is that any documents
    retrieved from mongo will be instantiations of the Model.

    The `Model.collection.raw()` method will give you access to `PyMongo`'s
    `Collection` for the model, unaltered.


Notes
-----

 * Collection-level operations are accessible though the `.collection`,
   eg. `MyModel.collection.find_one()`. It's verbose, but explicit is
   better than implicit.

 * All documents returned by `raw` will be instantiated as models. To get the
   raw json, use `raw()`, eg. `MyModel.collection.raw().find_one()`.

 * Document-level operations are ported down directly to the model, eg.
   `m = MyModel(); m.save()`.

 * You can't access top-level document keys though dot notation on the
   models after they've been retrieved from the database.

 * There is no model-level `update`, since it clashes with `dict`'s `update`.
   Use `save`, or `Model.collection.update(instance, ...)`.

 * The model-level `remove` is restricted to only remove the model's document.

 * No special ref support... yet.

 * Tests are desperately lacking. Help!
