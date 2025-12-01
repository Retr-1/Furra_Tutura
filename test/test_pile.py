import pytest

from terra_futura.pile import Pile, InterfaceShuffler
from terra_futura.interfaces import InterfaceCard

class FakeCard(InterfaceCard):
    """Simple stand-in for InterfaceCard."""

    def __init__(self, name: str) -> None:
        self.name = name

    def state(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"FakeCard({self.name})"


class FakeShuffler(InterfaceShuffler):
    """
    Deterministic shuffler for tests.
    Just records the decks it was asked to shuffle and returns them unchanged
    (you can change behaviour if you want to test permutations).
    """

    def __init__(self) -> None:
        self.calls: list[list[FakeCard]] = []

    def shuffle(self, deck: list[FakeCard]) -> list[FakeCard]:
        # record the exact deck Pile asked us to shuffle
        self.calls.append(list(deck))
        # return a copy, same order
        return list(deck)


def _make_cards(*names: str) -> list[FakeCard]:
    return [FakeCard(n) for n in names]


def test_init_fills_visible_up_to_four_from_hidden() -> None:
    # visible has only 2 cards, hidden has 3 → Pile must top up to 4
    visible = _make_cards("v1", "v2")
    hidden = _make_cards("h1", "h2", "h3")  # top is h3, because pop() from end
    shuffler = FakeShuffler()

    pile = Pile(visible_cards=visible, hidden_cards=hidden, shuffler=shuffler)

    # visible should now have 4 cards
    assert len(pile.visible_cards) == 4
    # existing visible stay in front, then two drawn from the end of hidden
    assert [c.state() for c in pile.visible_cards] == ["v1", "v2", "h3", "h2"]
    # one hidden card remains
    assert [c.state() for c in pile.hidden_cards] == ["h1"]
    # no discards yet, and shuffler not used
    assert pile.discarded_cards == []
    assert shuffler.calls == []


def test_getCard_returns_card_for_valid_index_and_none_out_of_range() -> None:
    visible = _make_cards("a", "b", "c", "d")
    hidden = _make_cards("x")
    pile = Pile(visible_cards=visible, hidden_cards=hidden, shuffler=FakeShuffler())

    # valid indices
    assert pile.getCard(1).state() == "a"
    assert pile.getCard(4).state() == "d"

    # out of range indices
    assert pile.getCard(0) is None
    assert pile.getCard(5) is None


def test_takeCard_removes_selected_and_refills_from_hidden() -> None:
    visible = _make_cards("v1", "v2", "v3", "v4")
    hidden = _make_cards("h1", "h2")  # top is h2
    pile = Pile(visible_cards=visible, hidden_cards=hidden, shuffler=FakeShuffler())

    taken = pile.takeCard(2)  # should take "v2"

    # returned card is correct
    assert taken.state() == "v2"

    # visible was [v1, v2, v3, v4], after remove index 2 → [v1, v3, v4]
    # then we refill from hidden, drawing h2 (top) and appending it
    assert [c.state() for c in pile.visible_cards] == ["v1", "v3", "v4", "h2"]

    # hidden now only has h1
    assert [c.state() for c in pile.hidden_cards] == ["h1"]

    # takeCard does not add anything to discard pile
    assert [c.state() for c in pile.discarded_cards] == []


def test_removeLastCard_discards_oldest_and_refills_from_hidden() -> None:
    visible = _make_cards("v1", "v2", "v3", "v4")
    hidden = _make_cards("h1", "h2")  # top is h2
    pile = Pile(visible_cards=visible, hidden_cards=hidden, shuffler=FakeShuffler())

    pile.removeLastCard()

    # oldest visible (last) was v4 → must be in discard pile
    assert [c.state() for c in pile.discarded_cards] == ["v4"]

    # visible becomes [v1, v2, v3] then we refill with h2
    assert [c.state() for c in pile.visible_cards] == ["v1", "v2", "v3", "h2"]

    # hidden lost h2, only h1 remains
    assert [c.state() for c in pile.hidden_cards] == ["h1"]


def test_init_raises_when_not_enough_cards_to_reach_four_visible() -> None:
    # total cards = 3 < 4 → constructor should fail in _fill_visible
    visible = _make_cards("v1")
    hidden = _make_cards("h1", "h2")

    with pytest.raises(ValueError, match="Not enough cards in deck"):
        Pile(visible_cards=visible, hidden_cards=hidden, shuffler=FakeShuffler())


def test_removeLastCard_triggers_reshuffle_using_shuffler() -> None:
    # Setup to eventually exhaust hidden while having some discarded cards
    visible = _make_cards("v1", "v2", "v3", "v4")
    hidden = _make_cards("h1")  # single hidden card
    shuffler = FakeShuffler()

    pile = Pile(visible_cards=visible, hidden_cards=hidden, shuffler=shuffler)

    # 1st remove:
    #   discards v4, refills with h1, no reshuffle yet (hidden becomes empty)
    pile.removeLastCard()
    assert shuffler.calls == []

    # 2nd remove:
    #   discards h1, now hidden empty and discarded has [v4, h1]
    #   _fill_visible must call _restore_hidden → shuffler.shuffle([...])
    pile.removeLastCard()

    # Shuffler must have been called exactly once with [v4, h1]
    assert len(shuffler.calls) == 1
    assert [c.state() for c in shuffler.calls[0]] == ["v4", "h1"]

    # After reshuffle, discarded_cards should be empty
    assert [c.state() for c in pile.discarded_cards] == []

    # There are still always 4 visible cards
    assert len(pile.visible_cards) == 4


def test_state_includes_visible_card_states() -> None:
    visible = _make_cards("v1", "v2", "v3", "v4")
    hidden = _make_cards("h1")
    pile = Pile(visible_cards=visible, hidden_cards=hidden, shuffler=FakeShuffler())

    s = pile.state()
    # At minimum, state() should mention visible cards via their state()
    for name in ["v1", "v2", "v3", "v4"]:
        assert name in s
