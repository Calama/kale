import unittest
import pymongo
from bson import ObjectId
import kale


class TestModel(unittest.TestCase):

    def setUp(self):
        self.connection = pymongo.MongoClient()
        self.database_name = 'kale_testing_database'

        class EmptyModel(kale.Model):
            _database = self.connection[self.database_name]
            _collection_name = 'empty_models'

        self.EmptyModel = EmptyModel

    def tearDown(self):
        self.connection.drop_database(self.database_name)

    def test_base_model(self):
        self.assertRaises(TypeError, kale.Model)

    def test_collection(self):
        assert isinstance(self.EmptyModel.collection,
            pymongo.collection.Collection)
        em = self.EmptyModel()
        assert isinstance(em.collection, pymongo.collection.Collection)

    def test_collection_name(self):
        class NoName(kale.Model):
            pass
        self.assertRaises(TypeError, NoName)
        self.assertEqual(self.EmptyModel.collection.name, 'empty_models')

    def test_save(self):
        instance = self.EmptyModel()
        _id = instance.save()
        assert isinstance(_id, ObjectId)
        assert '_id' in instance

    def test_save_again(self):
        instance = self.EmptyModel()
        _id1 = instance.save()
        _id2 = instance.save()
        self.assertEqual(_id1, _id2)

    def test_saved(self):
        self.EmptyModel().save()
        count = self.EmptyModel.collection.count()
        self.connection.fsync()
        self.assertEqual(count, 1)

    def test_insert(self):
        instance = self.EmptyModel()
        instance.insert()
        assert '_id' in instance
        self.assertRaises(pymongo.errors.DuplicateKeyError, instance.insert)
        instance2 = self.EmptyModel()
        instance2.insert()
        assert instance._id != instance2._id

    def test_inserted(self):
        self.EmptyModel().insert()
        count = self.EmptyModel.collection.count()
        self.connection.fsync()
        self.assertEqual(count, 1)

    def test_remove(self):
        instance = self.EmptyModel()
        instance.save()
        instance.remove()
        self.connection.fsync()
        self.assertEqual(self.EmptyModel.collection.count(), 0)
        assert '_id' not in instance

    def test_simple_inflate(self):
        json = {}
        instance = self.EmptyModel.inflate(json)
        assert isinstance(instance, self.EmptyModel)

    def test_recursive_inflate(self):
        json = {'a': {}}
        instance = self.EmptyModel.inflate(json)
        assert isinstance(instance.a, kale.AttrDict)

    def test_json_native_types(self):
        from datetime import datetime
        json = {
            'list': [1, 2, 3],
            'string': 'abcd',
            'nest': {},
            'dt': datetime.now(),
            'bool': True,
            'float': 1.1,
            'int': 1,
        }
        self.EmptyModel(json).save()
        self.connection.fsync()
        json_out = self.EmptyModel.collection.find_one()
        assert isinstance(json_out.list, list)
        assert isinstance(json_out.string, unicode)
        assert isinstance(json_out.nest, dict)
        assert isinstance(json_out.dt, datetime)
        assert isinstance(json_out.bool, bool)
        assert isinstance(json_out.float, float)
        assert isinstance(json_out.int, int)

    def test_json_simplified_types(self):
        json = {
            'tup': (1, 2, 3)
        }
        self.EmptyModel(json).save()
        self.connection.fsync()
        json_out = self.EmptyModel.collection.find_one()
        assert isinstance(json_out.tup, list)

    def test_json_unsupported_types(self):
        json = {
            'set': {1, 2, 3}
        }
        instance = self.EmptyModel(json)
        self.assertRaises(pymongo.errors.InvalidDocument, instance.save)


class TestModelCollection(unittest.TestCase):

    def setUp(self):
        self.connection = pymongo.MongoClient()
        self.database_name = 'kale_testing_database'

        class EmptyModel(kale.Model):
            _database = self.connection[self.database_name]
            _collection_name = 'empty_models'

        self.EmptyModel = EmptyModel

    def tearDown(self):
        self.connection.drop_database(self.database_name)

    def test_find_one_type(self):
        self.EmptyModel().save()
        self.connection.fsync()
        out = self.EmptyModel.collection.find_one()
        assert isinstance(out, self.EmptyModel)

    def test_find_type(self):
        self.EmptyModel().save()
        self.connection.fsync()
        out = self.EmptyModel.collection.find()[0]
        assert isinstance(out, self.EmptyModel)

    def test_raw_collection(self):
        self.EmptyModel().save()
        self.connection.fsync()
        out = self.EmptyModel.collection.raw().find_one()
        assert isinstance(out, dict)
        assert not isinstance(out, self.EmptyModel)


if __name__ == '__main__':
    unittest.main()
