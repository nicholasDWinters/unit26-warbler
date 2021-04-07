"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase
from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']
app.config['TESTING'] = True

class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def test_add_message(self):
        """Can a logged in user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_noUser_add_message(self):
        '''can a non logged in user add a message?'''
        with self.client as c:

            resp = c.get('/messages/new', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)

            resp1 = c.post("/messages/new", data={"text": "Hello"})
            html1 = resp.get_data(as_text=True)
            self.assertEqual(resp1.status_code, 302)
            


    def test_delete_message(self):
        '''can logged in user delete a message?'''
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

        resp = c.post("/messages/new", data={"text": "Hello"})
        msg = Message.query.one()
        newResp = c.post(f'/messages/{msg.id}/delete')

        self.assertEqual(resp.status_code, 302)
        user = User.query.get(sess[CURR_USER_KEY])

        self.assertEqual(len(user.messages), 0)


    def test_noUser_delete_message(self):
        '''can a non logged in user delete a message?'''

        msg = Message(id=2, text = 'Another test', user_id = self.testuser.id)
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            
            resp1 = c.post(f'/messages/2/delete', follow_redirects=True)
            html = resp1.get_data(as_text=True)
            self.assertEqual(resp1.status_code, 200)
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)


    def test_unauthorized_message_delete(self):

        # A second user that will try to delete the message
        u = User.signup(username="user2", email="test@test2.com", password="password", image_url=None)
        u.id = 2

        #Message is owned by testuser
        m = Message(id=5, text="a test message", user_id = self.testuser.id
        )
        db.session.add_all([u, m])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 2

            resp = c.post("/messages/5/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)


    def test_show_message(self):
        '''can a user see the message show page?'''
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

        resp1 = c.post("/messages/new", data={"text": "Hello"})
        msg = Message.query.one()
        resp = c.get(f'/messages/{msg.id}')
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('<p class="single-message">Hello</p>', html)

        
