# test/test_pile.py

import pytest
from typing import cast, List

from terra_futura.pile import Pile
from terra_futura.interfaces import InterfaceCard


class FakeCard:
    """Simple test double for InterfaceCard."""
    def __init__(self, label: str) -> None:
        self._label = label

    def state(self) -> str:
        return self._label

    def __repr__(self) -> str:
        return f"FakeCard({self._label})"


class FakeShuffler:
    def __init__(self) -> None:
        # Each element is the deck passed to shuffle() at that point in time.
        self.calls: List[list[InterfaceCard]] = []

    def shuffle(self, deck: list[InterfaceCard]) -> list[InterfaceCard]:
        self.calls.append(list(deck))
        return list(deck)


def _make_cards(*labels: str) -> list[FakeCard]:
    return [FakeCard(label) for label in labels]


def _as_interface_cards(cards: list[FakeCard]) -> list[InterfaceCard]:
    # Tell mypy to treat FakeCard as InterfaceCard for this test.
    return cast(List[InterfaceCard], cards)


# ---------------------------------------------------------------------
#  Tests
# ---------------------------------------------------------------------

def test_init_fills_visible_up_to_four_from_hidden() -> None:
    # visible has only 2 cards, hidden has 3 → Pile must top up to 4
    visible = _as_interface_cards(_make_cards("v1", "v2"))
    hidden = _as_interface_cards(_make_cards("h1", "h2", "h3"))  # top is h3
    shuffler = FakeShuffler()

    pile = Pile(visible_cards=visible, hidden_cards=hidden, shuffler=shuffler)

    # visible should now have 4 cards
    assert len(pile.visible_cards) == 4

    # Order:
    #   start: visible = [v1, v2]
    #   _fill_visible: pop h3 → insert at 0 → [h3, v1, v2]
    #                  pop h2 → insert at 0 → [h2, h3, v1, v2]
    visible_states = [c.state() for c in pile.visible_cards]
    assert visible_states == ["h2", "h3", "v1", "v2"]

    # one hidden card remains (h1)
    hidden_states = [c.state() for c in pile.hidden_cards]
    assert hidden_states == ["h1"]

    # no discards yet, and shuffler not used
    assert len(pile.discarded_cards) == 0
    assert shuffler.calls == []


def test_getCard_returns_card_for_valid_index_and_none_out_of_range() -> None:
    visible = _as_interface_cards(_make_cards("a", "b", "c", "d"))
    hidden = _as_interface_cards(_make_cards("x"))
    pile = Pile(visible_cards=visible, hidden_cards=hidden, shuffler=FakeShuffler())

    # valid indices 1..4
    assert pile.getCard(1).state() == "a"
    assert pile.getCard(4).state() == "d"

    # out of range indices
    assert pile.getCard(0) is None
    assert pile.getCard(5) is None


def test_takeCard_from_visible_removes_selected_and_refills_from_hidden() -> None:
    visible = _as_interface_cards(_make_cards("v1", "v2", "v3", "v4"))
    hidden = _as_interface_cards(_make_cards("h1", "h2"))  # top is h2
    pile = Pile(visible_cards=visible, hidden_cards=hidden, shuffler=FakeShuffler())

    taken = pile.takeCard(2)  # should take "v2"

    # returned card is correct
    assert taken.state() == "v2"

    # Explanation:
    #   initial visible = [v1, v2, v3, v4]
    #   takeCard(2) calls _fill_visible() first → already 4 cards, no change
    #   then removes index 2 (v2) → [v1, v3, v4]
    #   then _fill_visible():
    #       hidden = [h1, h2]; pop() → h2; insert at 0
    #       visible = [h2, v1, v3, v4]
    visible_states = [c.state() for c in pile.visible_cards]
    assert visible_states == ["h2", "v1", "v3", "v4"]

    # hidden now only has h1
    hidden_states = [c.state() for c in pile.hidden_cards]
    assert hidden_states == ["h1"]

    # takeCard from visible does not add anything to discard pile
    assert [c.state() for c in pile.discarded_cards] == []


def test_takeCard_index_0_takes_directly_from_hidden_without_changing_visible() -> None:
    visible = _as_interface_cards(_make_cards("v1", "v2", "v3", "v4"))
    hidden = _as_interface_cards(_make_cards("h1", "h2"))  # top is h2
    pile = Pile(visible_cards=visible, hidden_cards=hidden, shuffler=FakeShuffler())

    # takeCard(0) means "take directly from hidden deck"
    taken = pile.takeCard(0)

    # should be top of hidden deck (h2)
    assert taken.state() == "h2"

    # visible should remain unchanged (apart from the internal _fill_visible,
    # which did nothing because visible already had 4 cards)
    visible_states = [c.state() for c in pile.visible_cards]
    assert visible_states == ["v1", "v2", "v3", "v4"]

    # hidden now lost only h2, leaving h1
    hidden_states = [c.state() for c in pile.hidden_cards]
    assert hidden_states == ["h1"]


def test_takeCard_raises_for_invalid_index() -> None:
    visible = _as_interface_cards(_make_cards("v1", "v2", "v3", "v4"))
    hidden = _as_interface_cards(_make_cards("h1"))
    pile = Pile(visible_cards=visible, hidden_cards=hidden, shuffler=FakeShuffler())

    with pytest.raises(ValueError, match="Cannot get card at that position"):
        pile.takeCard(-1)

    with pytest.raises(ValueError, match="Cannot get card at that position"):
        pile.takeCard(5)


def test_removeLastCard_discards_oldest_and_refills_from_hidden() -> None:
    visible = _as_interface_cards(_make_cards("v1", "v2", "v3", "v4"))
    hidden = _as_interface_cards(_make_cards("h1", "h2"))  # top is h2
    pile = Pile(visible_cards=visible, hidden_cards=hidden, shuffler=FakeShuffler())

    pile.removeLastCard()

    # oldest visible (last) was v4 → must be in discard pile
    discarded_states = [c.state() for c in pile.discarded_cards]
    assert discarded_states == ["v4"]

    # Explanation:
    #   initial visible = [v1, v2, v3, v4]
    #   removeLastCard():
    #       _fill_visible() → unchanged
    #       pop() last → v4 → discarded
    #       visible = [v1, v2, v3]
    #       _fill_visible(): pop h2 → insert at 0
    #       visible = [h2, v1, v2, v3]
    visible_states = [c.state() for c in pile.visible_cards]
    assert visible_states == ["h2", "v1", "v2", "v3"]

    # hidden lost h2, only h1 remains
    hidden_states = [c.state() for c in pile.hidden_cards]
    assert hidden_states == ["h1"]


def test_init_raises_when_not_enough_cards_to_reach_four_visible() -> None:
    # total cards = 3 < 4 → constructor should fail in _fill_visible
    visible = _as_interface_cards(_make_cards("v1"))
    hidden = _as_interface_cards(_make_cards("h1", "h2"))

    with pytest.raises(ValueError, match="Not enough cards in deck"):
        Pile(visible_cards=visible, hidden_cards=hidden, shuffler=FakeShuffler())


def test_removeLastCard_triggers_reshuffle_using_shuffler() -> None:
    # Setup to eventually exhaust hidden while having some discarded cards
    visible = _as_interface_cards(_make_cards("v1", "v2", "v3", "v4"))
    hidden = _as_interface_cards(_make_cards("h1"))  # single hidden card
    shuffler = FakeShuffler()

    pile = Pile(visible_cards=visible, hidden_cards=hidden, shuffler=shuffler)

    # 1st remove:
    #   discard v4 → [v4]
    #   refill with h1 → visible [h1, v1, v2, v3], hidden []
    pile.removeLastCard()
    assert [c.state() for c in pile.discarded_cards] == ["v4"]
    assert [c.state() for c in pile.hidden_cards] == []

    # 2nd remove:
    #   discard last (v3) → discarded [v4, v3], visible [h1, v1, v2]
    #   refill: hidden empty, discarded non-empty → _restore_hidden
    #           shuffler.shuffle([v4, v3]) → [v4, v3]
    #           hidden.extend(...) → hidden [v4, v3], discarded cleared
    #           then pop v3 → insert at 0 → visible [v3, h1, v1, v2], hidden [v4]
    pile.removeLastCard()

    # Shuffler must have been called exactly once with [v4, v3]
    assert len(shuffler.calls) == 1
    reshuffled_states = [c.state() for c in shuffler.calls[0]]
    assert reshuffled_states == ["v4", "v3"]

    # Discard pile should now be empty (cards moved back into hidden and visible)
    assert [c.state() for c in pile.discarded_cards] == []

    # Still 4 visible cards
    assert len(pile.visible_cards) == 4
    visible_states = [c.state() for c in pile.visible_cards]
    assert visible_states == ["v3", "h1", "v1", "v2"]

    # Hidden should hold the remaining reshuffled card
    hidden_states = [c.state() for c in pile.hidden_cards]
    assert hidden_states == ["v4"]


def test_state_includes_visible_card_states() -> None:
    visible = _as_interface_cards(_make_cards("v1", "v2", "v3", "v4"))
    hidden = _as_interface_cards(_make_cards("h1"))
    pile = Pile(visible_cards=visible, hidden_cards=hidden, shuffler=FakeShuffler())

    s = pile.state()
    # At minimum, state() should mention visible cards via their state()
    for label in ["v1", "v2", "v3", "v4"]:
        assert label in s
