from abc import ABC, abstractmethod
from .interfaces import InterfaceCard
import random
import time
from typing import Optional, List
from collections.abc import Sequence

class InterfaceShuffler(ABC):
    @abstractmethod
    def shuffle(self, deck: list[InterfaceCard]) -> list[InterfaceCard]:
        pass


class RandomShuffler(InterfaceShuffler):
    def __init__(self, seed:Optional[int] = None) -> None:
        if not seed:
            seed = int(time.time())
        self.rng = random.Random(seed)
    
    def shuffle(self, deck: list[InterfaceCard]) -> list[InterfaceCard]:
        deck_copy = deck.copy()
        self.rng.shuffle(deck_copy)
        return deck_copy


class Pile:
    def __init__(self, visible_cards: Sequence[InterfaceCard], hidden_cards: Sequence[InterfaceCard], shuffler: Optional['InterfaceShuffler'] = None):
        if not shuffler:
            shuffler = RandomShuffler()
        self.shuffler = shuffler
        self.visible_cards: List[InterfaceCard] = list(visible_cards)
        self.hidden_cards: List[InterfaceCard] = list(hidden_cards)
        self.discarded_cards: List[InterfaceCard] = []
        self._fill_visible()

    def _restore_hidden(self) -> None:
        self.hidden_cards.extend(self.shuffler.shuffle(self.discarded_cards))
        self.discarded_cards.clear()

    def _fill_visible(self) -> None:
        while len(self.visible_cards) < 4:
            if len(self.hidden_cards) == 0:
                if len(self.discarded_cards) == 0:
                    raise ValueError('Not enough cards in deck')
                self._restore_hidden()

            self.visible_cards.append(self.hidden_cards.pop())

    
    def getCard(self, index: int) -> Optional[InterfaceCard]:
        if index < 1 or index > 4:
            return None
        
        return self.visible_cards[index-1]
    
    def takeCard(self, index: int) -> InterfaceCard:
        if index < 1 or index > 4:
            raise ValueError("Cannot get card at that position")
        
        self._fill_visible()
        card = self.visible_cards.pop(index-1)
        self._fill_visible()
        return card
    
    def removeLastCard(self) -> None:
        self._fill_visible()
        self.discarded_cards.append(self.visible_cards.pop())
        self._fill_visible()

    def state(self) -> str:
        out = ''
        
        for i,x in enumerate(self.visible_cards):
            out += f'Visible {i}: {x.state()}\n'
        for i,x in enumerate(self.visible_cards):
            out += f'Hidden {i}: {x.state()}\n'
        for i,x in enumerate(self.visible_cards):
            out += f'Discarded {i}: {x.state()}\n'
        
        return out


