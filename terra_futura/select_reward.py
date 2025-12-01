from __future__ import annotations

from typing import Optional, List, TYPE_CHECKING
from enum import Enum, auto

from .simple_types import Resource
from .interfaces import InterfaceCard


class RewardState(Enum):
    IDLE = auto()
    PENDING = auto()
    SELECTED = auto()


class SelectReward:
    """
    Tracks which player may choose a reward and which Resource options they can pick.

    Attributes
    ----------
    player:
        Id of the player who is allowed to choose the reward.
        None means that there is currently no pending reward.
    selection:
        List of Resource options that this player can choose from.
    """

    def __init__(self) -> None:
        self.player: Optional[int] = None
        self.selection: List[Resource] = []
        self._state: RewardState = RewardState.IDLE
        self._card: Optional["InterfaceCard"] = None

    # ------------------------------------------------------------------ #
    # Configuration                                                       #
    # ------------------------------------------------------------------ #
    def setReward(self, player: int, card: "InterfaceCard", reward: List[Resource]) -> None:
        """
        Configure a new reward:

        - player: id of the player who will choose
        - card:   card on which the effect happened (stored for possible future use)
        - reward: list of Resource options they may choose from
        """
        self.player = player
        self._card = card
        self.selection = list(reward)
        self._state = RewardState.PENDING

    # ------------------------------------------------------------------ #
    # Query & selection                                                   #
    # ------------------------------------------------------------------ #
    def canSelectReward(self, resource: Resource) -> bool:
        """
        Check whether a reward can currently be selected and
        whether this resource is one of the allowed options.
        """
        if self._state != RewardState.PENDING:
            return False

        return resource in self.selection

    def selectReward(self, resource: Resource) -> None:
        if not self.canSelectReward(resource):
            raise ValueError("Cannot select the reward")

        self.selection = [resource]
        self._state = RewardState.SELECTED

    # ------------------------------------------------------------------ #
    # State                                                               #
    # ------------------------------------------------------------------ #
    def state(self) -> RewardState:
        """
        Return current internal state as an enum value.
        """
        return self._state
