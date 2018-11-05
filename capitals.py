#!/usr/bin/env python3
# Implementation of the Capitals mobile game, with an API amenable to use in AI.

import random

from collections import deque

class Dictionary(object):
    """
    A dictionary of valid words.
    """

    def __init__(self, words):
        self.words = words

    def __len__(self):
        return len(self.words)

    def contains(self, word):
        """
        Return true if the dictionary contains the given word (irrespective of case).
        """
        return word.upper() in self.words

    @staticmethod
    def from_file(file_name):
        """
        Load a dictionary from a dictionary file, which should consist of one word per line.
        """
        words = set()
        with open(file_name, "r") as dict_file:
            for line in dict_file:
                words.add(line.upper())

        return Dictionary(words)

    @staticmethod
    def from_list(word_list):
        """
        Load a dictionary from a Python list.
        """
        return Dictionary(set(map(lambda k: k.upper(), word_list)))


class LetterGenerator(object):
    """
    Class for generating letters given some distribution; for now, this distribution is independent of the current
    letters on the board.
    """
    def __init__(self):
        # Letter distribution uses the Scrabble distribution for now.
        self.letter_dist = [('A', 9), ('B', 2), ('C', 2), ('D', 4), ('E', 12), ('F', 2), ('G', 3), ('H', 2),
                ('I', 9), ('J', 1), ('K', 1), ('L', 4), ('M', 2), ('N', 6), ('O', 8), ('P', 2), ('Q', 1),
                ('R', 6), ('S', 4), ('T', 6), ('U', 4), ('V', 2), ('W', 2), ('X', 1), ('Y', 2), ('Z', 1)]

        # List where a letter has been duplicated <weight> times.
        self.letters_dup = []
        for letter, weight in self.letter_dist:
            self.letters_dup += [letter] * weight

    def sample(self):
        """
        Randomly sample a letter from the letter distribution.
        """
        return random.choice(self.letters_dup)


# Constraints for valid positions in the board; each Y value has a starting X and ending X (both inclusive).
BOARD_CONSTRAINTS = {
    0: (0, 1),
    1: (0, 3),
    2: (0, 5),
    3: (0, 6),
    4: (0, 6),
    5: (0, 6),
    6: (1, 6),
    7: (3, 6),
    8: (5, 6)
}

# Offsets to obtain the adjacent tiles for a given tile.
ADJACENT_OFFSETS = [(-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (-1, -1)]

# Starting positions of the red/blue capitals.
RED_START_POS = (1, 1)
BLUE_START_POS = (5, 7)

# Constants for the possible tile types in the gameboard.
RED_CAPITAL = "RED_CAPITAL"
BLUE_CAPITAL = "BLUE_CAPITAL"
RED = "RED"
BLUE = "BLUE"
EMPTY = "EMPTY"
LETTER_PREFIX="LETTER_"

def valid_position(pos):
    """
    Return True if the given position is valid and inside the grid, and false otherwise.
    """
    x_constraint = BOARD_CONSTRAINTS[pos[1]] if pos[1] in BOARD_CONSTRAINTS else (1, 0)
    return pos[0] >= x_constraint[0] and pos[0] <= x_constraint[1]

# TODO: Precompute this, no point in remaking it every time.
def valid_positions():
    """
    Return a list of all valid positions on the board.
    """
    result = []
    for y, x_constraint in BOARD_CONSTRAINTS.items():
        x_min, x_max = x_constraint
        for x in range(x_min, x_max + 1):
            result.append((x, y))

    return result

def adjacent_positions(pos):
    """
    Return a list of adjacent position tuples to the given position; only returns
    positions that are in bounds of the grid.
    """
    result = []
    for offset_x, offset_y in ADJACENT_OFFSETS:
        offset_pos = (pos[0] + offset_x, pos[1] + offset_y)
        if valid_position(offset_pos):
            result.append(offset_pos)

    return result

class Board(object):
    """
    A game board of Capitals; contains methods for finding valid positions/adjacent positions, and tracks
    the state of the letters on the board.

    Positions on the game board are in axial coordinates (the X direction is up and to the right, the Y coordinate
    is straight down); (0, 0) is at the upper-left hand corner of the board.
    """

    def __init__(self, board = None):
        self.board = board or {}

        for pos, tile_type in self.board.items():
            if not valid_position(pos):
                raise ValueError("Passed invalid position " + repr(pos) + " to board constructor")

    @staticmethod
    def initial(lettergen):
        """
        Return the default starting board, given a letter generator.
        """
        board = {}
        board[RED_START_POS] = RED_CAPITAL
        board[BLUE_START_POS] = BLUE_CAPITAL

        for adj in adjacent_positions(RED_START_POS):
            board[adj] = LETTER_PREFIX + lettergen.sample()

        for adj in adjacent_positions(BLUE_START_POS):
            board[adj] = LETTER_PREFIX + lettergen.sample()

        return Board(board)

    def red_capital(self):
        """
        Return the position of the red capital, or None if there is no capital.
        """
        return self.find_single(RED_CAPITAL)

    def blue_capital(self):
        """
        Return the position of the blue capital, or None if there is no capital.
        """
        return self.find_single(BLUE_CAPITAL)

    def find_single(self, tile_type):
        """
        Return the position of a tile which has the given tile type; no gauruntees are made about
        which specific tile are returned if the choice is ambiguous.
        """
        for pos in valid_positions():
            if self.get_tile(pos) == tile_type:
                return pos

        return None

    def find_all(self, tile_type):
        """
        Return the position of all tiles which have the given type.
        """
        return self.find_all_matching(lambda p, t: t == tile_type)

    def find_all_matching(self, predicate):
        """
        Return the position of all (pos, tile_type) pairs which return True when passed to the given predicate.
        """
        positions = []
        for pos in valid_positions():
            if predicate(pos, self.get_tile(pos)):
                positions.append(pos)

        return positions

    def find_all_letters(self):
        """
        Return a map of positions -> letter at that position, for all of the letters on the board.
        """
        letter_positions = self.find_all_matching(lambda p, t: t.startswith(LETTER_PREFIX))
        return { pos: self.get_tile(pos)[len(LETTER_PREFIX):] for pos in letter_positions }

    def floodfill(self, start, predicate):
        """
        Performs a flood-fill starting at position <start>, using the given predicate on every adjacent (position,
        tile_type); if the predicate is True, the flood-fill will extend to that position.

        Returns a set of all of the visited positions in the flood-fill.
        """
        visited = set([start])
        queued = deque([start])

        while len(queued) > 0:
            pos = queued.popleft()
            for adj in adjacent_positions(pos):
                if adj in visited:
                    continue

                if predicate(adj, self.get_tile(adj)):
                    visited.add(adj)
                    queued.append(adj)

        return visited

    def set_tile(self, position, new_type):
        """
        Return a new board where the tile at the given position has been set to the given type.
        """
        if not valid_position(position):
            raise IndexError("Position " + repr(position) + " is not a valid board position")

        new_board = dict(self.board)
        new_board[position] = new_type

        return Board(new_board)

    def get_tile(self, position):
        """
        Return the tile at the given position (if there is no tile there, empty is returned).
        """
        if position not in self.board:
            if valid_position(position):
                return EMPTY
            else:
                raise IndexError("Position " + repr(position) + " is not a valid board position")

        return self.board[position]

    def get_letter(self, position):
        """
        Get the letter on the grid at the current position if it has one; otherwise, return None.
        """
        tile = self.get_tile(position)
        if tile.startswith(LETTER_PREFIX):
            return tile[len(LETTER_PREFIX):]
        else:
            return None

    def use_tiles(self, tiles, player, lettergen):
        """
        Given a list of tiles and the player who selected those tiles:
        - Finds all of the tiles connected to the players territory (either directly or via other selected tiles), and adds them to the players territory.
        - If any of the connected tiles are adjacent to enemy territory, "captures" that territory by replacing it with
          letter tiles.

        Returns a tuple of (new board, capital_captured); if capital_captured is True, then this operation captured the
        enemy capital.
        """
        # Verify all played tiles are letter tiles, and in bounds.
        for tile in tiles:
            if not valid_position(tile):
                raise ValueError("Tile " + repr(tile) + " is not a valid position on the board!")
            elif self.get_letter(tile) is None:
                raise ValueError("Tile " + repr(tile) + " is type " + self.get_tile(tile) + ", not letter!")

        # Compute some constants.
        player_capital = (player + "_CAPITAL")
        enemy = "RED" if player == "BLUE" else "BLUE"
        enemy_capital = "RED_CAPITAL" if player == "BLUE" else "BLUE_CAPITAL"

        # Flood-fill from each tile; if a tile is connected to the players territory, then this tile will
        # capture new territory.
        tiles = set(tiles)
        connected_tiles = set()
        for tile in tiles:
            flood_tiles = self.floodfill(tile, lambda p, t: t == player or t == (player + "_CAPITAL") or p in tiles)
            is_connected = any(map(lambda k: self.get_tile(k) == player or self.get_tile(k) == (player + "_CAPITAL"), flood_tiles))

            if is_connected:
                connected_tiles.add(tile)

        # Now that we have a set of connected tiles:
        # - Connected tiles become player territory, and all tiles adjacent to them which were enemy territory become letter tiles.
        # - Disconnected tiles just become a new letter.
        result = self
        captured_capital = False
        for tile in tiles:
            if tile in connected_tiles:
                result = result.set_tile(tile, player)
                for adj in adjacent_positions(tile):
                    if result.get_tile(adj) == enemy:
                        result = result.set_tile(adj, LETTER_PREFIX + lettergen.sample())
                    elif result.get_tile(adj) == enemy_capital:
                        result = result.set_tile(adj, LETTER_PREFIX + lettergen.sample())
                        captured_capital = True
            else:
                result = result.set_tile(tile, LETTER_PREFIX + lettergen.sample())

        return (result, captured_capital)


class State(object):
    """
    A state of the game of Capitals.
    """

    def __init__(self, dictionary, board = Board(), lettergen = LetterGenerator(), turn = "RED", round = 1, enemy_capital_captured = False):
        """
        Create a new game state. The board should be a Board instance; the turn should be
        "RED" for the red player, or "BLUE" for the blue player.
        """
        self.dictionary = dictionary
        self.lettergen = lettergen
        self.board = board
        self.turn = turn
        self.round = round

    @staticmethod
    def initial(dictionary, lettergen = LetterGenerator()):
        """
        Compute the initial game state as the game starts.
        """
        board = Board.initial(lettergen)
        return State(dictionary, board, lettergen)

    def winner(self):
        """
        Returns the winner (RED or BLUE) if a winner is apparent; otherwise, returns None.
        """
        if len(self.board.find_all_matching(lambda p, t: t == RED or t == RED_CAPITAL)) == 0:
            return BLUE
        elif len(self.board.find_all_matching(lambda p, t: t == BLUE or t == BLUE_CAPITAL)) == 0:
            return RED
        else:
            return None

    def next_turn(self, next_board, capital_captured):
        """
        Return a new state with a new game board; automatically increments the turn and round appropriately
        depend on whether or not the capital was captured.
        """
        increment_round = capital_captured or (self.turn == BLUE)
        next_player = self.turn if capital_captured else (RED if self.turn == BLUE else BLUE)
        next_round = self.round + 1 if increment_round else self.round
        return State(self.dictionary, next_board, self.lettergen, next_player, next_round)

    def act(self, played_positions):
        """
        Takes an action for the given player's turn (consisting of a list of board positions to take), returning a new
        GameState with the result if successful, or an error (TODO) if the action fails.
        """
        # To act, first collect all of the played positions and check that they are in bounds and form a word.
        word = ""
        for position in played_positions:
            letter = self.board.get_letter(position)
            if letter is None:
                raise ValueError("Invalid play: position " + repr(position) + " is not a letter!")

            word += letter

        # Check that the letter forms a valid word.
        if not self.dictionary.contains(word):
            raise ValueError("Invalid play: word '" + word + "' is not a word in the dictionary!")

        # Check if the enemy has a capital; if they don't, we'll try to give them a new one after this turn ends.
        enemy_has_capital = (self.board.red_capital() if self.turn == BLUE else self.board.blue_capital()) is not None

        # Everything seems to be in order, go ahead and swap the tiles.
        new_board, capital_captured = self.board.use_tiles(played_positions, self.turn, self.lettergen)

        # If the enemy didn't have a capital, choose a new spot for it from their normal colored spots.
        if not enemy_has_capital:
            enemy = (RED if self.turn == BLUE else BLUE)
            enemy_spots = self.board.find_all(enemy)
            if len(enemy_spots) > 0:
                position = random.choice(enemy_spots)
                new_board = new_board.set_tile(position, enemy + "_CAPITAL")

        return self.next_turn(new_board, capital_captured)

