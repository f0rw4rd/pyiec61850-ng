"""
Integration test: set_request_timeout and max_pdu_size.

Both were added in the current changeset and have zero integration
coverage. They touch ``IedConnection_setRequestTimeout`` and
``MmsConnection_setLocalDetail`` — SWIG-wrapped C functions that could
easily mismatch argument types at the boundary.
"""

from pyiec61850.mms import MMSClient
from pyiec61850.mms.exceptions import NotConnectedError

from ._fixture import IntegrationServerCase, REF_MX_FLOAT


class TestSetRequestTimeout(IntegrationServerCase):
    def test_set_request_timeout_does_not_raise(self):
        """Setting a valid timeout must not raise."""
        self.client.set_request_timeout(15000)

    def test_read_still_works_after_timeout_change(self):
        """A round-trip after changing the timeout proves the connection
        is still healthy."""
        self.client.set_request_timeout(30000)
        value = self.client.read_value(REF_MX_FLOAT, fc="MX")
        self.assertIsInstance(value, (int, float))

    def test_set_request_timeout_before_connect_raises(self):
        client = MMSClient()
        with self.assertRaises(NotConnectedError):
            client.set_request_timeout(5000)


class TestMaxPduSize(IntegrationServerCase):
    """max_pdu_size is a connect-time parameter. We override setUp to
    manage our own client."""

    def setUp(self) -> None:
        # Don't use the shared client — we need custom connect params.
        pass

    def tearDown(self) -> None:
        pass

    def test_connect_with_custom_pdu_size(self):
        """Connecting with a non-default PDU size must succeed and
        produce a usable connection."""
        with MMSClient(self.host, self.port, max_pdu_size=32000) as client:
            self.assertTrue(client.is_connected)
            value = client.read_value(REF_MX_FLOAT, fc="MX")
            self.assertIsInstance(value, (int, float))

    def test_connect_with_default_pdu_size(self):
        """Connecting without specifying max_pdu_size (None) must also
        work — regression test for the 'if max_pdu_size is not None'
        guard in connect()."""
        with MMSClient(self.host, self.port) as client:
            self.assertTrue(client.is_connected)
            value = client.read_value(REF_MX_FLOAT, fc="MX")
            self.assertIsInstance(value, (int, float))

    def test_pdu_size_via_connect_kwarg(self):
        """max_pdu_size passed to connect() directly."""
        client = MMSClient()
        try:
            client.connect(self.host, self.port, max_pdu_size=16000)
            self.assertTrue(client.is_connected)
            value = client.read_value(REF_MX_FLOAT, fc="MX")
            self.assertIsInstance(value, (int, float))
        finally:
            client.disconnect()
