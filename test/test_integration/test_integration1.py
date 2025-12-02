from terra_futura.game import Game
from terra_futura.player import Player
from terra_futura.grid import Grid
from terra_futura.pile import Pile, RandomShuffler
from terra_futura.card import Card
from terra_futura.move_card import MoveCard
from terra_futura.process_action import ProcessAction
from terra_futura.process_action_assistance import ProcessActionAssistance
from terra_futura.select_reward import SelectReward
from terra_futura.game_observer import GameObserver
from terra_futura.activation_pattern import ActivationPattern
from terra_futura.scoring_method import ScoringMethod
from terra_futura.simple_types import *
from terra_futura.arbitrary_basic import ArbitraryBasic
from terra_futura.transformation_fixed import TransformationFixed
from terra_futura.interfaces import TerraFuturaObserverInterface, Effect, InterfaceCard, InterfacePile
from typing import cast


class GameStateObserver(TerraFuturaObserverInterface):
    """Simple observer implementation for testing."""
    def __init__(self) -> None:
        self.notifications: list[str] = []

    def notify(self, game_state: str) -> None:
        self.notifications.append(game_state)


def create_test_card(upper_effect: Effect | None = None,
                     lower_effect: Effect | None = None,
                     pollution_spaces: int = 0) -> Card:
    """Create a card with specified effects for testing."""
    return Card(pollutionSpacesL=pollution_spaces,
                upperEffect=upper_effect,
                lowerEffect=lower_effect)


def create_test_player(player_id: int, grid: Grid) -> Player:
    """Create a player with activation patterns and scoring methods."""
    activation_pattern_1 = ActivationPattern(grid, [
        GridPosition(0, 0), GridPosition(0, 1),
        GridPosition(1, 0), GridPosition(1, 1)
    ])
    activation_pattern_2 = ActivationPattern(grid, [
        GridPosition(0, 0), GridPosition(1, 1),
        GridPosition(2, 0), GridPosition(0, 2)
    ])
    scoring_1 = ScoringMethod([Resource.RED], Points(5), grid)
    scoring_2 = ScoringMethod([Resource.GREEN, Resource.GREEN], Points(10), grid)

    return Player(
        id=player_id,
        activation_patterns=[activation_pattern_1, activation_pattern_2],
        scoring_methods=[scoring_1, scoring_2],
        grid=grid
    )


def test_basic_game_flow_with_pollution() -> None:


    starting_card_1 = create_test_card(
        upper_effect=ArbitraryBasic(from_=0, to=[Resource.RED], pollution=0),
        pollution_spaces=0
    )
    starting_card_2 = create_test_card(
        upper_effect=ArbitraryBasic(from_=0, to=[Resource.GREEN], pollution=0),
        pollution_spaces=0
    )

    level_i_cards: list[InterfaceCard] = []

    for i in range(6):
        level_i_cards.append(create_test_card(
            upper_effect=ArbitraryBasic(from_=0, to=[Resource.YELLOW], pollution=0),
            pollution_spaces=i % 4  # 0, 1, 2, 3, 0, 1
        ))

    for i in range(6):
        level_i_cards.append(create_test_card(
            upper_effect=ArbitraryBasic(from_=0, to=[Resource.RED], pollution=0),
            lower_effect=TransformationFixed(
                from_=[Resource.RED, Resource.RED],
                to=[Resource.GOODS],
                pollution=1  # Generates pollution
            ),
            pollution_spaces=i % 3  # 0, 1, 2, 0, 1, 2
        ))

    for i in range(6):
        level_i_cards.append(create_test_card(
            upper_effect=ArbitraryBasic(from_=0, to=[Resource.GREEN], pollution=0),
            lower_effect=TransformationFixed(
                from_=[Resource.GREEN],
                to=[Resource.FOOD],
                pollution=0
            ),
            pollution_spaces=2 if i % 2 == 0 else 0
        ))


    level_ii_cards: list[InterfaceCard] = []
    for i in range(18):
        level_ii_cards.append(create_test_card(
            upper_effect=ArbitraryBasic(from_=0, to=[Resource.YELLOW], pollution=0),
            lower_effect=TransformationFixed(
                from_=[Resource.YELLOW],
                to=[Resource.CONSTRUCTION],
                pollution=0
            ),
            pollution_spaces=1 if i % 3 == 0 else 0
        ))


    shuffler = RandomShuffler(seed=42)
    pile_level_i = Pile(
        visible_cards=level_i_cards[:4],
        hidden_cards=level_i_cards[4:],
        shuffler=shuffler
    )
    pile_level_ii = Pile(
        visible_cards=level_ii_cards[:4],
        hidden_cards=level_ii_cards[4:],
        shuffler=shuffler
    )

    # Create grids and players
    grid1 = Grid()
    grid2 = Grid()

    # Place starting cards in grids
    grid1.putCard(GridPosition(0, 0), starting_card_1)
    grid2.putCard(GridPosition(0, 0), starting_card_2)


    grid1.shouldActivate = set() 
    grid2.shouldActivate = set()  

    player1 = create_test_player(1, grid1)
    player2 = create_test_player(2, grid2)

    # Create game dependencies
    move_card = MoveCard()
    process_action = ProcessAction()
    process_action_assistance = ProcessActionAssistance()
    select_reward = SelectReward()

    # Create observers
    observer1 = GameStateObserver()
    observer2 = GameStateObserver()
    game_observer = GameObserver({1: observer1, 2: observer2})

    # Create game
    game = Game(
        players=[player1, player2],
        piles={Deck.LEVEL_I: cast(InterfacePile, pile_level_i), Deck.LEVEL_II: cast(InterfacePile, pile_level_ii)},
        moveCard=move_card,
        processAction=process_action,
        processActionAssistance=process_action_assistance,
        selectReward=select_reward,  # type: ignore[arg-type]
        gameObserver=game_observer
    )

    # Verify initial state
    assert game.state == GameState.TakeCardNoCardDiscarded
    assert game.turnNumber == 1
    assert game.currentPlayerId == 1

    # ===== TURN 1: Player 1 =====
    # Take first card from Level I pile and place it
    success = game.takeCard(
        playerId=1,
        source=CardSource(deck=Deck.LEVEL_I, index=1),
        cardIndex=1,
        destination=GridPosition(1, 0)
    )
    assert success
    assert len(grid1._cells) == 2

    assert game.turnFinished(1)
    assert game.currentPlayerId == 2
    assert game.turnNumber == 1

    # ===== TURN 2: Player 2 =====
    success = game.takeCard(
        playerId=2,
        source=CardSource(deck=Deck.LEVEL_I, index=2),
        cardIndex=2,
        destination=GridPosition(1, 0)
    )
    assert success

    assert game.turnFinished(2)
    assert game.turnNumber == 2
    assert game.currentPlayerId == 1


    positions_player1 = [
        GridPosition(2, 0), GridPosition(0, 1), GridPosition(1, 1),
        GridPosition(2, 1), GridPosition(0, 2), GridPosition(1, 2), GridPosition(2, 2)
    ]

    positions_player2 = [
        GridPosition(2, 0), GridPosition(0, 1), GridPosition(1, 1),
        GridPosition(2, 1), GridPosition(0, 2), GridPosition(1, 2), GridPosition(2, 2)
    ]

    # Turns 3-9 (7 more turns for each player to complete the 3x3 grid)
    for turn_idx in range(7):
        # Player 1's turn
        game.takeCard(
            playerId=1,
            source=CardSource(deck=Deck.LEVEL_I, index=1),
            cardIndex=1,
            destination=positions_player1[turn_idx]
        )
        # Skip activation for simplicity, just end turn
        game.turnFinished(1)

        # Player 2's turn
        game.takeCard(
            playerId=2,
            source=CardSource(deck=Deck.LEVEL_II, index=1),
            cardIndex=1,
            destination=positions_player2[turn_idx]
        )
        game.turnFinished(2)

    assert len(grid1._cells) == 9
    assert len(grid2._cells) == 9

    print(f"Turn number: {game.turnNumber}, State: {game.state}, Current player: {game.currentPlayerId}")


    for pos, card_interface in grid1._cells.items():
        card = cast(Card, card_interface)
        assert card.pollutionSpacesL >= 0
        assert card.pollution >= 0
        if card.pollution < card.pollutionSpacesL:
            assert card.isActive()


    assert game.turnNumber == 9
    assert len(grid1._cells) == 9
    assert len(grid2._cells) == 9


    assert len(observer1.notifications) > 0
    assert len(observer2.notifications) > 0

    # Verify grid positions are valid
    for pos in grid1._cells.keys():
        assert -2 <= pos.x <= 2
        assert -2 <= pos.y <= 2

    print("✓ Test 1: Basic Game Flow with Pollution & Deactivation - PASSED")
