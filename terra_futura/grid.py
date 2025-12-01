from __future__ import annotations

from typing import Dict, List, Optional, Set, Iterable

from .interfaces import InterfaceGrid, InterfaceCard
from .simple_types import GridPosition


class Grid(InterfaceGrid):
    _MAX_SIZE = 3

    def __init__(self) -> None:
        # Coordinate -> card
        self._cells: Dict[GridPosition, InterfaceCard] = {}

        # Current activation pattern (order chosen by the player / game logic)
        self._activation_pattern: List[GridPosition] = []

        # Coordinates already activated in the current turn
        self._activated_this_turn: Set[GridPosition] = set()


    def _all_rows_cols_including(self, coordinate: GridPosition) -> tuple[List[int], List[int]]:
        row = [pos.x for pos in self._cells.keys()] + [coordinate.x]
        col = [pos.y for pos in self._cells.keys()] + [coordinate.y]
        return row, col

    def getCard(self, coordinate: GridPosition) -> Optional[InterfaceCard]:
        return self._cells.get(coordinate)

    def canPutCard(self, coordinate: GridPosition) -> bool:
        # Already occupied
        if coordinate in self._cells:
            return False

        # First card can always go anywhere
        if not self._cells:
            return True

        row, col = self._all_rows_cols_including(coordinate)
        width = max(row) - min(row) + 1
        height = max(col) - min(col) + 1

        if height > self._MAX_SIZE or width > self._MAX_SIZE:
            return False

        return True

    def putCard(self, coordinate: GridPosition, card: InterfaceCard) -> None:
        if not self.canPutCard(coordinate):
            raise ValueError("Cannot put card on this position")

        self._cells[coordinate] = card

    def canBeActivated(self, coordinate: GridPosition) -> bool:
        """
        A coordinate can be activated if:
        - there is a card there
        - it is part of the current activation pattern
        - it has not yet been activated in this turn
        """
        if coordinate not in self._cells:
            return False

        if coordinate not in self._activation_pattern:
            return False

        if coordinate in self._activated_this_turn:
            return False

        return True

    def setActivated(self, coordinate: GridPosition) -> None:
        """
        Mark the card at 'coordinate' as activated for this turn.
        """
        if not self.canBeActivated(coordinate):
            raise ValueError("Cannot activate this card")
        
        self._activated_this_turn.add(coordinate)

    def setActivationPattern(self, pattern: List[GridPosition]) -> None:
        self._activation_pattern = pattern
        self._activated_this_turn.clear()

    def endTurn(self) -> None:
        self._activated_this_turn.clear()

    def state(self) -> str:
        """
        Return a simple string representation of the grid and activation state.

        The format is not specified by the assignment, so this is mainly
        for debugging / Game.state() composition.
        """
        if not self._cells:
            return "Grid(empty)"

        # Sort by row, then col for deterministic output
        sorted_items: Iterable[tuple[GridPosition, InterfaceCard]] = sorted(
            self._cells.items(),
            key=lambda item: (item[0].y, item[0].x),
        )

        lines: List[str] = []
        lines.append("Grid:")

        for pos, card in sorted_items:
            in_pattern = pos in self._activation_pattern
            is_activated = pos in self._activated_this_turn
            marker: str
            if is_activated:
                marker = "[X]"  # already activated this turn
            elif in_pattern:
                marker = "[*]"  # in pattern, not yet activated
            else:
                marker = "[ ]"  # not in current pattern

            try:
                coord_str = f"({pos.y},{pos.x})"
            except AttributeError:
                coord_str = repr(pos)

            lines.append(f"  {marker} {coord_str}: {card!r}")

        return "\n".join(lines)
