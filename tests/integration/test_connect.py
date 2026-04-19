"""
Integration test: connect / disconnect lifecycle against a real server.

Regression coverage for the class of bug where ``MMSClient.connect``
compared SWIG's ``(None, error_code)`` tuple return to an int error
constant. That bug was invisible to every mocked test in
``tests/test_mms.py`` because the mocks returned bare ints, not tuples.
"""

from pyiec61850.mms import MMSClient, ConnectionFailedError

from ._fixture import IntegrationServerCase


class TestConnect(IntegrationServerCase):
    """Connection lifecycle tests.

    These tests manage their own MMSClient instances, so we skip the
    shared setUp/tearDown client.
    """

    def setUp(self) -> None:
        # Override: these tests create their own clients.
        pass

    def tearDown(self) -> None:
        pass

    def test_connect_with_kwargs_in_constructor(self):
        """MMSClient(host, port) + context manager is the blessed API form."""
        with MMSClient(self.host, self.port) as client:
            self.assertTrue(client.is_connected)
        self.assertFalse(client.is_connected)

    def test_connect_explicit_call_still_works(self):
        """Backwards-compat path: empty ctor + explicit .connect()."""
        client = MMSClient()
        try:
            client.connect(self.host, self.port)
            self.assertTrue(client.is_connected)
        finally:
            client.disconnect()
        self.assertFalse(client.is_connected)

    def test_connect_to_wrong_port_raises(self):
        """Connecting to a closed port must raise ConnectionFailedError,
        not silently succeed or raise TypeError from a tuple comparison."""
        with self.assertRaises(ConnectionFailedError):
            MMSClient().connect(self.host, self.port + 31337, timeout=1000)

    def test_double_connect_disconnects_first(self):
        """Calling connect() twice must not leak the first connection."""
        client = MMSClient()
        try:
            client.connect(self.host, self.port)
            self.assertTrue(client.is_connected)
            # Second connect to the same server — must not raise.
            client.connect(self.host, self.port)
            self.assertTrue(client.is_connected)
        finally:
            client.disconnect()

    def test_disconnect_when_never_connected_is_safe(self):
        """disconnect() on a fresh client must not raise."""
        client = MMSClient()
        client.disconnect()  # should be a no-op
        self.assertFalse(client.is_connected)

    def test_connect_without_host_raises_valueerror(self):
        """connect() with no host anywhere must raise ValueError."""
        with self.assertRaises(ValueError):
            MMSClient().connect()

    def test_get_server_identity_after_connect(self):
        """A trivial MMS round-trip — proves the association completed,
        not just that TCP connected."""
        with MMSClient(self.host, self.port) as client:
            identity = client.get_server_identity()
            self.assertIsNotNone(identity)
            # The identity object must have all three fields. The basic_io
            # server may return None for all of them — that's fine, the
            # important thing is the round-trip didn't crash.
            self.assertTrue(hasattr(identity, "vendor"))
            self.assertTrue(hasattr(identity, "model"))
            self.assertTrue(hasattr(identity, "revision"))
