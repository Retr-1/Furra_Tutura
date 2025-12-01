# test/test_select_reward.py

import pytest
from typing import cast

from terra_futura.select_reward import SelectReward, RewardState
from terra_futura.simple_types import Resource
from terra_futura.interfaces import InterfaceCard


def _two_resources() -> tuple[Resource, Resource]:
    """Helper to return two distinct Resource enum members."""
    return Resource.YELLOW, Resource.RED


def test_initial_state_is_idle_and_empty():
    sr = SelectReward()

    assert sr.player is None
    assert sr.selection == []
    assert sr.state() == RewardState.IDLE


def test_set_reward_sets_player_selection_and_pending_state():
    sr = SelectReward()
    r1, r2 = _two_resources()
    rewards = [r1, r2]

    dummy_card = cast(InterfaceCard, object())

    sr.setReward(player=1, card=dummy_card, reward=rewards)

    # basic attributes
    assert sr.player == 1
    assert sr.selection == [r1, r2]
    assert sr.state() == RewardState.PENDING

    # selection must be a copy, not the same list instance
    assert sr.selection is not rewards

    # mutating the original list must not affect internal selection
    rewards.append(Resource.MONEY)
    assert sr.selection == [r1, r2]


def test_can_select_reward_only_when_pending_and_resource_in_selection():
    sr = SelectReward()
    r1, r2 = _two_resources()

    # idle state: cannot select anything
    assert sr.state() == RewardState.IDLE
    assert sr.canSelectReward(r1) is False

    dummy_card = cast(InterfaceCard, object())
    sr.setReward(player=1, card=dummy_card, reward=[r1])

    # pending: allowed for r1, not for r2
    assert sr.state() == RewardState.PENDING
    assert sr.canSelectReward(r1) is True
    assert sr.canSelectReward(r2) is False

    # after a valid selection, state = SELECTED, no further selection allowed
    sr.selectReward(r1)
    assert sr.state() == RewardState.SELECTED
    assert sr.canSelectReward(r1) is False
    assert sr.canSelectReward(r2) is False


def test_select_reward_success_updates_state_and_selection():
    sr = SelectReward()
    r1, r2 = _two_resources()
    dummy_card = cast(InterfaceCard, object())
    sr.setReward(player=1, card=dummy_card, reward=[r1, r2])

    sr.selectReward(r2)

    # only the chosen resource should remain
    assert sr.selection == [r2]
    assert sr.state() == RewardState.SELECTED


def test_select_reward_raises_if_resource_not_allowed():
    sr = SelectReward()
    r1, r2 = _two_resources()
    dummy_card = cast(InterfaceCard, object())
    sr.setReward(player=1, card=dummy_card, reward=[r1])

    with pytest.raises(ValueError):
        sr.selectReward(r2)


def test_select_reward_raises_if_not_pending():
    sr = SelectReward()
    r1 = Resource.YELLOW

    # initial state is IDLE
    with pytest.raises(ValueError):
        sr.selectReward(r1)

    # go to PENDING and then SELECTED
    dummy_card = cast(InterfaceCard, object())
    sr.setReward(player=1, card=dummy_card, reward=[r1])
    sr.selectReward(r1)
    assert sr.state() == RewardState.SELECTED

    # further selection attempts in SELECTED state must also raise
    with pytest.raises(ValueError):
        sr.selectReward(r1)
