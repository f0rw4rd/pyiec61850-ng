"""
Integration test: GoosePublisher.start() against the real SWIG binding.

Regression for issue #20: CommParameters.dstAddress is a C ``uint8_t[6]``
array that SWIG exposes as an opaque ``unsigned char *`` — it does NOT support
Python item assignment, so the old ``dstAddress[i] = mac[i]`` loop raised
``TypeError: 'SwigPyObject' object does not support item assignment`` and
GOOSE publishing was completely broken. start() must use the binding's
``CommParameters_setDstAddress`` helper instead.

This needs the native extension and a loopback interface, but no server. A
MagicMock CommParameters *does* support item assignment, which is exactly why
the mocked unit tests never caught this — so it must run against the real
binding.
"""

import unittest

from pyiec61850.goose import GoosePublisher
from pyiec61850.goose.exceptions import PublishError

from ._fixture import _skip_reason


class TestGoosePublisherStart(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # GOOSE publishing needs the extension + an interface, not a container.
        reason = _skip_reason()
        if reason and "runtime" not in reason:
            raise unittest.SkipTest(reason)

    def _start_stop(self, pub: GoosePublisher) -> None:
        """Start then stop, tolerating environments without raw-socket perms.

        A PublishError (GoosePublisher_createEx returned NULL) is acceptable —
        the destination MAC is set *before* the publisher is created, so the
        issue-#20 code path has already run. A TypeError, however, means the
        regression is back and fails the test.
        """
        try:
            pub.start()
        except PublishError:
            return
        try:
            self.assertTrue(pub.is_running)
        finally:
            pub.stop()

    def test_start_default_mac_no_typeerror(self):
        pub = GoosePublisher("lo")
        pub.set_go_cb_ref("simpleIOGenericIO/LLN0$GO$gcbAnalogValues")
        pub.set_app_id(0x1000)
        self._start_stop(pub)

    def test_start_custom_mac_no_typeerror(self):
        pub = GoosePublisher("lo")
        pub.set_dst_mac(b"\x01\x0c\xcd\x01\x00\x2a")
        pub.set_go_cb_ref("simpleIOGenericIO/LLN0$GO$gcbAnalogValues")
        self._start_stop(pub)


if __name__ == "__main__":
    unittest.main()
