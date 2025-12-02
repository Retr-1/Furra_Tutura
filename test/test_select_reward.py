# test/test_select_reward.py

from __future__ import annotations

import pytest
from typing import cast, Dict

from terra_futura.select_reward import SelectReward, RewardState
from terra_futura.simple_types import Resource, GridPosition
from terra_futura.interfaces import InterfaceCard, PlayerInterface


# ------------------------------------------------------------------ #
# Test doubles                                                       #
# ------------------------------------------------------------------ #

class DummyCard:
    """Minimal card with a 'state()' method to satisfy SelectReward logic."""
    def __init__(self, state_value: int) -> None:
        self._state_value = state_value

    def state(self) -> int:
        return self._state_value


class DummyGrid:
    """Minimal grid with a 'getCard(GridPosition)' method."""
    def __init__(self, cards: Dict[GridPosition, InterfaceCard] | None = None) -> None:
        self._cards: Dict[GridPosition, InterfaceCard] = cards or {}

    def getCard(self, pos: GridPosition) -> InterfaceCard | None:
        return self._cards.get(pos)


class DummyPlayer:
    """Minimal player with a 'getGrid()' method."""
    def __init__(self, grid: DummyGrid) -> None:
        self._grid = grid

    def getGrid(self) -> DummyGrid:
        return self._grid


def _two_resources() -> tuple[Resource, Resource]:
    """Helper to return two distinct Resource enum members."""
    return Resource.YELLOW, Resource.RED


# ------------------------------------------------------------------ #
# Tests                                                              #
# ------------------------------------------------------------------ #

def test_initial_state_is_idle_and_empty() -> None:
    sr = SelectReward()

    assert sr.player is None
    assert sr.selection == []
    assert sr.state() == RewardState.IDLE


def test_set_reward_raises_if_player_has_no_such_card() -> None:
    sr = SelectReward()
    r1, _ = _two_resources()

    # Grid with no cards at all
    empty_grid = DummyGrid()
    player = DummyPlayer(empty_grid)
    card = DummyCard(state_value=1)

    with pytest.raises(ValueError):
        sr.setReward(
            player=cast(PlayerInterface, player),
            card=cast(InterfaceCard, card),
            reward=[r1],
        )


def test_set_reward_sets_player_selection_and_pending_state_when_card_is_on_grid() -> None:
    sr = SelectReward()
    r1, r2 = _two_resources()
    rewards = [r1, r2]

    card = DummyCard(state_value=42)
    # Place the card at (0, 0) so the search in setReward finds it
    grid_cards: Dict[GridPosition, InterfaceCard] = {
        GridPosition(0, 0): cast(InterfaceCard, card),
    }
    grid = DummyGrid(grid_cards)
    player = DummyPlayer(grid)

    sr.setReward(
        player=cast(PlayerInterface, player),
        card=cast(InterfaceCard, card),
        reward=rewards,
    )

    # basic attributes
    assert sr.player is not None
    assert sr.selection == [r1, r2]
    assert sr.state() == RewardState.PENDING

    # selection must be a copy, not the same list instance
    assert sr.selection is not rewards

    # mutating the original list must not affect internal selection
    rewards.append(Resource.MONEY)
    assert sr.selection == [r1, r2]


def test_can_select_reward_only_when_pending_and_resource_in_selection() -> None:
    sr = SelectReward()
    r1, r2 = _two_resources()

    # idle state: cannot select anything
    assert sr.state() == RewardState.IDLE
    assert sr.canSelectReward(r1) is False

    # Prepare player with matching card on grid
    card = DummyCard(state_value=7)
    grid_cards: Dict[GridPosition, InterfaceCard] = {
        GridPosition(1, 1): cast(InterfaceCard, card),
    }
    grid = DummyGrid(grid_cards)
    player = DummyPlayer(grid)

    sr.setReward(
        player=cast(PlayerInterface, player),
        card=cast(InterfaceCard, card),
        reward=[r1],
    )

    # pending: allowed for r1, not for r2
    assert sr.state() == RewardState.PENDING
    assert sr.canSelectReward(r1) is True
    assert sr.canSelectReward(r2) is False

    # after a valid selection, state = SELECTED, no further selection allowed
    sr.selectReward(r1)
    assert sr.state() == RewardState.SELECTED
    assert sr.canSelectReward(r1) is False
    assert sr.canSelectReward(r2) is False


def test_select_reward_success_updates_state_and_selection() -> None:
    sr = SelectReward()
    r1, r2 = _two_resources()

    card = DummyCard(state_value=99)
    grid_cards: Dict[GridPosition, InterfaceCard] = {
        GridPosition(-1, -1): cast(InterfaceCard, card),
    }
    grid = DummyGrid(grid_cards)
    player = DummyPlayer(grid)

    sr.setReward(
        player=cast(PlayerInterface, player),
        card=cast(InterfaceCard, card),
        reward=[r1, r2],
    )

    sr.selectReward(r2)

    # only the chosen resource should remain
    assert sr.selection == [r2]
    assert sr.state() == RewardState.SELECTED


def test_select_reward_raises_if_resource_not_allowed() -> None:
    sr = SelectReward()
    r1, r2 = _two_resources()

    card = DummyCard(state_value=5)
    grid_cards: Dict[GridPosition, InterfaceCard] = {
        GridPosition(2, 0): cast(InterfaceCard, card),
    }
    grid = DummyGrid(grid_cards)
    player = DummyPlayer(grid)

    sr.setReward(
        player=cast(PlayerInterface, player),
        card=cast(InterfaceCard, card),
        reward=[r1],
    )

    with pytest.raises(ValueError):
        sr.selectReward(r2)


def test_select_reward_raises_if_not_pending() -> None:
    sr = SelectReward()
    r1 = Resource.YELLOW

    # initial state is IDLE
    with pytest.raises(ValueError):
        sr.selectReward(r1)

    # now move to PENDING then SELECTED
    card = DummyCard(state_value=123)
    grid_cards: Dict[GridPosition, InterfaceCard] = {
        GridPosition(0, 2): cast(InterfaceCard, card),
    }
    grid = DummyGrid(grid_cards)
    player = DummyPlayer(grid)

    sr.setReward(
        player=cast(PlayerInterface, player),
        card=cast(InterfaceCard, card),
        reward=[r1],
    )
    sr.selectReward(r1)
    assert sr.state() == RewardState.SELECTED

    # further selection attempts in SELECTED state must also raise
    with pytest.raises(ValueError):
        sr.selectReward(r1)
