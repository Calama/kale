import unittest
import warnings
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

    def test_repr_doesnt_break(self):
        e = self.EmptyModel()
        print(repr(e))

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

    def test_unsaved_remove(self):
        instance = self.EmptyModel()
        instance.remove()

    def test_wronglevel_remove(self):
        instance = self.EmptyModel()
        with self.assertRaises(kale.WrongLevel):
            instance.remove({'_id': '1234'})

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
        try:
            assert isinstance(json_out.string, unicode)  # py2x
        except NameError:
            assert isinstance(json_out.string, str)  # py3
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
            'set': set([1, 2, 3])
        }
        instance = self.EmptyModel(json)
        with self.assertRaises(pymongo.errors.InvalidDocument):
            with warnings.catch_warnings(record=True):
                instance.save()

    def test_descriptor_getter(self):
        """should be moved to attrdict tests"""
        class DescModel(kale.Model):
            _database = self.connection[self.database_name]
            _collection_name = 'empty_models'

            @property
            def thing(self):
                return self.lalala

        d = DescModel()
        with self.assertRaises(AttributeError) as e:
            d.thing
        try:
            d.thing
        except AttributeError as e:
            self.assertNotEqual(str(e), 'AttributeError: thing')

    def test_attributeerror_propagates(self):
        """should be moved to attrdict tests"""
        class DescModel(kale.Model):
            _database = self.connection[self.database_name]
            _collection_name = 'empty_models'

            @property
            def thing(self):
                return self.lalala

        d = DescModel()
        with self.assertRaises(AttributeError) as e:
            d.thing
        try:
            d.thing
        except AttributeError as e:
            print(e)
            assert 'lalala' in str(e), 'wrong attribute error'

    def test_descriptor_setter(self):
        """should be moved to attrdict tests"""
        class DescModel(kale.Model):
            _database = self.connection[self.database_name]
            _collection_name = 'empty_models'

            def blah():
                def fget(self):
                    return None

                def fset(self, val):
                    self.described = val

                return locals()
            blah = property(**blah())
        d = DescModel()
        d.blah = 'hello'
        self.assertEqual(d.described, 'hello')

    def test_descriptor_deleter(self):
        """should be moved to attrdict tests"""
        class DescModel(kale.Model):
            _database = self.connection[self.database_name]
            _collection_name = 'empty_models'

            def blah():
                def fget(self):
                    pass

                def fset(self, val):
                    pass

                def fdel(self):
                    self.deleted = 'yeah'

                return locals()
            blah = property(**blah())
        d = DescModel()
        del d.blah
        self.assertEqual(d.deleted, 'yeah')

    def test_inherited_descriptior_setter(self):
        """should be move to AttrDict tests"""
        class DescModel(kale.Model):
            _database = self.connection[self.database_name]
            _collection_name = 'empty_models'

            def blah():
                def fget(self):
                    return None

                def fset(self, val):
                    self.described = val

                return locals()
            blah = property(**blah())

        class ExtendDescModel(DescModel):
            pass

        ed = ExtendDescModel()
        ed.blah = 'hello'
        self.assertEqual(ed.described, 'hello')

    def test_setting_models(self):
        a = self.EmptyModel()
        b = self.EmptyModel()
        a.b = b
        assert isinstance(a.b, type(b)), 'b is not a b'

    def test_aggressive_remove(self):
        a = self.EmptyModel()
        b = self.EmptyModel()
        b.save()
        a.b_id = b._id
        a_id = a.save()
        b.remove()
        a_in_db = self.EmptyModel.collection.find_one(a_id)
        assert a_in_db is not None, 'a was removed through b...'

    def test_is_saved(self):
        a = self.EmptyModel()
        assert a.is_in_db() is False, 'the model has not been saved...'
        a.save()
        assert a.is_in_db() is True, 'the model should be saved...'
        a.remove()
        assert a.is_in_db() is False, 'the model should be removed...'
        a.save()
        assert a.is_in_db() is True, 'the model should be re-saved...'

    def test_multiple_instances(self):
        a = self.EmptyModel()
        a.save()
        b = self.EmptyModel.collection.find_one()
        assert b is a, 'multiple instances of a document exist'

    def test_inserted_instances(self):
        a = self.EmptyModel()
        a.insert()
        b = self.EmptyModel.collection.find_one()
        self.assertIs(b, a, 'multiple instances of a document exist')

    def test_remove_saved_identity(self):
        a = self.EmptyModel()
        a_id = a.save()
        b = self.EmptyModel.collection.find_one()
        a.remove()
        self.assertFalse(b.is_in_db(), 'b should know it is not in the db')
        a_id2 = a.save()
        assert a_id2 != a_id, 'resaved document should have new id'
        self.assertIs(b, a, 'documents lost track of each other')

    def test_weakrefs_are_weak(self):
        a = self.EmptyModel()
        a.save()
        del a
        import gc
        gc.collect()
        self.assertFalse(self.EmptyModel._live_documents, 'document lived!')


class TestAttrDict(unittest.TestCase):

    def test_bad_multi_arg_update(self):
        ad = kale.AttrDict()
        with self.assertRaises(TypeError):
            ad.update({}, {})

    def test_set_default(self):
        ad = kale.AttrDict()
        ad.setdefault('a')
        self.assertEqual(ad['a'], None)
        ad.setdefault('b', 1)
        self.assertEqual(ad['b'], 1)

    def test_bad_delattr(self):
        ad = kale.AttrDict()
        with self.assertRaises(AttributeError):
            del ad.lalala

    def test_dict_cast(self):
        d = {}
        ad = kale.AttrDict(d)
        self.assertIs(type(ad), kale.AttrDict)

    def test_nested_dict_cast(self):
        d = {'a': {}}
        ad = kale.AttrDict(d)
        self.assertIs(type(ad.a), kale.AttrDict)

    def test_list_of_dicts_cast(self):
        d = {'a': [{}]}
        ad = kale.AttrDict(d)
        self.assertIs(type(ad.a[0]), kale.AttrDict)

    def test_interable_of_strings_regression(self):
        d = {'a': ['b']}
        ad = kale.AttrDict(d)


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

    def test_cursor_slice(self):
        for model in range(5):
            self.EmptyModel().save()
        self.connection.fsync()
        self.EmptyModel.collection.find()[2:4]

    def test_raw_collection(self):
        self.EmptyModel().save()
        self.connection.fsync()
        out = self.EmptyModel.collection.raw().find_one()
        assert isinstance(out, dict)
        assert not isinstance(out, self.EmptyModel)

    def test_sub_subclass_type(self):
        class SubSubModel(self.EmptyModel):
            _collection_name = 'test_subnode'
        _id = SubSubModel().save()
        loaded = SubSubModel.collection.find_one(_id)
        assert isinstance(loaded, SubSubModel),\
            'loaded subnode is not a subnode'
        SubSubModel.collection.drop()


class TestCollectionMethod(unittest.TestCase):

    def setUp(self):
        self.connection = pymongo.MongoClient()
        self.database_name = 'kale_testing_database'

    def tearDown(self):
        self.connection.drop_database(self.database_name)

    def test_collection_method(self):

        class MethodModel(kale.Model):
            _database = self.connection[self.database_name]
            _collection_name = 'empty_models'

            @kale.collectionmethod
            def sayhi(collection):
                return 'hello'

        self.assertEqual(MethodModel.sayhi(), 'hello')
        m = MethodModel()
        self.assertEqual(m.sayhi(), 'hello')



if __name__ == '__main__':
    unittest.main()
