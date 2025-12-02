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
# Activation behaviour: shouldActivate + setActivated + endTurn
# ---------------------------------------------------------------------------

def test_put_card_does_not_activate_anything_on_first_card() -> None:
    grid = Grid()
    card = DummyCard()
    pos = GridPosition(x=0, y=0)

    grid.putCard(pos, card)

    # No other cards share row/col yet, so nothing should be in shouldActivate
    assert grid.canBeActivated(pos) is False


def test_put_card_activates_existing_cards_in_same_row() -> None:
    grid = Grid()
    c1 = DummyCard()
    c2 = DummyCard()

    pos1 = GridPosition(x=-1, y=0)
    pos2 = GridPosition(x=1, y=0)  # same row (y=0)

    grid.putCard(pos1, c1)

    # After first card, nothing is marked
    assert grid.canBeActivated(pos1) is False

    grid.putCard(pos2, c2)

    # pos1 should now be in shouldActivate because new card shares its row
    assert grid.canBeActivated(pos1) is True
    # The newly placed card itself is NOT added to shouldActivate
    assert grid.canBeActivated(pos2) is False


def test_put_card_activates_existing_cards_in_same_column() -> None:
    grid = Grid()
    c1 = DummyCard()
    c2 = DummyCard()

    pos1 = GridPosition(x=0, y=-1)
    pos2 = GridPosition(x=0, y=1)  # same column (x=0)

    grid.putCard(pos1, c1)
    assert grid.canBeActivated(pos1) is False

    grid.putCard(pos2, c2)

    # pos1 now shares column with new card → should be activatable
    assert grid.canBeActivated(pos1) is True
    assert grid.canBeActivated(pos2) is False


def test_multiple_existing_cards_in_same_row_or_column_are_activated() -> None:
    grid = Grid()
    c1 = DummyCard()
    c2 = DummyCard()
    c3 = DummyCard()

    pos1 = GridPosition(x=-1, y=0)
    pos2 = GridPosition(x=0, y=0)
    pos3 = GridPosition(x=1, y=0)

    grid.putCard(pos1, c1)
    grid.putCard(pos2, c2)

    # No activations yet (only 2 cards, second didn't share row with any
    # *previous* cards? Actually it did: putting pos2 should activate pos1)
    assert grid.canBeActivated(pos1) is True
    assert grid.canBeActivated(pos2) is False

    # Now adding third card in same row should activate both existing ones
    grid.endTurn()  # clear shouldActivate to see effect purely from third placement
    grid.putCard(pos3, c3)

    assert grid.canBeActivated(pos1) is True
    assert grid.canBeActivated(pos2) is True
    assert grid.canBeActivated(pos3) is False


def test_setActivated_removes_coordinate_from_shouldActivate() -> None:
    grid = Grid()
    c1 = DummyCard()
    c2 = DummyCard()

    pos1 = GridPosition(x=-1, y=0)
    pos2 = GridPosition(x=1, y=0)

    grid.putCard(pos1, c1)
    grid.putCard(pos2, c2)

    # pos1 should be activatable (existing card sharing row with newly placed)
    assert grid.canBeActivated(pos1) is True

    grid.setActivated(pos1)
    assert grid.canBeActivated(pos1) is False

    # Calling setActivated again should fail
    with pytest.raises(ValueError):
        grid.setActivated(pos1)


def test_setActivated_raises_for_coordinate_not_in_shouldActivate() -> None:
    grid = Grid()
    card = DummyCard()
    pos = GridPosition(x=0, y=0)

    grid.putCard(pos, card)

    # pos not in shouldActivate yet
    assert grid.canBeActivated(pos) is False
    with pytest.raises(ValueError):
        grid.setActivated(pos)

def test_correct_shouldactivate() -> None:
    grid = Grid()
    c1 = DummyCard()
    c2 = DummyCard()
    c3 = DummyCard()
    p1 = GridPosition(1,-1)
    p2 = GridPosition(2,0)
    p3 = GridPosition(1,0)
    grid.putCard(p1, c1)
    grid.putCard(p2, c2)
    print(grid.shouldActivate)
    grid.putCard(p3, c3)
    print(grid.shouldActivate)

    assert p1 in grid.shouldActivate
    assert p2 in grid.shouldActivate
    assert not p3 in grid.shouldActivate


def test_endTurn_clears_shouldActivate() -> None:
    grid = Grid()
    c1 = DummyCard()
    c2 = DummyCard()

    pos1 = GridPosition(x=-1, y=0)
    pos2 = GridPosition(x=1, y=0)

    grid.putCard(pos1, c1)
    grid.putCard(pos2, c2)

    assert grid.canBeActivated(pos1) is True

    grid.endTurn()
    assert grid.canBeActivated(pos1) is False


def test_setActivationPattern_raises_if_grid_not_full() -> None:
    grid = Grid()
    card = DummyCard()
    pos = GridPosition(x=0, y=0)

    grid.putCard(pos, card)
    pattern = [GridPosition(x=0, y=0)]

    with pytest.raises(ValueError):
        grid.setActivationPattern(pattern)


def test_setActivationPattern_offsets_pattern_to_grid_coordinates() -> None:
    grid = Grid()
    cards: List[DummyCard] = [DummyCard() for _ in range(9)]

    # Build a 3×3 block with x,y in {-1,0,1}
    positions = [
        GridPosition(x, y)
        for y in (-1, 0, 1)
        for x in (-1, 0, 1)
    ]

    for card, pos in zip(cards, positions):
        grid.putCard(pos, card)

    # Local pattern: bottom-left (0,0), next to the right (1,0), top-right (2,2)
    local_pattern = [
        GridPosition(x=0, y=0),
        GridPosition(x=1, y=0),
        GridPosition(x=2, y=2),
    ]

    grid.setActivationPattern(local_pattern)

    # minx, miny are computed from existing cells:
    # rows = [pos.x], cols = [pos.y]
    # rows,cols ∈ {-1,0,1}, so minx = min(cols) = -1, miny = min(rows) = -1
    # So global pattern = (x+minx, y+miny)
    expected_global = [
        GridPosition(x=-1, y=-1),  # (0-1, 0-1)
        GridPosition(x=0,  y=-1),  # (1-1, 0-1)
        GridPosition(x=1,  y=1),   # (2-1, 2-1)
    ]

    assert grid.activationPattern == expected_global
