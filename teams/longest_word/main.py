# Main file for a random word agent.
import capitals as cap

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

class LongestWordAgent(cap.Agent):
    """
    A simple agent which selects the longest playable word from the dictionary.
    """

    # No initialization required.
    def __init__(self):
        pass

    def act(self, state):
        """
        Selects all of the words on the board, returns the first word in the dictionary that we can play.
        """
        pos_to_letters = state.board.find_all_letters()
        letters_to_pos = invert_map(pos_to_letters)
        letters_freq = frequency_map(pos_to_letters.values())

        # Select the first word we can play.
        word_to_play = None
        for word in state.dictionary:
            word_freq = frequency_map(word)
            if frequency_map_contained_by(word_freq, letters_freq):
                if word_to_play is None or len(word_to_play) < len(word):
                    word_to_play = word

        # No valid words to play, do nothing.
        if word_to_play is None:
            return None

        # Compute positions for the letters; a somewhat hacky way to do it.
        positions_to_play = []
        for letter in word_to_play:
            for position in letters_to_pos[letter]:
                if position not in positions_to_play:
                    positions_to_play.append(position)
                    break

        return positions_to_play
