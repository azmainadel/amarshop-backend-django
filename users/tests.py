import re

from django.core import mail
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AuthFlowTest(APITestCase):
    def setUp(self):
        self.client.post('/api/users/register/', {'email': 'a@x.com', 'password': 'Pass12345!'}, format='json')
        self.client.post('/api/users/register/', {'email': 'b@x.com', 'password': 'Pass12345!'}, format='json')

    def login(self, email='a@x.com', password='Pass12345!'):
        return self.client.post('/api/users/login/', {'email': email, 'password': password}, format='json')

    def test_register_two_users(self):
        self.assertEqual(User.objects.count(), 2)

    def test_logout_blacklists_refresh_token(self):
        tokens = self.login().data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}")

        response = self.client.post('/api/users/logout/', {'refresh_token': tokens['refresh_token']}, format='json')
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        refresh = self.client.post('/api/users/logout/', {'refresh_token': tokens['refresh_token']}, format='json')
        self.assertEqual(refresh.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_rejects_another_users_token(self):
        own = self.login().data
        other = self.login('b@x.com').data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {own['access_token']}")

        response = self.client.post('/api/users/logout/', {'refresh_token': other['refresh_token']}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_requires_auth(self):
        response = self.client.post('/api/users/logout/', {'refresh_token': 'x'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_password_reset_flow(self):
        response = self.client.post('/api/users/password-reset/', {'email': 'a@x.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)

        uid, token = re.search(r'uid=([^&\s]+)&token=(\S+)', mail.outbox[0].body).groups()
        confirm = self.client.post('/api/users/password-reset/confirm/',
                                   {'uid': uid, 'token': token, 'new_password': 'NewPass987!'}, format='json')
        self.assertEqual(confirm.status_code, status.HTTP_200_OK)
        self.assertEqual(self.login(password='NewPass987!').status_code, status.HTTP_200_OK)
        self.assertEqual(self.login().status_code, status.HTTP_401_UNAUTHORIZED)

        reused = self.client.post('/api/users/password-reset/confirm/',
                                  {'uid': uid, 'token': token, 'new_password': 'Other9876!'}, format='json')
        self.assertEqual(reused.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_unknown_email_looks_the_same(self):
        response = self.client.post('/api/users/password-reset/', {'email': 'nobody@x.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_rejects_weak_password(self):
        self.client.post('/api/users/password-reset/', {'email': 'a@x.com'}, format='json')
        uid, token = re.search(r'uid=([^&\s]+)&token=(\S+)', mail.outbox[0].body).groups()
        response = self.client.post('/api/users/password-reset/confirm/',
                                    {'uid': uid, 'token': token, 'new_password': '123'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', response.data)
