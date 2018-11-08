from capitals import Dictionary, Board, State, LetterGenerator
import capitals as cap

RED_CAPITAL = "RED_CAPITAL"
BLUE_CAPITAL = "BLUE_CAPITAL"
RED = "RED"
BLUE = "BLUE"
EMPTY = "EMPTY"
LETTER_PREFIX="LETTER_"

def getMove(state, dictionary, player):

    myWord = ""
    lets = state.board.find_all_letters()
    letters = {}
    for pos in lets:
        let = lets[pos]
        if let not in letters:
            letters[let] = 0
        letters[let] += 1
    temp = []
    bestAction = []
    bestActionScore = 0
    for word in dictionary.words:
        action = []
        if (len(word) > 3):
            word = word.rstrip()
            # print(word.rstrip())
            word_count = {}
            for character in word:
                if character not in word_count:
                    word_count[character] = 0
                word_count[character] += 1
            valid = True
            for key in word_count:
                if key not in letters or key not in word_count or letters[key] < word_count[key]:
                    valid = False
                    break
            if valid:
                myWord = word
                for character in myWord:
                    for pos in lets:
                        if lets[pos] == character and pos not in action:
                            action.append(pos)
                            break
                score = scoreMove(state,action, player)
                if (score>bestActionScore):
                    bestAction = action
                    bestActionScore = score
    # print(bestActionScore)
    return bestAction if len(bestAction) > 0 else None

def scoreMove(state, action, player):
    # return len(action)
    tiles = action
    player_capital = (player + "_CAPITAL")
    enemy = "RED" if player == "BLUE" else "BLUE"
    enemy_capital = "RED_CAPITAL" if player == "BLUE" else "BLUE_CAPITAL"
    newTiles = 0
    captured = 0

    # Flood-fill from each tile; if a tile is connected to the players territory, then this tile will
    # capture new territory.
    tiles = set(tiles)
    connected_tiles = set()
    for tile in tiles:
        flood_tiles = state.board.floodfill(tile, lambda p, t: t == player or t == (player + "_CAPITAL") or p in tiles)
        is_connected = any(
            map(lambda k: state.board.get_tile(k) == player or state.board.get_tile(k) == (player + "_CAPITAL"), flood_tiles))

        if is_connected:
            connected_tiles.add(tile)

    # Now that we have a set of connected tiles:
    # - Connected tiles become player territory, and all tiles adjacent to them which were enemy territory become letter tiles.
    # - Disconnected tiles just become a new letter.
    result = state.board

    flipped = set()

    captured_capital = False
    enemyCap = state.board.find_single(enemy_capital)
    for tile in tiles:
        if tile in connected_tiles:
            result = result.set_tile(tile, player)
            newTiles+=1
            for adj in cap.adjacent_positions(tile):
                if result.get_tile(adj) == enemy or result.get_tile(adj) == EMPTY:
                    flipped.add(adj)
                elif result.get_tile(adj) == enemy_capital and captured<10000-1:
                    captured+=10000
                    captured_capital = True
                elif result.get_tile(adj) == EMPTY:
                    pass
        else:
            # result = result.set_tile(tile, LETTER_PREFIX + lettergen())
            pass
    captured += len(flipped)
    if enemyCap == None:
        return captured
    return captured+newTiles

class JohnAgent(object):
    def __init__(self):
        pass

    def act(self, state):
        return getMove(state, state.dictionary, state.turn)
