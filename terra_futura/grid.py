from __future__ import annotations

from typing import Dict, List, Optional, Set, Iterable

from .interfaces import InterfaceGrid, InterfaceCard
from .simple_types import GridPosition


class Grid(InterfaceGrid):
    _MAX_SIZE = 3

    def __init__(self) -> None:
        # Coordinate -> card
        self._cells: Dict[GridPosition, InterfaceCard] = {}

        # Coordinates already activated in the current turn
        self.shouldActivate: Set[GridPosition] = set()
        self.activationPattern: List[GridPosition] = []


    def _all_rows_cols_including(self, coordinate: GridPosition) -> tuple[List[int], List[int]]:
        row = [pos.x for pos in self._cells.keys()] + [coordinate.x]
        col = [pos.y for pos in self._cells.keys()] + [coordinate.y]
        return row, col
    
    def _all_rows_cols(self) -> tuple[List[int], List[int]]:
        row = [pos.x for pos in self._cells.keys()] 
        col = [pos.y for pos in self._cells.keys()]
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
        
        self.shouldActivate.clear()
        
        for placed_pos in self._cells:
            if placed_pos.x == coordinate.x or placed_pos.y == coordinate.y:
                self.shouldActivate.add(placed_pos)

        self._cells[coordinate] = card

    def canBeActivated(self, coordinate: GridPosition) -> bool:
        return coordinate in self.shouldActivate

    def setActivated(self, coordinate: GridPosition) -> None:
        if not self.canBeActivated(coordinate):
            raise ValueError("Cannot activate this card")
        
        self.shouldActivate.remove(coordinate)

    def setActivationPattern(self, pattern: List[GridPosition]) -> None:
        """# pattern pos == 0,0 is in bottom-left grid position"""
        
        if len(self._cells) != 9:
            raise ValueError("The grid is not full")

        rows, cols = self._all_rows_cols()
        minx, miny = min(cols), min(rows)

        self.activationPattern = [GridPosition(pos.x + minx, pos.y + miny) for pos in pattern]

    def endTurn(self) -> None:
        self.shouldActivate.clear()

    def state(self) -> str:
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
            is_activated = pos in self.shouldActivate
            
            marker: str
            if is_activated:
                marker = "[X]"  # already activated this turn
            elif pos in self._cells:
                marker = "[*]"  # Card, not activated
            else:
                marker = "[ ]"  # Empty cell

            try:
                coord_str = f"({pos.y},{pos.x})"
            except AttributeError:
                coord_str = repr(pos)

            lines.append(f"  {marker} {coord_str}: {card!r}")

        return "\n".join(lines)
