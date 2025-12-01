from .simple_types import Resource, GridPosition
from .interfaces import ProcessActionAssistanceInterface, InterfaceGrid, InterfaceCard, PlayerInterface
from collections import Counter

class ProcessActionAssistance(ProcessActionAssistanceInterface):
    def activateCard(self, card: InterfaceCard, grid: InterfaceGrid, assistingPlayer: PlayerInterface, 
                     assistingCard: InterfaceCard, inputs: list[tuple[Resource, GridPosition]], 
                     outputs: list[tuple[Resource, GridPosition]], 
                     pollution: list[GridPosition]) -> bool:
        
        
        """Checks whether the action is valid, and if so performs it."""
        if card.hasAssistance() == False:
            return False

        otherGrid = assistingPlayer.getGrid()
        
        if not card.isActive() or not assistingCard.isActive():
            return False

        #check pollution for each position
        counted_pollution = Counter(pollution)
        for position, count in counted_pollution.items():
            pollution_card = grid.getCard(position)
            if pollution_card is None:
                return False
            if not pollution_card.canPlacePollution(count):
                return False

        #check inputs for each position
        inputs_grouped: dict[GridPosition, list[Resource]] = {}
        for resource, position in inputs:
            inputs_grouped.setdefault(position, []).append(resource)

        for position, resources in inputs_grouped.items():
            input_card = grid.getCard(position)
            if input_card is None:
                return False
            if not input_card.canGetResources(resources):
                return False

        otherPlayerCard = None
        for row in range(-2, 3):
            for col in range(-2, 3):
                c = otherGrid.getCard(GridPosition(row, col))
                if c is not None and c.state() == assistingCard.state():
                    otherPlayerCard = otherGrid.getCard(GridPosition(row, col))
        
        if not otherPlayerCard:
            return False

        #check outputs for each position
        outputs_grouped: dict[GridPosition, list[Resource]] = {}
        outputs_resources: list[Resource] = []
        for resource, position in outputs:
            outputs_grouped.setdefault(position, []).append(resource)
        if len(outputs_grouped) > 1:
            return False

        elif len(outputs_grouped) == 1:
            output_card_position = next(iter(outputs_grouped))
            outputs_resources = outputs_grouped[output_card_position]
            output_card = grid.getCard(output_card_position)
            if output_card is None:
                return False
            if not card.canPutResources(outputs_resources) or not output_card.hasAssistance() or not card.state() == output_card.state():
                return False

        inputs_resources: list[Resource] = [input[0] for input in inputs]

        if assistingCard.check(inputs_resources, outputs_resources, len(pollution)) or assistingCard.checkLower(inputs_resources, outputs_resources, len(pollution)):
            #perform action
            for position, count in counted_pollution.items():
                pollution_card = grid.getCard(position)
                if pollution_card is None:
                    return False
                pollution_card.placePollution(count)
            for position, resources in inputs_grouped.items():
                output_card = grid.getCard(position)
                if output_card is None:
                    return False
                output_card.getResources(resources)
            for position, resources in outputs_grouped.items():
                input_card = grid.getCard(position)
                if input_card is None:
                    return False
                input_card.putResources(resources)
            #SelectReward()  
            return True

        return False
