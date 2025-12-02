from terra_futura.interfaces import Resource, Effect
from typing import List
from dataclasses import dataclass

@dataclass(frozen=True)
class ArbitraryBasic(Effect):
    """
    Effect representing: 
        pay <from> arbitrary resources (any types),
        gain <to> specific resources,
        produce <pollution> pollution.

    UML alignment:
      - from: int
      - to: List[Resource]
      - pollution: int

    NOTE:
        Constructor uses from_ because 'from' is a Python keyword,
        but we expose a `.from` attribute to match the UML.
    """

    from_: int                 # internal
    to: List[Resource]
    pollution: int

    def __post_init__(self) ->None:
        # expose real UML attribute name: obj.from
        object.__setattr__(self, "from", self.from_)

        if self.from_ < 0:
            raise ValueError("'from' (required resource count) must be >= 0")
        if self.pollution < 0:
            raise ValueError("'pollution' must be >= 0")

    # ----------------------------------------------------------------------
    # Effect interface implementation
    # ----------------------------------------------------------------------

    def check(self, input: List[Resource], output: List[Resource], pollution: int) -> bool:
        """
        Terra Futura meaning:
        - You must pay exactly `from_` resources (any types)
        - You receive exactly `to`
        - The effect produces exactly `pollution`

        'input' = resources player intends to pay
        'output' = resources player expects to gain
        'pollution' = pollution player expects to produce
        """

        # Check the number of resources paid (any type is allowed)
        if len(input) != self.from_:
            return False

        # Check output matches exactly the specified resources
        if len(output) != len(self.to):
            return False

        # Simple 1:1 multiset check
        # (Assumes Resource instances are comparable; adjust if needed)
        for r in self.to:
            if output.count(r) != self.to.count(r):
                return False

        # Check pollution
        if pollution != self.pollution:
            return False

        return True

    def hasAssistance(self) -> bool:
        """
        ArbitraryBasic is never an Assistance-type effect.
        """
        return False

    def state(self) -> str:
        """
        Nicely formatted effect description for debugging/UI.
        """
        return f"Pay any {self.from_} → Gain {self.to} (+{self.pollution} pollution)"
    

"""
Example usage

wood = Resource()
oil = Resource()

effect = ArbitraryBasic(from_=2, to=[wood], pollution=1)

print(effect.from)      # UML-correct attribute access
print(effect.state())   # readable
"""