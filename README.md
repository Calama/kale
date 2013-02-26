kale
====

A convenient superclass and some helpers for stuff you want to keep in mongodb.

Add and remove properties all you like. They'll be there.

Built on pymongo and jsonpickle.


Install
-------

```sh
pip install kale
```

hint: virtualenv is awesome.


Quickstart
----------

```python
>>> from kale import KaleModel
>>> class User(KaleModel):
...     def __init__(self, username):
...             self.username = username
... 
>>> joe = User('joe')
>>> joe.password = 'security now!'
>>> joe.save()
ObjectId('512d1ace360e2e3037a3d89c')
>>> del joe
>>> retrieved_joe = User.find_one({'username': 'joe'})
>>> retrieved_joe.__class__
<class '__main__.User'>
>>> retrieved_joe.password
u'security now!'
>>> 
```

By default, kale will try to use a connection on localhost to a database
called kale. To set this yourself, monkey-patch db.
