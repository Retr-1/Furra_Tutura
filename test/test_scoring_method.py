import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from terra_futura.scoring_method import ScoringMethod
from terra_futura.simple_types import Resource, Points, GridPosition
from terra_futura.interfaces import InterfaceGrid, InterfaceCard, Effect
from typing import Optional, List
from collections import Counter
from terra_futura.transformation_fixed import TransformationFixed


class GridFake(InterfaceGrid):
#used
    def getCard(self, coordinate: GridPosition)-> Optional[InterfaceCard]:
        if coordinate == GridPosition(0,0):
            card = CardFake(1, TransformationFixed([], [Resource.GREEN], 0))
            card.putResources([Resource.RED, Resource.RED, Resource.MONEY, Resource.CONSTRUCTION])
            return card

        if coordinate == GridPosition(1,0):
            card = CardFake(1, TransformationFixed([], [Resource.GREEN], 1))
            card.putResources([Resource.FOOD, Resource.CONSTRUCTION, Resource.GOODS])
            card.placePollution(1)
            return card
        
        if coordinate == GridPosition(2,0):
            card = CardFake(1, TransformationFixed([], [Resource.GREEN], 0))
            card.putResources([Resource.RED, Resource.RED, Resource.MONEY, Resource.CONSTRUCTION, Resource.RED])
            return card
        
        return None

    def canPutCard(self, coordinate: GridPosition)-> bool:
        if(coordinate.x >2):
            return False
        return True

    def putCard(self, coordinate: GridPosition, card: InterfaceCard) -> None:
        ...

# not used
    def canBeActivated(self, coordinate: GridPosition)-> bool:
        return False
        
    def setActivated(self, coordinate: GridPosition) -> None:
        ...

    def setActivationPattern(self, pattern: List[GridPosition]) -> None:
        ...
        
    def endTurn(self) -> None:
        ...

    def state(self) -> str:
        return ""

class CardFake(InterfaceCard):

    def __init__(
        self,
        pollutionSpacesL: int = 0,
        upperEffect: Optional[Effect] = None,
        lowerEffect: Optional[Effect] = None,
    ) -> None:
        # resources stored on this card (produced by its effects)
        self.resources: List[Resource] = []

        # how many pollution spaces the card has (top-right icon)
        self.pollutionSpacesL: int = pollutionSpacesL

        # current pollution state
        self._pollution: int = 0   # pollution cubes on safe spaces

        # optional effects
        self.upperEffect: Optional[Effect] = upperEffect
        self.lowerEffect: Optional[Effect] = lowerEffect

    # ------------------------------------------------------------------
    # Pollution logic (Terra Futura rules)
    # ------------------------------------------------------------------

    @property
    def pollution(self) -> int:
        return self._pollution

    @property
    def is_active(self) -> bool:

        return self.pollution < self.pollutionSpacesL

    def isActive(self) -> bool:
        return self.is_active

    def canPlacePollution(self, amount: int = 1) -> bool:
        if amount < 0:
            return False
        if not self.is_active:
            return False
        

        free_slots = self.pollutionSpacesL - self._pollution

        if amount > free_slots:
            return False
        
        return True

    def placePollution(self, amount: int = 1) -> None:

        if amount == 0:
            return

        if not self.canPlacePollution(amount):
            raise ValueError("Cannot place pollution on an inactive card.")

        free_slots = self.pollutionSpacesL - self._pollution
        use_slots = min(free_slots, amount)

        self._pollution += use_slots
        # self.is_active will now reflect center pollution automatically

    # ------------------------------------------------------------------
    # Resource management on this card
    # ------------------------------------------------------------------

    def canPutResources(self, resources: List[Resource]) -> bool:
   
        if not self.is_active:
            return False
        return True

    def putResources(self, resources: List[Resource]) -> None:

        if not self.canPutResources(resources):
            raise ValueError("Cannot add resources to an inactive card.")
        self.resources.extend(resources)

    def canGetResources(self, resources: List[Resource]) -> bool:
        if not self.is_active:
            return False

        wanted = Counter(resources)
        have = Counter(self.resources)
        # Check wanted multiset is subset of have
        return all(have[r] >= c for r, c in wanted.items())

    def getResources(self, resources: List[Resource]) -> None:
        if not self.canGetResources(resources):
            raise ValueError("Cannot pay these resources from this card.")

        # Multiset removal
        wanted = Counter(resources)
        new_contents: List[Resource] = []
        current: Counter[Resource] = Counter()
        
        for r in self.resources:
            # Keep this resource if we have already removed enough of that type
            if current[r] < wanted[r]:
                current[r] += 1
                # skip adding to new_contents -> "removed"
            else:
                new_contents.append(r)

        self.resources = new_contents


    def check(self, input: List[Resource], output: List[Resource], pollution: int) -> bool:
        if not self.is_active:
            return False
        if self.upperEffect is None:
            return False

        # Can this card pay the requested input (from its own resources)?
        if not self.canGetResources(input):
            return False

        # Can this card accept the resulting pollution?
        if not self.canPlacePollution(pollution):
            return False

        # Delegate detailed IO check to the effect itself
        return self.upperEffect.check(input, output, pollution)

    def checkLower(self, input: List[Resource], output: List[Resource], pollution: int) -> bool:
        if not self.is_active:
            return False
        if self.lowerEffect is None:
            return False

        if not self.canGetResources(input):
            return False

        if not self.canPlacePollution(pollution):
            return False

        return self.lowerEffect.check(input, output, pollution)

    def hasAssistance(self) -> bool:
        upper = self.upperEffect.hasAssistance() if self.upperEffect else False
        lower = self.lowerEffect.hasAssistance() if self.lowerEffect else False
        return upper or lower

    def state(self) -> str:
        status = "active" if self.is_active else "inactive"
        return (
            f"Card(status={status}, "
            f"resources={len(self.resources)}, "
            f"pollution={self._pollution}/{self.pollutionSpacesL}")


class TestScoringMethod(unittest.TestCase):
    def setUp(self) -> None:
        self.scoringMethod = ScoringMethod
        self.grid = GridFake()

    def test_scoringMethodNotCalculatedYet(self) ->None:
        scoring = self.scoringMethod([Resource.GREEN, Resource.GREEN, Resource.CONSTRUCTION], Points(5), self.grid)
        self.assertEqual("Scoring method wasn't calculated",  scoring.state())
    
    def test_scoringMethodEmptyNotCalculated(self) ->None:
        scoring = self.scoringMethod([], Points(0), self.grid)
        self.assertEqual("Scoring method wasn't calculated",  scoring.state())

    def test_scoringMethodEmptyCalculated(self) -> None:
        scoring = self.scoringMethod([], Points(0), self.grid)
        scoring.selectThisMethodAndCalculate()
        self.assertEqual("14", scoring.state())

    def test_scoringMethodNoBonusCalculated(self) -> None:
        scoring = self.scoringMethod([Resource.GREEN, Resource.GREEN, Resource.CONSTRUCTION], Points(5), self.grid)
        scoring.selectThisMethodAndCalculate()
        self.assertEqual("14", scoring.state())

    def test_scoringMethodBonusCalculated(self) -> None:
        scoring = self.scoringMethod([Resource.RED, Resource.CONSTRUCTION], Points(3), self.grid)
        scoring.selectThisMethodAndCalculate()
        self.assertEqual("20", scoring.state())