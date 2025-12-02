
from dataclasses import dataclass
from typing import List
from collections import Counter
from abc import ABC, abstractmethod
from terra_futura.interfaces import Effect, Resource


@dataclass(frozen=True)
class TransformationFixed(Effect):
    """
    Fixed transformation effect:

        pay EXACTLY 'from' (multiset of specific resources)
        -> receive EXACTLY 'to'
        -> produce EXACTLY 'pollution' cubes.

    UML fields:
      - from: List[Resource]
      - to:   List[Resource]
      - polution: int  (spelled 'pollution' here in code)

    Note:
        - Constructor uses 'from_' because 'from' is a Python keyword.
        - We expose .from attribute in __post_init__ to match UML naming.
    """

    from_: List[Resource]
    to: List[Resource]
    pollution: int

    def __post_init__(self) -> None:
        # Expose .from for UML alignment
        object.__setattr__(self, "from", self.from_)

        if self.pollution < 0:
            raise ValueError("'pollution' must be >= 0")

    # ------------------------------------------------------------------
    # Effect interface implementation
    # ------------------------------------------------------------------

    def check(self, input: List[Resource], output: List[Resource], pollution: int) -> bool:
        """
        Check whether:
          - input matches 'from' as a multiset (same resources with same multiplicities)
          - output matches 'to' as a multiset
          - pollution equals self.pollution

        Multiset comparison is done with collections.Counter, which requires that
        Resource objects be hashable and comparable in a meaningful way, or that
        you use distinct instances appropriately.
        """
        # Compare paid resources with expected 'from'
        if Counter(input) != Counter(self.from_):
            return False

        # Compare gained resources with expected 'to'
        if Counter(output) != Counter(self.to):
            return False

        # Compare pollution
        if pollution != self.pollution:
            return False

        return True

    def hasAssistance(self) -> bool:
        """
        A pure fixed transformation is not an Assistance effect.
        """
        return False

    def state(self) -> str:
        """
        Human-readable representation, useful for debugging or UI logs.
        """

        core = f"Pay {self.from_} → Gain {self.to}"
        if self.pollution > 0:
            core += f" (+{self.pollution} pollution)"
        return core