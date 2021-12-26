import nextcord
from itertools import product
from typing import List, Union, Optional
from ..util.exception import NotFound, ALEDException

CLASSIC_DECK = [i + j for i, j in product(['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'V', 'D', 'R'], ['♥',  '♣', '♦', '♠'])]
TAROT = CLASSIC_DECK + ['C♥', 'C♣', 'C♦', 'C♠', 'Excuse'] + [f"A{i}" for i in range(1, 22)]


class Game:
    def __init__(self, *, players, deck="Classic"):
        """
        Args:
            players (List[nextcord.User]):
            deck Union[str, List[str]]:
        """
        self.players = [Player(member, self) for member in players]
        if isinstance(deck, str):
            if deck == "Classic": self.deck = CLASSIC_DECK
            elif deck == "Tarot": self.deck = TAROT
            else: raise NotFound(f"{deck} was not found in predifined decklist")
        elif isinstance(deck, list):
            self.deck = deck
        else:
            raise ALEDException("Deck must be a str or a List[str]")

    def draw(self):
        try:
            return self.deck.pop()
        except IndexError:
            return None

    def draw_cards(self, number=1):
        result = []
        for i in range(number):
            try:
                result.append(self.deck.pop())
            except IndexError:
                pass
        return result


class Player:
    def __init__(self, member, game):
        """
        Args:
            member (nextcord.User):
            game (Game):
        """
        self.member = member
        self.game = game
        self.hand = []

    def draw(self) -> Optional[str]:
        card = self.game.draw()
        if card:
            self.hand.append(card)
            return card
        else:
            return None

    def draw_cards(self, number=1):
        self.hand += self.game.draw_cards(number)

    @staticmethod
    def get_card_color(card : str) -> str:
        if '♥' in card or '♦' in card:
            return '-'
        elif '♣' in card or '♠' in card:
            return '*'
        else:
            return '+'


    def format_hand(self):
        return "```diff\n{}```".format(
            '\n'.join(f"{self.get_card_color(v)} {i:>2}: {v}") for i, v in enumerate(self.hand))