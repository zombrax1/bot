from cogs.alliance_registration import valid_state


def test_registration_state_range():
    assert valid_state(1)
    assert valid_state(1755)
    assert valid_state(9999)
    assert not valid_state(0)
    assert not valid_state(10000)
