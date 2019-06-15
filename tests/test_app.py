import unittest

from werkzeug.security import check_password_hash, generate_password_hash

from csgobeans import create_app
from csgobeans import ctx


class AppTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            'TESTING': True,
            'DATABASE_FILE': 'test.sqlite'
        })
        self.client = self.app.test_client()

        self.username = "tester"
        self.password = "password"

        with self.app.app_context():
            db = ctx.get_db()
            db.initialize_from_schema()
            db.populate_beans_from_file()
            db.register_user(self.username, self.password)
            user_id = db.check_username_and_password(
                self.username, self.password)
            self.user_id = user_id


class TestCtx(AppTest):
    def test_get_db(self):
        with self.app.app_context():
            self.assertIs(ctx.get_db(), ctx.get_db())
            beans = ctx.get_db().list_beans()
            self.assertEqual('Jelly', beans[0][1].name)

    def test_teardown_db(self):
        db = None
        with self.app.app_context():
            db = ctx.get_db()
            self.assertFalse(db.closed())
        self.assertTrue(db.closed())

    def test_get_user_id(self):
        with self.client:
            self.client.get("/")

            self.assertEqual(None, ctx.get_user_id())
            ctx.set_user_id(self.user_id)
            self.assertEqual(self.user_id, ctx.get_user_id())
            ctx.clear_session()
            self.assertEqual(None, ctx.get_user_id())

    def test_get_username(self):
        with self.client:
            self.client.get("/")

            self.assertEqual(None, ctx.get_username())

            ctx.set_user_id(self.user_id)
            self.assertEqual(self.username, ctx.get_username())
            self.assertIs(ctx.get_username(), ctx.get_username())

            ctx.clear_session()
            self.assertEqual(None, ctx.get_username())


class TestRoot(AppTest):
    def test_index(self):
        response = self.client.get("/")
        self.assertEqual(200, response.status_code)

        with self.app.app_context():
            db = ctx.get_db()
            beans = db.list_beans()
            data = response.get_data().decode('utf-8')
            for bean_id, bean in beans:
                self.assertIn(bean.name, data)


class TestAuth(AppTest):
    def test_register(self):
        response = self.client.get("/register")
        self.assertEqual(200, response.status_code)

        response = self.client.post(
            "/register",
            data={
                "username": self.username + '2',
                "password": self.password
            },
            follow_redirects=True)
        self.assertEqual(200, response.status_code)

        with self.app.app_context():
            db = ctx.get_db()
            self.assertIsNot(
                None,
                db.check_username_and_password(
                    self.username + '2',
                    self.password))

    def test_login_logout(self):
        response = self.client.post(
            "/login",
            data={
                "username": self.username + 'x',
                "password": self.password
            },
            follow_redirects=True)
        self.assertEqual(200, response.status_code)
        self.assertIn(
            "Incorrect username or password",
            response.get_data().decode('utf-8'))

        response = self.client.post(
            "/login",
            data={
                "username": self.username,
                "password": self.password + 'x'
            },
            follow_redirects=True)
        self.assertEqual(200, response.status_code)
        self.assertIn(
            "Incorrect username or password",
            response.get_data().decode('utf-8'))

        response = self.client.post(
            "/login",
            data={
                "username": self.username,
                "password": self.password
            },
            follow_redirects=True)

        self.assertEqual(200, response.status_code)
        self.assertIn("Logged in as", response.get_data().decode('utf-8'))

        response = self.client.post("/logout", follow_redirects=True)
        self.assertEqual(200, response.status_code)
        self.assertIn("Logged out", response.get_data().decode('utf-8'))
