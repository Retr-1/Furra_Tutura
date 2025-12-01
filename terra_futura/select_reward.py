from __future__ import annotations

from typing import Optional, List, TYPE_CHECKING
from enum import Enum, auto

from .simple_types import Resource, GridPosition
from .interfaces import InterfaceCard, PlayerInterface


class RewardState(Enum):
    IDLE = auto()
    PENDING = auto()
    SELECTED = auto()


class SelectReward:
    def __init__(self) -> None:
        self.player: Optional[PlayerInterface] = None
        self.selection: List[Resource] = []
        self._state: RewardState = RewardState.IDLE
        self._card: Optional["InterfaceCard"] = None

    def setReward(self, player: PlayerInterface, card: "InterfaceCard", reward: List[Resource]) -> None:
        has_card = False
        for x in range(-2,3):
            for y in range(-2,3):
                c = player.getGrid().getCard(GridPosition(x,y))
                if c and c.state() == card.state():
                    has_card = True
                    break
        
        if not has_card:
            raise ValueError("Player has no such card")

        self.player = player
        self._card = card
        self.selection = list(reward)
        self._state = RewardState.PENDING


    def canSelectReward(self, resource: Resource) -> bool:
        if self._state != RewardState.PENDING:
            return False
        
        if not self.player:
            return False

        return resource in self.selection

    def selectReward(self, resource: Resource) -> None:
        if not self.canSelectReward(resource):
            raise ValueError("Cannot select the reward")

        self.selection = [resource]
        self._state = RewardState.SELECTED

    def state(self) -> RewardState:
        return self._state
