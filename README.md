kale
====

A convenient superclass and some helpers for stuff you want to keep in mongodb.


Notes
-----

 * Collection-level operations are accessible though the `.collection`,
   eg. `MyModel.collection.find_one()`. It's verbose, but explicit is
   better than implicit.

 * Document-level operations are ported down directly to the model, eg.
   `m = MyModel(); m.save()`.

 * You can't access top-level document keys though dot notation on the
   models after they've been retrieved from the database. urmurmurm.

 * There is no model-level `update`, since it clashes with `dict`'s `update`.
   Use `save`, or `Model.collection.update(instance, ...)`.

 * The model-level `remove` is restricted to only remove the model's document.

 * No special ref support... yet.

 * Tests are desperately lacking. Help!
