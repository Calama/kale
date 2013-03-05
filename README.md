kale
====

A convenient superclass and some helpers for stuff you want to keep in mongodb.


Features
--------

### CRUD -- methods for model Creation, Reading, Updating, and Deleting

#### Creating, saving

`Model.save()` will call `mongo

#### Reading

`Model.find_one()` wraps `pymongo.read_one()`, returning an instantiation of `Model` based on the result of the query, or `None`.

#### Save

`

