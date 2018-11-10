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
    bestActionScore = -10000
    words = []
    for word in dictionary.words:
        action = []
        if (len(word) > 1):
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
                words.append(word)
                word_arr = []

                for character in myWord:
                    let_arr = []
                    for pos in lets:
                        if lets[pos] == character:
                            let_arr.append(pos)
                    word_arr.append(let_arr)

                word_pos_list = []
                getAllWords(word_arr, word_pos_list, [], 0)
                for word in word_pos_list:
                    score = scoreMove(state,word, player)
                    if (score>bestActionScore):
                        bestAction = word
                        bestActionScore = score
    return bestAction

def getAllWords(word_arr, word_list, temp, start):
    if len(word_arr) == len(temp):
        word_list.append(temp)
    else:
        for idx in range(start, len(word_arr)):
            for i in range(len(word_arr[idx])):
                temp2 = []
                for let in temp:
                    temp2.append(let)
                if (word_arr[idx][i] not in temp2):
                    temp2.append(word_arr[idx][i])
                    getAllWords(word_arr, word_list, temp2, idx+1)



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
        flood_tiles = state.board.floodfill([tile], lambda p, t: t == player or t == (player + "_CAPITAL") or p in tiles)
        is_connected = any(
            map(lambda k: state.board.get_tile(k) == player or state.board.get_tile(k) == (player + "_CAPITAL"), flood_tiles))

        if is_connected:
            connected_tiles.add(tile)

    # Now that we have a set of connected tiles:
    # - Connected tiles become player territory, and all tiles adjacent to them which were enemy territory become letter tiles.
    # - Disconnected tiles just become a new letter.
    result = state.board
    vulnurable = 0
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
                elif result.get_tile(adj) == enemy_capital and captured<10000-500:
                    captured+=10000
                    captured_capital = True
                elif result.get_tile(adj) == EMPTY:
                    pass
        else:
            # result = result.set_tile(tile, LETTER_PREFIX + lettergen())
            pass
    cap_guard = cap.adjacent_positions(state.board.find_single(player_capital))
    # print(enemyCap, state.board.find_single(player_capital))
    for adj in cap_guard:
        """
        if result.get_tile(adj) != player:
            print(result.get_tile(adj), player)
            vulnurable -= 100
        """
        if adj in tiles:
            vulnurable+=100

    captured += len(flipped)
    if enemyCap == None:
        return captured
    return captured+newTiles+vulnurable

class JohnAgent(object):
    def __init__(self):
        pass

    def act(self, state):
        return getMove(state, state.dictionary, state.turn)
