from __future__ import annotations

from typing import List

import pytest

from terra_futura.grid import Grid
from terra_futura.simple_types import GridPosition
from terra_futura.interfaces import InterfaceCard


class DummyCard(InterfaceCard):
    """Simple test double for InterfaceCard."""

    def __repr__(self) -> str:
        return "DummyCard()"


# ---------------------------------------------------------------------------
# Placement rules
# ---------------------------------------------------------------------------

def test_first_card_can_be_placed_anywhere() -> None:
    grid = Grid()
    card = DummyCard()

    pos1 = GridPosition(x=0, y=0)
    pos2 = GridPosition(x=2, y=-2)

    assert grid.canPutCard(pos1) is True
    assert grid.canPutCard(pos2) is True

    # Actually place one to be sure putCard works on empty grid
    grid.putCard(pos1, card)
    assert grid.getCard(pos1) is card

def test_cannot_place_two_cards_far_apart() -> None:
    grid = Grid()
    card = DummyCard()

    pos1 = GridPosition(x=-2, y=0)
    pos2 = GridPosition(x=2, y=-2)

    grid.putCard(pos1, card)
    assert grid.canPutCard(pos2) is False


def test_cannot_put_card_on_occupied_coordinate() -> None:
    grid = Grid()
    card1 = DummyCard()
    card2 = DummyCard()
    pos = GridPosition(x=1, y=1)

    grid.putCard(pos, card1)

    # Same coordinate should not be allowed
    assert grid.canPutCard(pos) is False

    # And putCard should raise
    with pytest.raises(ValueError):
        grid.putCard(pos, card2)


def test_can_have_up_to_three_cards_in_same_row() -> None:
    """
    According to rules, territory is 3×3 cards.
    Having exactly 3 cards in one row is legal; the 4th would break 3×3.
    """
    grid = Grid()
    c1 = DummyCard()
    c2 = DummyCard()
    c3 = DummyCard()

    # All in row y = 0, different x
    pos1 = GridPosition(x=0, y=0)
    pos2 = GridPosition(x=1, y=0)
    pos3 = GridPosition(x=2, y=0)

    grid.putCard(pos1, c1)
    grid.putCard(pos2, c2)

    # This is the critical one – must be allowed by canPutCard
    assert grid.canPutCard(pos3) is True
    grid.putCard(pos3, c3)


def test_fourth_card_in_same_row_is_not_allowed() -> None:
    grid = Grid()
    cards: List[DummyCard] = [DummyCard() for _ in range(4)]

    # Fill positions (0,0), (1,0), (2,0)
    positions = [
        GridPosition(x=0, y=0),
        GridPosition(x=1, y=0),
        GridPosition(x=2, y=0),
    ]

    for card, pos in zip(cards[:3], positions):
        grid.putCard(pos, card)

    # 4th in the same row would create width 4 → violates 3×3 rule
    pos4 = GridPosition(x=-1, y=0)
    assert grid.canPutCard(pos4) is False
    with pytest.raises(ValueError):
        grid.putCard(pos4, cards[3])


def test_can_have_up_to_three_cards_in_same_column() -> None:
    grid = Grid()
    c1 = DummyCard()
    c2 = DummyCard()
    c3 = DummyCard()

    # All in column x = 0, different y
    pos1 = GridPosition(x=0, y=0)
    pos2 = GridPosition(x=0, y=1)
    pos3 = GridPosition(x=0, y=2)

    grid.putCard(pos1, c1)
    grid.putCard(pos2, c2)

    # Third in the column must be allowed
    assert grid.canPutCard(pos3) is True
    grid.putCard(pos3, c3)


def test_fourth_card_in_same_column_is_not_allowed() -> None:
    grid = Grid()
    cards: List[DummyCard] = [DummyCard() for _ in range(4)]

    positions = [
        GridPosition(x=0, y=0),
        GridPosition(x=0, y=1),
        GridPosition(x=0, y=2),
    ]

    for card, pos in zip(cards[:3], positions):
        grid.putCard(pos, card)

    pos4 = GridPosition(x=0, y=-2)
    assert grid.canPutCard(pos4) is False
    with pytest.raises(ValueError):
        grid.putCard(pos4, cards[3])


def test_three_by_three_territory_is_allowed_but_cannot_be_extended() -> None:
    """
    Full 3×3 territory is legal. Any attempt to place a card outside
    must be rejected because it would exceed 3 distinct rows or columns.
    """
    grid = Grid()
    cards: List[DummyCard] = [DummyCard() for _ in range(9)]

    # Build a 3×3 block with x,y in {0,1,2}
    positions = [
        GridPosition(x, y)
        for y in range(3)
        for x in range(3)
    ]

    for card, pos in zip(cards, positions):
        assert grid.canPutCard(pos) is True
        grid.putCard(pos, card)

    # Now grid is 3×3; any new position must extend rows/cols beyond 3
    outside_positions = [
        GridPosition(x=-1, y=1),
        GridPosition(x=1, y=-1),
    ]

    for pos in outside_positions:
        assert grid.canPutCard(pos) is False
        with pytest.raises(ValueError):
            grid.putCard(pos, DummyCard())


# ---------------------------------------------------------------------------
# Activation pattern / per-turn activation
# ---------------------------------------------------------------------------

def test_card_cannot_be_activated_without_pattern() -> None:
    grid = Grid()
    card = DummyCard()
    pos = GridPosition(x=0, y=0)

    grid.putCard(pos, card)

    # No activation pattern set → cannot be activated
    assert grid.canBeActivated(pos) is False

    with pytest.raises(ValueError):
        grid.setActivated(pos)


def test_can_be_activated_if_in_pattern_and_not_yet_activated() -> None:
    grid = Grid()
    c1 = DummyCard()
    c2 = DummyCard()

    pos1 = GridPosition(x=0, y=0)
    pos2 = GridPosition(x=1, y=0)

    grid.putCard(pos1, c1)
    grid.putCard(pos2, c2)

    # Only pos1 will be in the activation pattern
    grid.setActivationPattern([pos1])

    assert grid.canBeActivated(pos1) is True
    assert grid.canBeActivated(pos2) is False


def test_setActivated_marks_coordinate_and_blocks_future_activation() -> None:
    grid = Grid()
    card = DummyCard()
    pos = GridPosition(x=0, y=0)

    grid.putCard(pos, card)
    grid.setActivationPattern([pos])

    assert grid.canBeActivated(pos) is True

    grid.setActivated(pos)

    # Now it should no longer be activatable in this turn
    assert grid.canBeActivated(pos) is False

    with pytest.raises(ValueError):
        grid.setActivated(pos)


def test_endTurn_resets_activation_but_keeps_pattern() -> None:
    """
    With your current implementation, endTurn clears only the
    'activated this turn' set and leaves the pattern unchanged.
    That means same pattern can be used again next turn.
    """
    grid = Grid()
    card = DummyCard()
    pos = GridPosition(x=0, y=0)

    grid.putCard(pos, card)
    grid.setActivationPattern([pos])

    grid.setActivated(pos)
    assert grid.canBeActivated(pos) is False

    grid.endTurn()

    # After endTurn(), card is still in pattern, but activation is reset
    assert grid.canBeActivated(pos) is True


# ---------------------------------------------------------------------------
# State representation
# ---------------------------------------------------------------------------

def test_state_empty_grid() -> None:
    grid = Grid()
    assert grid.state() == "Grid(empty)"


def test_state_marks_pattern_and_activation() -> None:
    grid = Grid()
    c1 = DummyCard()
    c2 = DummyCard()

    pos1 = GridPosition(x=0, y=0)
    pos2 = GridPosition(x=1, y=0)

    grid.putCard(pos1, c1)
    grid.putCard(pos2, c2)

    grid.setActivationPattern([pos1])
    grid.setActivated(pos1)

    state_str = grid.state()
    # Basic format checks
    assert "Grid:" in state_str
    # pos1 is in pattern and activated → [X]
    assert "[X] (0,0)" in state_str
    # pos2 is not in pattern → [ ]
    assert "[ ] (0,1)" in state_str
