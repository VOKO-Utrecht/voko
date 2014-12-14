from django.test import TransactionTestCase
import mock


class VokoTestCase(TransactionTestCase):
    def patch(self, to_patch):
        patcher = mock.patch(to_patch)
        self.addCleanup(patcher.stop)
        return patcher.start()

