import random
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

def choose_tiles_maximizing_territory(board, team, letters_to_pos, word, word_freq):
    """
    Heuristically chooses tiles on the board which maximize the amount of territory gained. Assumes that the
    word in word freq can be created via tiles on the board.
    """
    # This first pass is a greedy approach, which assigns distance scores to every letter tile on the board;
    # tiles unreachable from our territory are assigned a score of 20 to de-incentize choosing them.
    enemy_team = cap.RED if team == cap.BLUE else cap.BLUE

    # Compute the distance scores for reachable letters from our territory.
    scores = {}
    team_tiles = board.find_all_matching(lambda p, t: t == team or t == team + "_CAPITAL")
    closed = set(team_tiles)
    queue = deque([(tile, 0) for tile in team_tiles])
    while queue:
        elem, dist = queue.popleft()
        scores[elem] = dist

        for adj in cap.adjacent_positions(elem):
            if adj in closed:
                continue

            letter = board.get_letter(adj)
            if letter is not None and letter in word_freq:
                queue.append((adj, dist + 1))
                closed.add(adj)

    # Invert the map into distance -> [words at that distace]
    distance_to_tiles = invert_map(scores)

    # Select as many letters as possible from distance 1, then reachable letters from distance 2, etc.
    selected_tiles = set()
    reachable_tiles = set(distance_to_tiles[1] if 1 in distance_to_tiles else [])
    remaining_frequency = dict(word_freq)

    for dist in distance_to_tiles:
        # For each distance, select as many reachable letters as possible.
        random.shuffle(distance_to_tiles[dist])
        for tile in distance_to_tiles[dist]:
            letter = board.get_letter(tile)

            # If the tile is reachable & in the remaining frequency, add it and update the frequency.
            if tile in reachable_tiles and letter in remaining_frequency:
                selected_tiles.add(tile)

                # Update the remaining frequency counts.
                remaining_frequency[letter] -= 1
                if remaining_frequency[letter] == 0:
                    del remaining_frequency[letter]

                # Add new reachable tiles.
                reachable_tiles = reachable_tiles | set(cap.adjacent_positions(tile))

            # Quit if we've finished finding all letters.
            if len(remaining_frequency) == 0:
                break

    # At this point, we just need to complete the word using the un-selected tiles.
    for letter in remaining_frequency:
        num_remaining = remaining_frequency[letter]
        for pos in letters_to_pos[letter]:
            if pos not in selected_tiles:
                selected_tiles.add(pos)
                num_remaining -= 1

            if num_remaining == 0:
                break

    # TODO: More advanced statistics requested.
    new_board, capital_captured = board.use_tiles(selected_tiles, team, lambda: "LETTER_A")
    return reorder_tiles(board, selected_tiles, word), \
            (len(selected_tiles), len(board.find_all_matching(lambda p, t: t == enemy_team or t == enemy_team + "_CAPITAL")) \
            - len(new_board.find_all_matching(lambda p, t: t == enemy_team or t == enemy_team + "_CAPITAL")) \
            + (10 if capital_captured else 0))

class L3x1c0nHack3rAgent(cap.Agent):
    def __init__(self):
        # No initialization required.
        pass

    def act(self, state):
        pos_to_letters = state.board.find_all_letters()
        letters_to_pos = invert_map(pos_to_letters)
        letters_freq = frequency_map(pos_to_letters.values())

        # For each word playable on the board...
        best_move = None
        best_word = None
        best_move_stats = None
        possible_words = 0
        for word in state.dictionary:
            word_freq = frequency_map(word)
            if not frequency_map_contained_by(word_freq, letters_freq):
                continue
            
            possible_words += 1

            # Choose the tiles which maximize territory gain with this word...
            move, stats = choose_tiles_maximizing_territory(state.board, state.turn, letters_to_pos, word, word_freq)
            if best_move is None or best_move_stats < stats:
                best_word = word
                best_move = move
                best_move_stats = stats

        return best_move
