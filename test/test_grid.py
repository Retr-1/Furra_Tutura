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
# Placement rules (3×3 territory, coordinates in [-2, 2])
# ---------------------------------------------------------------------------

def test_first_card_can_be_placed_anywhere_within_allowed_coordinates() -> None:
    grid = Grid()
    card = DummyCard()

    pos1 = GridPosition(x=0, y=0)
    pos2 = GridPosition(x=2, y=-2)  # still within [-2, 2]

    # When grid is empty, any coordinate in allowed range is OK
    assert grid.canPutCard(pos1) is True
    assert grid.canPutCard(pos2) is True

    grid.putCard(pos1, card)
    assert grid.getCard(pos1) is card


def test_cannot_put_card_on_occupied_coordinate() -> None:
    grid = Grid()
    card1 = DummyCard()
    card2 = DummyCard()
    pos = GridPosition(x=0, y=0)

    grid.putCard(pos, card1)

    # Same coordinate should not be allowed
    assert grid.canPutCard(pos) is False

    # And putCard should raise
    with pytest.raises(ValueError):
        grid.putCard(pos, card2)


def test_can_have_up_to_three_cards_in_same_row() -> None:
    """
    Territory is at most 3×3 cards.
    Using x in {-1, 0, 1} and fixed y = 0 is a legal 3-wide row.
    """
    grid = Grid()
    c1 = DummyCard()
    c2 = DummyCard()
    c3 = DummyCard()

    pos1 = GridPosition(x=-1, y=0)
    pos2 = GridPosition(x=0, y=0)
    pos3 = GridPosition(x=1, y=0)

    grid.putCard(pos1, c1)
    grid.putCard(pos2, c2)

    # Third in the row must be allowed
    assert grid.canPutCard(pos3) is True
    grid.putCard(pos3, c3)


def test_fourth_card_in_same_row_is_not_allowed() -> None:
    grid = Grid()
    cards: List[DummyCard] = [DummyCard() for _ in range(4)]

    # Legal row: x in {-1, 0, 1}, y = 0
    positions = [
        GridPosition(x=-1, y=0),
        GridPosition(x=0, y=0),
        GridPosition(x=1, y=0),
    ]

    for card, pos in zip(cards[:3], positions):
        grid.putCard(pos, card)

    # x = 2 would make width 4 (from -1 to 2 → 4 columns) → illegal
    pos4 = GridPosition(x=2, y=0)
    assert grid.canPutCard(pos4) is False
    with pytest.raises(ValueError):
        grid.putCard(pos4, cards[3])


def test_can_have_up_to_three_cards_in_same_column() -> None:
    grid = Grid()
    c1 = DummyCard()
    c2 = DummyCard()
    c3 = DummyCard()

    # Legal column: y in {-1, 0, 1}, x = 0
    pos1 = GridPosition(x=0, y=-1)
    pos2 = GridPosition(x=0, y=0)
    pos3 = GridPosition(x=0, y=1)

    grid.putCard(pos1, c1)
    grid.putCard(pos2, c2)

    assert grid.canPutCard(pos3) is True
    grid.putCard(pos3, c3)


def test_fourth_card_in_same_column_is_not_allowed() -> None:
    grid = Grid()
    cards: List[DummyCard] = [DummyCard() for _ in range(4)]

    positions = [
        GridPosition(x=0, y=-1),
        GridPosition(x=0, y=0),
        GridPosition(x=0, y=1),
    ]

    for card, pos in zip(cards[:3], positions):
        grid.putCard(pos, card)

    pos4 = GridPosition(x=0, y=2)
    assert grid.canPutCard(pos4) is False
    with pytest.raises(ValueError):
        grid.putCard(pos4, cards[3])


def test_three_by_three_territory_is_allowed_but_cannot_be_extended() -> None:
    """
    Full 3×3 territory (x,y in {-1,0,1}) is legal.
    Any attempt to place a card outside must be rejected
    because it would exceed 3 distinct rows or columns.
    """
    grid = Grid()
    cards: List[DummyCard] = [DummyCard() for _ in range(9)]

    # Build 3×3 block with x,y in {-1,0,1}
    positions = [
        GridPosition(x, y)
        for y in (-1, 0, 1)
        for x in (-1, 0, 1)
    ]

    for card, pos in zip(cards, positions):
        assert grid.canPutCard(pos) is True
        grid.putCard(pos, card)

    # Now any position that expands x or y range beyond {-1,0,1} is illegal
    outside_positions = [
        GridPosition(x=2, y=0),   # width from -1 to 2 → 4
        GridPosition(x=-2, y=0),  # width from -2 to 1 → 4
        GridPosition(x=0, y=2),   # height from -1 to 2 → 4
        GridPosition(x=0, y=-2),  # height from -2 to 1 → 4
    ]

    for pos in outside_positions:
        assert grid.canPutCard(pos) is False
        with pytest.raises(ValueError):
            grid.putCard(pos, DummyCard())


# ---------------------------------------------------------------------------
# Activation behaviour (no stored pattern, just "activated this turn")
# ---------------------------------------------------------------------------

def test_can_be_activated_if_card_exists_and_not_yet_activated() -> None:
    grid = Grid()
    card = DummyCard()
    pos = GridPosition(x=0, y=0)

    grid.putCard(pos, card)

    # Not activated yet → True
    assert grid.canBeActivated(pos) is True


def test_cannot_be_activated_if_no_card() -> None:
    grid = Grid()
    pos = GridPosition(x=0, y=0)

    assert grid.canBeActivated(pos) is False
    with pytest.raises(ValueError):
        grid.setActivated(pos)


def test_setActivated_marks_coordinate_and_blocks_future_activation() -> None:
    grid = Grid()
    card = DummyCard()
    pos = GridPosition(x=0, y=0)

    grid.putCard(pos, card)

    assert grid.canBeActivated(pos) is True

    grid.setActivated(pos)

    # Now it should no longer be activatable in this turn
    assert grid.canBeActivated(pos) is False

    with pytest.raises(ValueError):
        grid.setActivated(pos)


def test_setActivationPattern_activates_all_positions() -> None:
    """
    In the new implementation, setActivationPattern does not store a pattern,
    but immediately calls setActivated on each coordinate.
    """
    grid = Grid()
    c1 = DummyCard()
    c2 = DummyCard()

    pos1 = GridPosition(x=-1, y=0)
    pos2 = GridPosition(x=1, y=0)

    grid.putCard(pos1, c1)
    grid.putCard(pos2, c2)

    # Initially, both can be activated
    assert grid.canBeActivated(pos1) is True
    assert grid.canBeActivated(pos2) is True

    grid.setActivationPattern([pos1, pos2])

    # After setActivationPattern, both should be marked activated
    assert grid.canBeActivated(pos1) is False
    assert grid.canBeActivated(pos2) is False


def test_setActivationPattern_raises_if_coordinate_without_card() -> None:
    grid = Grid()
    card = DummyCard()
    valid_pos = GridPosition(x=0, y=0)
    invalid_pos = GridPosition(x=1, y=0)

    grid.putCard(valid_pos, card)

    # Pattern includes a coordinate without a card → setActivated raises
    with pytest.raises(ValueError):
        grid.setActivationPattern([valid_pos, invalid_pos])


def test_endTurn_resets_activation() -> None:
    grid = Grid()
    card = DummyCard()
    pos = GridPosition(x=0, y=0)

    grid.putCard(pos, card)
    grid.setActivated(pos)

    assert grid.canBeActivated(pos) is False

    grid.endTurn()

    # After endTurn(), activation is reset
    assert grid.canBeActivated(pos) is True


# ---------------------------------------------------------------------------
# State representation
# ---------------------------------------------------------------------------

def test_state_empty_grid() -> None:
    grid = Grid()
    assert grid.state() == "Grid(empty)"


def test_state_marks_activated_and_non_activated_cards() -> None:
    grid = Grid()
    c1 = DummyCard()
    c2 = DummyCard()

    pos1 = GridPosition(x=-1, y=0)
    pos2 = GridPosition(x=1, y=0)

    grid.putCard(pos1, c1)
    grid.putCard(pos2, c2)

    # Initially, none are activated → both should be "[*]"
    state_str = grid.state()
    assert "[*] (0,-1)" in state_str  # (y,x) = (0,-1)
    assert "[*] (0,1)" in state_str   # (y,x) = (0,1)

    # Activate one of them
    grid.setActivated(pos1)
    state_str = grid.state()

    # pos1 is now activated → [X]
    assert "[X] (0,-1)" in state_str
    # pos2 is still not activated → [*]
    assert "[*] (0,1)" in state_str
