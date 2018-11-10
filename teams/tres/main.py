import random
import copy
import capitals as cap

from collections import deque

def frequency_map(input_list):
    """
    Computes a frequency map of the elements in the list, returning it in a map of the form { element -> count }.
    """
    result = {}
    for elem in input_list:
        if elem not in result:
            result[elem] = 1
        else:
            result[elem] += 1

    return result

def frequency_map_contained_by(first, second):
    """
    Returns true if the frequency counts of all of the items in the first map is less than or equal to
    the frequency counts of the same items in the second map.
    """
    for key in first:
        if key not in second or first[key] > second[key]:
            return False

    return True

def invert_map(input_map):
    """
    Inverts a map from K -> V to V -> [K]. Since values may be duplicates, each value maps to a list of keys which
    mapped to it.
    """
    result = {}
    for key in input_map:
        if input_map[key] not in result:
            result[input_map[key]] = [key]
        else:
            result[input_map[key]].append(key)

    return result

def reorder_tiles(board, tiles, word):
    """
    Re-orders a random selection of tiles so that they form the given word; assumes the tiles have all
    of the letters in the word.
    """
    letters_to_tiles = invert_map({ tile: board.get_letter(tile) for tile in tiles })
    ordered_tiles = []

    for letter in word:
        for tile in letters_to_tiles[letter]:
            if tile in ordered_tiles:
                continue
            ordered_tiles.append(tile)
            break

    return ordered_tiles

def complete_word(letters_to_pos, partial_soln, remaining_freq):
    """
    Completes a word, choosing tiles from the letter -> position mappings which are not in the partial solution
    and which satisfy the remaining needed letter frequencies. Returns a complete solution which contains both
    the partial solution and the extra added tiles.
    """
    result = set(partial_soln)
    for letter, freq in remaining_freq.items():
        needed = freq
        for pos in letters_to_pos[letter]:
            # If we found enough letters, quit.
            if needed == 0:
                break

            # Skip positions already in the partial solution, of course.
            if pos in partial_soln:
                continue

            result.add(pos)
            needed -= 1

    return result

def score_board(board, team):
    """
    From the Bot definition, provides a score which scales with the following characteristics:
    - Killing the enemy by claiming all territory.
    - Claiming the enemy capital, in order to gain a free round.
    - Protecting the local capital from adjacent + connected tiles.
    - Maximize territory gain: i.e., maximize local territory.
    - Minimizing enemy territory: i.e., minimize territory that the enemy holds.
    - TODO: Minimizing letter-adjacency: i.e., minimize number of territory tiles that are adjacent to letter tiles.
    """
    enemy = cap.enemy_color(team)
    our_territory = board.territory(team)
    our_capital = board.capital(team)

    enemy_territory = board.territory(enemy)
    enemy_capital = board.capital(enemy)

    enemy_reachable_letters = set(board.floodfill(enemy_territory, lambda p, t: t == enemy or t == enemy + "_CAPITAL" or t.startswith(cap.LETTER_PREFIX)))

    # First Heuristic: If enemy has no territory, assign maximum score.
    if len(enemy_territory) == 0:
        return 99999999

    # The rest of the heuristics are additive.
    score = 0

    # Second Heuristic: If there is no enemy capital (because we capture it).
    if enemy_capital is None:
        score += 100

    # Third Heuristic: The local capital should not have tiles which are reachable from enemy territory.
    if our_capital is not None:
        for adj in cap.adjacent_positions(our_capital):
            if adj in enemy_reachable_letters:
                score -= 20
            elif board.get_tile(adj).startswith(cap.LETTER_PREFIX):
                score -= 4

    # Fourth Heuristic: We should maximize our own territory.
    score += 2 * len(our_territory)

    # Fifth Heuristic: We should minimize enemy territory.
    score -= 1 * len(enemy_territory)

    return score

def find_best_move_for_word(board, team, word, word_freq, letters_to_pos):
    """
    Finds the best move (based on heuristic scores) for a given board; returns the move as well as it's score.
    """
    # Fancy implementation which looks at every way that a move can be constructed via a breadth first search.
    word_letters = set(word)
    our_territory = board.territory(team)

    # The starting letters are letters in the word adjacent to our territory.
    starting_letters = { adj: board.get_letter(adj)
            for pos in our_territory for adj in cap.adjacent_positions(pos) if board.get_letter(adj) in word_letters }
    starting_available = invert_map(starting_letters)

    # The queue contains (partial action, remaining, available words).
    visited = set([frozenset()])
    queue = deque([(frozenset(), word_freq, starting_available)])
    best_move = None
    best_score = None

    while queue:
        action, remaining, available = queue.popleft()

        # For each remaining letter, look through the available positions for the letter and add them to the queue.
        valid_children = 0
        for letter in remaining:
            if letter not in available:
                continue

            # Create a new remaining count which removes the current letter.
            new_remaining = dict(remaining)
            new_remaining[letter] -= 1
            if new_remaining[letter] == 0:
                del new_remaining[letter]

            # Iterate through each available position, appending _new_ positions.
            for pos in available[letter]:
                if pos in action:
                    continue

                valid_children += 1

                new_action = action | frozenset([pos])
                if new_action in visited:
                    continue
                visited.add(new_action)

                new_available = copy.deepcopy(available)
                for adj in cap.adjacent_positions(pos):
                    pletter = board.get_letter(adj)
                    if pletter is not None and pletter in new_remaining:
                        if pletter in new_available:
                            new_available[pletter].append(adj)
                        else:
                            new_available[pletter] = [adj]

                queue.append((new_action, new_remaining, new_available))

        # If no valid children, then this is a terminal state which we need to complete.
        if valid_children == 0:
            completed = complete_word(letters_to_pos, action, remaining)
            score = score_board(board.use_tiles(completed, team)[0], team)
            if best_move is None or score > best_score:
                best_move, best_score = completed, score

    return reorder_tiles(board, best_move, word), best_score


class L3x1c0nHack3rAgent(cap.Agent):
    """
    A greedy (i.e., non-minimax) agent which focuses on the following objectives:
    - Killing the enemy by claiming all territory.
    - Claiming the enemy capital, in order to gain a free round.
    - Protecting the local capital from adjacent + connected tiles.
    - Maximize territory gain: i.e., maximize local territory.
    - Minimizing letter-adjacency: i.e., minimize number of territory tiles that are adjacent to letter tiles.
    - Minimizing enemy territory: i.e., minimize territory that the enemy holds.

    The agent scans through all playable words on the board and tries many letter choices, choosing the one that
    maximizes the resulting board state.
    """

    def __init__(self):
        # No initialization required.
        pass

    def act(self, state):
        pos_to_letters = state.board.find_all_letters()
        letters_to_pos = invert_map(pos_to_letters)
        letters_freq = frequency_map(pos_to_letters.values())

        # For each word playable on the board...
        best_move = None
        best_score = None
        possible_words = 0
        for word in state.dictionary:
            word_freq = frequency_map(word)
            if not frequency_map_contained_by(word_freq, letters_freq):
                continue
            
            possible_words += 1

            # Choose the tiles which maximize territory gain with this word...
            move, score = find_best_move_for_word(state.board, state.turn, word, word_freq, letters_to_pos)
            if best_move is None or score > best_score:
                best_move, best_score = move, score

        return best_move
