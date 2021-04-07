"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows
from sqlalchemy import exc

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']
# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()
        

        user1 = User.signup("testuser", "test@test.com", "HASHED_PASSWORD", None)
        user1_id = 1
        user1.id = user1_id

        user2 = User.signup("testuser2", "test2@test.com", "HASHED_PASSWORD2", None)
        user2_id = 2
        user2.id = user2_id

        
        db.session.commit()

        u1 = User.query.get(user1_id)
        u2 = User.query.get(user2_id)

        self.u1 = u1
        self.u2 = u2

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res
       

    def test_user_model(self):
        """Does basic model work?"""
       
        # User should have no messages & no followers
        self.assertEqual(len(self.u1.messages), 0)
        self.assertEqual(len(self.u1.followers), 0)

    def test_user_repr(self):
        '''does the repr display what is expected?'''
        
        self.assertEqual(repr(self.u1), f'<User #1: testuser, test@test.com>')

    def test_follow_functionality(self):
        '''does the follow and unfollow functions work correctly?'''
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u1.following), 1)
        self.assertEqual(len(self.u2.followers), 1)
        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))
        self.assertTrue(self.u2.is_followed_by(self.u1))
        self.assertFalse(self.u1.is_followed_by(self.u2))

    
    def test_failed_user(self):
        '''test to make sure it doesn't create a user if username, email, or password are not passed thru correctly'''
        
        user3 = User.signup(None, "test@test.com", "password", None)
        uid = 3
        user3.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

        db.session.rollback()

        user4 = User.signup("testtest", None, "password", None)
        uid = 4
        user4.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

        self.assertRaises(ValueError, User.signup, "testtest", "email@email.com", "", None)
        self.assertRaises(ValueError, User.signup, "testtest", "email@email.com", None, None)
        

    def test_authentication(self):
        '''test the authentication of an existing user, testing with a wrong username, and testing with wrong password'''
        u = User.authenticate('testuser', 'HASHED_PASSWORD')
        self.assertEqual(u.id, self.u1.id)

        self.assertFalse(User.authenticate('testuserwrong', 'HASHED_PASSWORD'))
        self.assertFalse(User.authenticate('testuser', 'WRONG_PASSWORD'))