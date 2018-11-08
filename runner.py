#!/usr/bin/env python3
# Runner script for Capitals AIs - dynamically loads python modules which provide an Agent implementation,
# and runs them against each other.

import os
import sys
import signal
import importlib
import argparse
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

class TimedOutException(Exception):
    """
    Trivial exception type which is thrown when an action times out.
    """
    pass

def call_with_timeout(timeout, func, *args):
    """
    Calls a function with a given amount of timeout; if the function times out, a TimedOutException is raised.
    Note that this timeout functionality only works on unix machines.
    """
    def handler(signum, frame):
        raise TimedOutException()

    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)
    result = func(*args)
    signal.alarm(0)

    return result

def run_game(red_competitor, blue_competitor, dictionary, max_rounds=100, turn_timeout=10, verbose=True, logfile=None):
    """
    Run a game of capitals between two competitors. Returns the winner (either RED for the red competitor or BLUE for
    the blue competitor), and the game log.

    If logfile is specified, then the game log is dumped to the given log file as well.
    """
    game_log = GameLog.initial(State.initial(dictionary), red_competitor.name, blue_competitor.name)

    red_agent = red_competitor.create_agent()
    blue_agent = blue_competitor.create_agent()

    turn_skips = 0
    while game_log.winner() is None and game_log.current_round() <= max_rounds:
        # TODO: Pass deep copies of current state objects, to prevent people from meddling with them.
        state = game_log.current_state()
        competitor = red_competitor if state.turn == capitals.RED else blue_competitor
        agent = red_agent if state.turn == capitals.RED else blue_agent

        action = None
        timeout = False
        try:
            action = call_with_timeout(turn_timeout, agent.act, state)
        except TimedOutException:
            timeout = True

        # Skip agents who forgo their turn.
        if action is None:
            if verbose:
                if not timeout:
                    print("[%s (%s)] SKIPPED TURN" % (competitor.name, state.turn))
                else:
                    print("[%s (%s)] TIMED OUT" % (competitor.name, state.turn))

            turn_skips += 1 if not timeout else 0
            game_log.add_turn(None, state.next_turn(state.board, False))
        else:
            try:
                game_log.act(action)
                turn_skips = 0
                if verbose:
                    print("[%s (%s)] PLAYING '%s'" % (competitor.name, state.turn, state.board.get_word(action)))
            except:
                if verbose:
                    print("[%s (%s)] INVALID PLAY at positions %s" % (competitor.name, state.turn, repr(action)))
                turn_skips += 1

        # If both agents skipped their turn twice (due to invalid board state, not timeouts), the game state must be
        # broken, so kill the board.
        if turn_skips >= 4:
            break

    # Dump the log to the log file, if it's not none.
    if logfile is not None:
        GameLog.to_file(game_log, logfile)

    return game_log.winner(), game_log


def run_series(competitor1, competitor2, dictionary, num_games=5, turn_timeout=10, max_rounds=100, verbose=True, logdir=None):
    """
    Runs a series of games between two competitors, returning the number of wins for each competitor as a tuple of
    (competitor1Wins, competitor2Wins, ties), as well as a list of game logs.

    If logdir is not None, then logs will be dumped to the given directory, named by the game number.
    """

    if logdir is not None:
        if not os.path.isdir(logdir):
            os.mkdir(logdir)

    wins = [0, 0, 0]
    logs = []
    for game_num in range(num_games):
        if verbose:
            print()
            print("== GAME %d == " % game_num)
        # TODO: Lots of code duplication, relatively suboptimal.
        logfile = os.path.join(logdir, str(game_num) + ".json") if logdir is not None else None
        if game_num % 2 == 0:
            winner, log = run_game(competitor1, competitor2, dictionary, max_rounds=max_rounds, verbose=verbose,
                    turn_timeout=turn_timeout, logfile=logfile)

            logs.append(log)
            if winner == capitals.RED:
                wins[0] += 1
            elif winner == capitals.BLUE:
                wins[1] += 1
            else:
                wins[2] += 1
        else:
            winner, log = run_game(competitor2, competitor1, dictionary, max_rounds=max_rounds, verbose=verbose,
                    logfile=logfile)

            logs.append(log)
            if winner == capitals.RED:
                wins[1] += 1
            elif winner == capitals.BLUE:
                wins[0] += 1
            else:
                wins[2] += 1

    return tuple(wins), logs


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="Run games between AIs")
    argparser.add_argument("first_agent", type=str, help="First agent to run")
    argparser.add_argument("second_agent", type=str, help="Second agent to run")
    argparser.add_argument("--max_rounds", type=int, default=100, help="Maximum number of rounds per game")
    argparser.add_argument("--games", type=int, default=5, help="Number of games to run")
    argparser.add_argument("--logdir", type=str, default=None, help="Directory to dump log files to")
    argparser.add_argument("--turn_timeout", type=int, default=10, help="Number of seconds allowed per turn")
    args = argparser.parse_args()

    dictionary = Dictionary.from_file("dict.txt")
    print("Dictionary: %d words" % len(dictionary))

    first_agent = None
    try:
        first_agent = Competitor.from_module("teams." + args.first_agent)
    except:
        print("Failed to load agent '%s'" % args.first_agent)
        sys.exit(1)

    second_agent = None
    try:
        second_agent = Competitor.from_module("teams." + args.second_agent)
    except:
        print("Failed to load agent '%s'" % args.second_agent)
        sys.exit(1)

    print("Game Series: %s vs. %s (%d games, %d rounds/game)" % (first_agent.name, second_agent.name, args.games, args.max_rounds))
    scores, logs = run_series(first_agent, second_agent, dictionary, num_games=args.games, max_rounds=args.max_rounds,
            turn_timeout=args.turn_timeout, logdir=args.logdir)

    print()
    print("== FINAL SCORES ==")
    print("%s wins %d, %d ties, %s wins %d" % (first_agent.name, scores[0], scores[2], second_agent.name, scores[1]))
