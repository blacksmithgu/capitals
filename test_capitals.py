import capitals

from capitals import Dictionary, Board, State, LetterGenerator

# Dictionary Tests
def test_dictionary_from_list_len():
    new_dict = Dictionary.from_list(["a", "b", "c"])
    assert len(new_dict) == 3

def test_dictionary_from_list_contains():
    new_dict = Dictionary.from_list(["a", "b", "c"])
    assert new_dict.contains("A")
    assert new_dict.contains("a")

def test_dictionary_from_list_no_contains():
    new_dict = Dictionary.from_list(["a", "b", "c"])
    assert not new_dict.contains("x")
    assert not new_dict.contains("~")


# Position tests
def test_valid_position():
    assert capitals.valid_position((0, 0))
    assert capitals.valid_position((1, 0))
    assert capitals.valid_position(capitals.RED_START_POS)
    assert capitals.valid_position(capitals.BLUE_START_POS)

def test_invalid_position():
    assert not capitals.valid_position((-1, 0))
    assert not capitals.valid_position((0, -1))
    assert not capitals.valid_position((0, 8))
    assert not capitals.valid_position((0, 7))

def test_all_valid_positions():
    for position in capitals.valid_positions():
        assert capitals.valid_position(position)

def test_adjacent_positions():
    assert set(capitals.adjacent_positions((0, 0))) == set([(1, 0), (0, 1), (1, 1)])
    assert set(capitals.adjacent_positions((2, 2))) == set([(1, 2), (3, 2), (2, 1), (2, 3), (1, 1), (3, 3)])

# Board tests
def test_empty_board_get_tile():
    board = Board()

    assert board.get_tile((0, 0)) == capitals.EMPTY
    assert board.get_tile((1, 0)) == capitals.EMPTY

    try:
        board.get_tile((-1, 0))
        assert False
    except:
        # Should throw a ValueException
        pass

def test_board_set_tile():
    board = Board()
    board = board.set_tile((0, 0), capitals.RED)
    board = board.set_tile((1, 0), capitals.BLUE)

    assert board.get_tile((0, 0)) == capitals.RED
    assert board.get_tile((1, 0)) == capitals.BLUE

def test_board_find_single_None():
    board = Board()

    assert board.find_single(capitals.RED_CAPITAL) is None
    assert board.find_single(capitals.RED) is None

def test_board_find_single():
    board = Board({ (0, 0): capitals.RED, (3, 4): capitals.RED_CAPITAL })

    assert board.find_single(capitals.RED) == (0, 0)
    assert board.find_single(capitals.RED_CAPITAL) == (3, 4)

def test_board_find_all():
    board = Board({ (0, 0): capitals.RED, (1, 0): capitals.RED, (3, 4): capitals.RED, (3, 5): capitals.RED_CAPITAL })

    assert set(board.find_all(capitals.RED)) == set([(0, 0), (1, 0), (3, 4)])
    assert set(board.find_all(capitals.RED_CAPITAL)) == set([(3, 5)])

def test_board_find_all_letters():
    board = Board({ (0, 0): capitals.RED, (1, 0): "LETTER_X", (1, 1): "LETTER_Q", (3, 4): "LETTER_Z" })

    assert board.find_all_letters() == { (1, 0): "X", (1, 1): "Q", (3, 4): "Z" }

def test_board_floodfill():
    board = Board({ (0, 0): capitals.RED, (1, 0): capitals.RED_CAPITAL, (1, 1): capitals.RED, (0, 2): capitals.BLUE,
                    (1, 2): capitals.BLUE, (2, 2): capitals.RED, (3, 2): capitals.RED, (5, 7): capitals.RED })

    assert board.floodfill((0, 0), lambda p, t: t == capitals.RED or t == capitals.RED_CAPITAL) \
        == set([(0, 0), (1, 0), (1, 1), (2, 2), (3, 2)])
    assert board.floodfill((5, 7), lambda p, t: t == capitals.RED or t == capitals.RED_CAPITAL) \
        == set([(5, 7)])

def test_board_get_letter():
    board = Board({ (0, 0): capitals.RED, (1, 0): "LETTER_X", (1, 1): "LETTER_Z" })

    assert board.get_letter((0, 0)) is None
    assert board.get_letter((1, 0)) == "X"
    assert board.get_letter((1, 1)) == "Z"

def test_board_use_tiles():
    board = Board({ (0, 0): capitals.RED, (1, 0): capitals.RED_CAPITAL, (0, 1): "LETTER_X", (1, 1): "LETTER_Q", (0, 2):
        capitals.BLUE_CAPITAL, (4, 3): capitals.RED })

    new_board, capital_cap = board.use_tiles([(0, 1), (1, 1)], capitals.BLUE, LetterGenerator())
    assert new_board.get_tile((0, 0)).startswith(capitals.LETTER_PREFIX)
    assert new_board.get_tile((1, 0)).startswith(capitals.LETTER_PREFIX)
    assert new_board.get_tile((0, 1)) == capitals.BLUE
    assert new_board.get_tile((1, 1)) == capitals.BLUE
    assert capital_cap

    assert set(new_board.find_all_matching(lambda p, t: t == capitals.RED or t == capitals.RED_CAPITAL)) == set([(4, 3)])

def test_board_use_tiles2():
    board = Board({ (3, 3): capitals.BLUE, (2, 2): capitals.RED_CAPITAL, (2, 3): capitals.RED, (3, 2): "LETTER_A" })

    new_board, capital_cap = board.use_tiles([(3, 2)], capitals.RED, LetterGenerator())
    assert new_board.get_tile((3, 2)) == capitals.RED
    assert new_board.get_tile((2, 2)) == capitals.RED_CAPITAL
    assert new_board.get_letter((3, 3)) is not None
    assert not capital_cap

def test_board_use_tiles3():
    # Test that we replace EMPTY tiles with letter tiles around newly taken territory.
    board = Board({ (3, 3): capitals.BLUE, (4, 4): "LETTER_X" })

    new_board, capital_cap = board.use_tiles([(4, 4)], capitals.BLUE, LetterGenerator())
    assert new_board.get_tile((4, 4)) == capitals.BLUE
    for pos in capitals.adjacent_positions((4, 4)):
        if pos == (3, 3):
            continue

        assert new_board.get_letter(pos) is not None

# Game State tests
def test_state_next_turn():
    dictionary = Dictionary.from_list(["a", "ab", "abc", "abcd"])
    state = State.initial(dictionary)

    assert state.turn == capitals.RED
    assert state.round == 1

    state = state.next_turn(state.board, False)
    assert state.turn == capitals.BLUE
    assert state.round == 1

    state = state.next_turn(state.board, False)
    assert state.turn == capitals.RED
    assert state.round == 2

def test_state_next_turn_capital_captured():
    dictionary = Dictionary.from_list(["a", "ab", "abc", "abcd"])
    state = State.initial(dictionary)

    assert state.turn == capitals.RED
    assert state.round == 1

    state = state.next_turn(state.board, True)
    assert state.turn == capitals.RED
    assert state.round == 2

    state = state.next_turn(state.board, True)
    assert state.turn == capitals.RED
    assert state.round == 3

def test_state_winner():
    dictionary = Dictionary.from_list(["a", "ab", "abc", "abcd"])
    board = Board({ (2, 2): capitals.RED_CAPITAL, (2, 3): capitals.BLUE_CAPITAL, (3, 3): "LETTER_A", (5, 5): "LETTER_A" })
    state = State(dictionary, board)

    # Red goes first, have them win.
    state_red_win = state.act([(3, 3)])
    assert state_red_win.winner() == capitals.RED

    # Now, have red do nothing useful and then have blue win.
    state_blue_win = state.act([(5, 5)]).act([(3, 3)])
    assert state_blue_win.winner() == capitals.BLUE

def test_state_capture_capital():
    dictionary = Dictionary.from_list(["a", "ab", "abc", "abcd"])
    board = Board({ (2, 2): capitals.RED_CAPITAL, (1, 1): capitals.RED, (3, 3): "LETTER_A", (4, 4):
        capitals.BLUE_CAPITAL, (5, 5): capitals.BLUE, (3, 5): "LETTER_A" })
    state = State(dictionary, board)

    # Have red capture the capital - we should get another turn.
    state_red = state.act([(3, 3)])
    assert state_red.turn == capitals.RED
    assert state_red.board.get_tile((4, 4)).startswith(capitals.LETTER_PREFIX)
    assert state_red.board.blue_capital() is None

    # Have red waste the turn; we should see a blue capital show up again.
    state_red2 = state_red.act([(3, 5)])
    assert state_red2.board.blue_capital() == (5, 5)
