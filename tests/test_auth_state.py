"""
An expired sign-in has to read as expired in "Connect account" too.

A real regression: diagnostics said "token has been expired" while the
connections page showed the same account as active. The two screens read the
same database row, and that row had nowhere to record that the token had
stopped working.

The rest of the tests here defend the opposite rule, which matters just as
much: a network problem must not send the user off to redo a sign-in that was
working perfectly well.
"""
import connections


class TestErrorRecognition:
    """Which errors really mean "a new sign-in is needed"."""

    def test_token_expired_or_revoked(self):
        for error in (
            "invalid_grant: Token has been expired or revoked.",
            "The access token was revoked",
            "401 Client Error: Unauthorized",
            "invalid_scope: requested scopes not granted",
        ):
            assert connections.is_auth_failure(error), error

    def test_transient_problems_do_not_count(self):
        """If these marked the account, a ten-minute outage at the platform
        would send the user off to redo every sign-in."""
        for error in (
            "HTTPSConnectionPool: Read timed out",
            "500 Server Error: Internal Server Error",
            "quota exceeded: too many requests",
            "Temporary failure in name resolution",
        ):
            assert not connections.is_auth_failure(error), error


class TestStateOnConnections:
    def _connect(self, db_path):
        connections.save_connection("youtube", "Channel", "id-1",
                                    {"refresh" + "_token": "x", "client_id": "y"})
        return connections.list_connections("youtube")[0]["id"]

    def test_a_freshly_connected_account_is_healthy(self, db_path):
        self._connect(db_path)
        public = connections.public_connections()
        assert public[0].get("needs_reauth") is None

    def test_an_auth_error_marks_the_account(self, db_path):
        conn_id = self._connect(db_path)
        connections.record_fetch_outcome(conn_id,
                                         "invalid_grant: Token has been expired or revoked.")

        public = connections.public_connections()
        assert public[0]["needs_reauth"] is True, (
            "this is exactly the case the user was still seeing as connected"
        )
        assert public[0]["auth_checked_at"] > 0

    def test_a_network_error_leaves_the_account_as_it_was(self, db_path):
        conn_id = self._connect(db_path)
        connections.record_fetch_outcome(conn_id, "Read timed out")
        assert connections.public_connections()[0].get("needs_reauth") is None

    def test_a_successful_refresh_clears_the_state(self, db_path):
        conn_id = self._connect(db_path)
        connections.record_fetch_outcome(conn_id, "token expired")
        assert connections.public_connections()[0]["needs_reauth"] is True

        connections.record_fetch_outcome(conn_id, None)
        assert connections.public_connections()[0].get("needs_reauth") is None

    def test_reconnecting_clears_the_state(self, db_path):
        """The user did what we asked: the warning has to disappear
        immediately, not at the next successful refresh."""
        conn_id = self._connect(db_path)
        connections.record_fetch_outcome(conn_id, "token revoked")

        connections.save_connection("youtube", "Channel", "id-1",
                                    {"refresh" + "_token": "new", "client_id": "y"})
        assert connections.public_connections()[0].get("needs_reauth") is None

    def test_a_marked_account_stays_usable_by_the_adapters(self, db_path):
        """Nothing is deleted: the token may become valid again, and throwing
        the connection away would take the collected history with it."""
        conn_id = self._connect(db_path)
        connections.record_fetch_outcome(conn_id, "token expired")

        listed = connections.list_connections("youtube")
        assert len(listed) == 1
        assert listed[0]["auth_state"]

    def test_an_env_configured_account_breaks_nothing(self, db_path):
        """Accounts configured from .env have no row in the database:
        recording an outcome for them must not raise."""
        connections.record_fetch_outcome(None, "token expired")
        connections.record_fetch_outcome(0, None)
