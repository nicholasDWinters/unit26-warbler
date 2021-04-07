"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase
from models import db, connect_db, Message, User, Follows, Likes

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

class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",email="test@test.com",password="testuser",image_url=None)
        self.testuser2 = User.signup(username="testuser2",email="test@test2.com",password="testuser2",image_url=None)
        self.testuser.id = 1
        self.testuser2.id = 2
        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_all_users(self):
        '''does the page show users?'''
        resp = self.client.get('/users')
        html = resp.get_data(as_text=True)
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn('<p>@testuser</p>', html)


    def test_user_show(self):
        '''does the page show user details'''
        resp = self.client.get(f'/users/{self.testuser.id}')
        html = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('<h4 id="sidebar-username">@testuser</h4>', html)



    def test_show_following(self):
        '''can a non logged in user see following page? does it work if logged in?'''
        self.testuser.following.append(self.testuser2)
        db.session.commit()

        resp = self.client.get(f'/users/{self.testuser.id}/following', follow_redirects=True)
        html = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f'/users/{self.testuser.id}/following', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<a href="/users/1/following">1</a>', html)
            self.assertIn('<p>@testuser2</p>', html)


    def test_show_followers(self):
        '''can a non logged in user see followers page? does it work if logged in?'''
        self.testuser.following.append(self.testuser2)
        db.session.commit()

        resp = self.client.get(f'/users/{self.testuser2.id}/followers', follow_redirects=True)
        html = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 1

            resp = c.get(f'/users/2/followers', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<a href="/users/2/followers">1</a>', html)
            self.assertIn('<p>@testuser</p>', html)


    def test_add_followers(self):
        '''can a non logged in user add followers? can a logged in user add followers?'''
        resp = self.client.post('/users/follow/2', follow_redirects=True)
        html = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 1

            resp = c.post('/users/follow/2', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            user = User.query.get(1)
            self.assertEqual(len(user.following), 1)

    def test_remove_followers(self):
        '''can a non logged in user remove follower? can a logged in user remove followers?'''
        resp = self.client.post('/users/stop-following/2', follow_redirects=True)
        html = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 1

            resp1 = c.post('/users/follow/2', follow_redirects=True)
            user = User.query.get(1)
            self.assertEqual(len(user.following), 1)

            resp = c.post('/users/stop-following/2', follow_redirects=True)
            html = resp.get_data(as_text=True)
            user = User.query.get(1)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(user.following), 0)


    def test_show_likes(self):
        '''can a non logged in user see likes page? does it work if logged in?'''

        resp = self.client.get('/users/1/likes', follow_redirects=True)
        html = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 1

            m = Message(id=1, text="a test message", user_id = 2)
            db.session.add(m)
            db.session.commit()
            message = Message.query.get(1)
            user = User.query.get(1)
            user.likes.append(message)
            db.session.commit()

            resp = c.get('/users/1/likes', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<a href="/users/1/likes">1</a>', html)
            self.assertIn('a test message', html)
            self.assertIn('btn-primary', html)

    
    def test_add_remove_likes(self):
        '''can a non logged in user add likes? can a logged in user add likes? can they remove them as well?'''
        resp = self.client.post('/users/add_like/1', follow_redirects=True)
        html = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('<div class="alert alert-danger">Unauthorized action.</div>', html)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 1

            m = Message(id=1, text="a test message", user_id = 2)
            db.session.add(m)
            db.session.commit()
        

            resp = c.post('/users/add_like/1', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            user = User.query.get(1)
            self.assertEqual(len(user.likes), 1)

            resp = c.post('/users/add_like/1', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            user = User.query.get(1)
            self.assertEqual(len(user.likes), 0)

    def test_edit_profile_route(self):
        '''can a non user get to the edit form? does the user information show in the form correctly?'''
        resp = self.client.get('/users/profile', follow_redirects=True)
        html = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 1

            resp = c.get('/users/profile', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Edit Your Profile', html)
            self.assertIn('value="testuser"', html)




    