#!/usr/bin/env python3
# Runner script for Capitals AIs - dynamically loads python modules which provide an Agent implementation,
# and runs them against each other.

import os
import importlib
import capitals

from capitals import State, Dictionary, GameLog, Board

class Competitor(object):
    """
    A competitor in an AI competition; contains basic metadata as well as a factory for creating an agent.
    """

    def __init__(self, name, creators, agent_class):
        self.name = name
        self.creators = creators
        self.agent_class = agent_class

    def create_agent(self):
        """
        Create a new agent for this competitor.
        """
        return self.agent_class()

    @staticmethod
    def from_module(module):
        """
        Load a competitor from a folder, using the folder's config.py in order to figure out AI information.
        """
        # Extract configuration information.
        try:
            config = importlib.import_module(module + ".config")
            name = config.Name
            creators = config.Creators
            agent_class = config.Agent
            return Competitor(name, creators, agent_class)
        except:
            raise ValueError("Fail to import configuration at " + (module + ".config"))

def run_game(red_competitor, blue_competitor, dictionary, max_rounds=100):
    """
    Run a game of capitals between two competitors. Returns the winner (either RED for the red competitor or BLUE for
    the blue competitor), and the game log.
    """
    game_log = GameLog.initial(State.initial(dictionary))

    red_agent = red_competitor.create_agent()
    blue_agent = blue_competitor.create_agent()

    turn_skips = 0
    while game_log.winner() is None and game_log.current_round() <= max_rounds:
        # TODO: Pass deep copies of current state objects, to prevent people from meddling with them.
        state = game_log.current_state()
        action = None
        if game_log.current_turn() == capitals.RED:
            action = red_agent.act(state)
        else:
            action = blue_agent.act(state)

        # Skip agents who forgo their turn.
        if action is None:
            turn_skips += 1
            game_log.add_turn(None, state.next_turn(state.board, False))

            # If both agents skipped their turn, the game state must be broken, so kill the board.
            if turn_skips >= 2:
                return None, game_log

            continue
        else:
            turn_skips = 0
            game_log.act(action)

    return game_log.winner(), game_log

if __name__ == "__main__":
    dictionary = Dictionary.from_file("dict.txt")
    print("Dictionary: %d words" % len(dictionary))

    first_comp = Competitor.from_module("teams.first_word")
    longest_comp = Competitor.from_module("teams.longest_word")
    winner, log = run_game(first_comp, longest_comp, dictionary)
    print("FIRST" if winner == "RED" else "LONGEST")
    GameLog.to_file(log, "log.json")
