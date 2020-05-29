from multiprocessing import Pool
from threading import Lock
from collections import defaultdict
from itertools import combinations
from typing import List, Optional

from GameLogic import *
from PokerObjects import *


class AtomicCounter:
    def __init__(self):
        self._value = 0
        self._lock = Lock()

    def increment(self):
        with self._lock:
            self._value += 1

    def get(self):
        with self._lock:
            return self._value


def get_winner(hands: List[Hand], board: Board):
    """Takes in a hands and complete board, returns winning hand or none if tied."""
    if len(board.cards) != 5:
        raise ValueError(
            f"Board is the wrong length: expected length is 5, but given {len(board.cards)}.\n Board == {board}"
        )

    scored_hands = []
    for hand in hands:
        scored_hands.append(find_strongest(hand=hand, board=board))
    scoring_order = get_scoring_order(*scored_hands)
    if len(scoring_order[0]) == 1:
        return scoring_order[0][0]
    else:
        return "Tie"  # currently ignores that 2 hands can tie in 3+ hand set. All ties treated as the same.


def thread_task(board_combination, hands, board, win_dict):
    # win_dict[get_winner(hands, Board(*(board.cards + list(board_combination))))].increment()
    winner = get_winner(hands, Board(*(board.cards + list(board_combination))))
    target = win_dict[winner]
    target.increment()


def get_outs(hands: List[Hand], board: Board):

    # TODO: Fiddle with this to allow it to take in empty hands and get odds for one to win
    deck = [c for c in Deck().cards if c not in [c for hand in hands for c in hand.cards] and c not in board.cards]
    win_dict = defaultdict(int)

    possible_combinations = combinations(deck, 5-len(board.cards))
    for board_combination in possible_combinations:
        current_board = Board(*(board.cards + list(board_combination)))

        if (hand := get_winner(hands, current_board)) is not None:
            win_dict[hand] += 1
        else:
            win_dict["Tie"] += 1

    return win_dict


def get_outs_multithreaded(hands: List[Hand], board: Board):

    win_dict = {hand: AtomicCounter() for hand in [*hands, "Tie"]}

    deck = [c for c in Deck().cards if c not in [c for hand in hands for c in hand.cards] and c not in board.cards]

    pool = Pool(processes=2)
    pool.starmap(thread_task, [[combos, hands, board] for combos in combinations(deck, 5-len(board.cards))])

    return_dict = defaultdict(int)
    for key, item in win_dict.items():
        return_dict[key] = item.get()

    return return_dict

