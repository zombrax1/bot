import asyncio

from cogs.alliance_id_channel import AllianceIDChannel


class _Object:
    def __init__(self, **values):
        self.__dict__.update(values)


def test_state_prompt_consumes_reply_and_clears_pending():
    async def run():
        answer = _Object(
            content="1755",
            author=_Object(id=7, bot=False),
            channel=_Object(id=9),
        )

        class Bot:
            async def wait_for(self, event, timeout, check):
                assert event == "message"
                assert timeout == 60
                assert check(answer)
                return answer

        async def reply(*args, **kwargs):
            return None

        message = _Object(
            guild=_Object(id=5),
            channel=_Object(id=9),
            author=_Object(id=7),
            reply=reply,
        )
        cog = AllianceIDChannel.__new__(AllianceIDChannel)
        cog.bot = Bot()
        cog.pending_state_answers = set()

        assert await cog._ask_for_state(message, 123456) == 1755
        assert cog.pending_state_answers == set()

    asyncio.run(run())
