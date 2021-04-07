"""Message model tests."""

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


class MessageModelTestCase(TestCase):
    """Tests for message model"""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()
        

        user1 = User.signup("testuser", "test@test.com", "HASHED_PASSWORD", None)
        user1_id = 1
        user1.id = user1_id

        db.session.commit()

        u1 = User.query.get(user1_id)

        self.u1 = u1
        

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res
       

    def test_check_messages(self):
        '''check to see if the messages were created in the setup funcion, and correctly associated with the user'''

        message1 = Message(text='Message 1 text', user_id = 1)
        message1_id = 1
        message1.id = message1_id
        
        db.session.add(message1)
        db.session.commit()

        m = Message.query.get(1)

        self.assertEqual(m.user_id, self.u1.id)
        self.assertEqual(m.text, 'Message 1 text')
        self.assertEqual(len(self.u1.messages), 1)
        self.assertEqual(str(m.user), repr(self.u1))