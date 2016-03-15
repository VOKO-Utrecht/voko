from django.test import TransactionTestCase
import mock
from accounts.tests.factories import VokoUserFactory


class VokoTestCase(TransactionTestCase):
    def patch(self, to_patch):
        patcher = mock.patch(to_patch)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def login(self):
        self.user = VokoUserFactory.create()
        self.user.set_password('secret')
        self.user.is_active = True
        self.user.save()
        self.client.login(username=self.user.email, password='secret')

    def logout(self):
        self.client.logout()

    def assertMsgInResponse(self, response, msg):
        if response.context is None:
            raise AssertionError("Response context is None!")

        messages = list(response.context['messages'])
        if any([str(m) == msg for m in messages]):
            return True

        raise AssertionError("Message '%s' not found in response. Messages found: '%s'" %
                             (msg, ', '.join([str(m) for m in messages])))
