from pymongo import MongoClient
from kale import Model

def super_insecure_hash(to_hash):
    hashed = "".join(str(ord(c)) for c in to_hash)
    return hashed

class User(Model):
    _collection_name = 'users'
    _database = MongoClient().test_database
    
    def __init__(self, username, password):
        self.username = username
        self.set_password(password)
    
    def set_password(self, password):
        pw_hash = super_insecure_hash(password)
        self.pw_hash = pw_hash
    
    def check_password(self, password_challenge):
        hashed_challenge = super_insecure_hash(password_challenge)
        return hashed_challenge == self.pw_hash  # true if they match

User.collection.drop()

alice = User('alice', 'abc123')
alice.save()
alice
del alice

def login(username, password):
    requested_user = User.collection.find_one({'username': username})
    if requested_user.check_password(password):
        return requested_user
    else:
        return 'Bad login!'

faker = login('alice', '123456')
faker

real_alice = login('alice', 'abc123')
real_alice
real_alice.set_password('password')
real_alice.save()
