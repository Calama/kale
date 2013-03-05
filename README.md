kale
====

A convenient superclass and some helpers for stuff you want to keep in mongodb.


Features
--------

 * Collection-level operations are accessible though the `.collection`,
   eg. `MyModel.collection.find_one()`. It's verbose, but explicit is
   better than implicit.

 * Document-level operations are ported down directly to the model, eg.
   `m = MyModel(); m.save()`.

 * You can't access top-level document keys though dot notation on the
   models after they've been retrieved from the database. urmurmurm.

 * autoref?

