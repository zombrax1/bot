import unittest
from unittest.mock import AsyncMock, Mock, patch

from cogs import gift_redemption


class GiftRedemptionTests(unittest.IsolatedAsyncioTestCase):
    def test_only_definitive_account_failures_are_ignored(self):
        self.assertTrue(gift_redemption.should_ignore_gift_status("ROLE_NOT_EXIST"))
        self.assertTrue(gift_redemption.should_ignore_gift_status("STATE_MISMATCH"))
        self.assertFalse(gift_redemption.should_ignore_gift_status("TIMEOUT_RETRY"))
        self.assertFalse(gift_redemption.should_ignore_gift_status("ERROR"))

    def test_wrong_state_users_are_listed_with_fids(self):
        users = gift_redemption._wrong_state_users(
            {
                "100": ("Alice", "Wrong state on file", 1),
                "200": ("Bob", "Connection failed", 1),
            }
        )

        self.assertEqual(len(users), 1)
        self.assertIn("Alice", users[0])
        self.assertIn("(100)", users[0])

    async def test_state_mismatch_does_not_start_blocking_state_scan(self):
        cog = Mock()
        cog.clean_gift_code.side_effect = str.strip
        cog.get_test_fid.return_value = "test-fid"
        cog.cursor.fetchone.return_value = None
        cog.retry_config = None
        cog.wos_giftcode_url = "https://example.invalid/gift"
        cog.wos_giftcode_redemption_url = "https://example.invalid"
        cog.processing_stats = {
            "total_fids_processed": 0,
            "total_processing_time": 0.0,
        }
        session = Mock()

        with (
            patch.object(gift_redemption.requests, "Session", return_value=session),
            patch.object(gift_redemption, "get_user_kid", AsyncMock(return_value=1944)),
            patch.object(
                gift_redemption,
                "redeem_giftcode_once",
                AsyncMock(return_value="STATE_MISMATCH"),
            ) as redeem,
            patch(
                "cogs.gift_state_resolver.resolve_state",
                AsyncMock(side_effect=AssertionError("state scan must not run during claims")),
            ),
        ):
            status = await gift_redemption.claim_giftcode_rewards_wos(
                cog, "172166138", " FB4Million "
            )

        self.assertEqual(status, "STATE_MISMATCH")
        redeem.assert_awaited_once()
        session.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
