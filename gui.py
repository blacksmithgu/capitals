#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter import *
from math import cos, sin, sqrt, radians

import capitals
import argparse

COLOR_EMPTY = "#f9f9f9"
COLOR_LETTER = "#e6e6e6"
COLOR_RED = "#cc0000"
COLOR_BLUE = "#0066cc"
COLOR_RED_CAPITAL = "#660000"
COLOR_BLUE_CAPITAL = "#000066"
COLOR_SHADE = "#a6a6a6"
# ------------------------------------------------------------------------------
class Field:
    def __init__(self, parent, x, y, kind, size):
        self.parent = parent
        self.x = x
        self.y = y
        self.kind = kind
        self.color = Field.types[self.kind]
        self.selected = False

    def draw(self):
        FillHexagon(self.parent, self.x, self.y, self.size, self.color)

    def enlight(self):
        pass


# ------------------------------------------------------------------------------
class StrokeHexagon:
    def __init__(self, parent, x, y, length, color):
        self.parent = parent  # canvas
        self.x = x  # top left x
        self.y = y  # top left y
        self.length = length  # length of a side
        self.color = color  # outline color

        self.draw()

    def draw(self):
        start_x = self.x
        start_y = self.y
        angle = 60

        for i in range(6):
            end_x = start_x + self.length * cos(radians(angle * i))
            end_y = start_y + self.length * sin(radians(angle * i))
            self.parent.create_line(start_x,
                                    start_y,
                                    end_x,
                                    end_y,
                                    fill=self.color)
            start_x = end_x
            start_y = end_y


# ------------------------------------------------------------------------------
class FillHexagon:
    def __init__(self, parent, x, y, length, color, tags):
        self.parent = parent  # canvas
        self.x = x  # top left x
        self.y = y  # top left y
        self.length = length  # length of a side
        self.color = color  # fill color

        self.selected = False
        self.tags = tags

        self.draw()

    def draw(self):
        start_x = self.x
        start_y = self.y
        angle = 60
        coords = []
        for i in range(6):
            end_x = start_x + self.length * cos(radians(angle * i))
            end_y = start_y + self.length * sin(radians(angle * i))
            coords.append([start_x, start_y])
            start_x = end_x
            start_y = end_y
        self.parent.create_polygon(coords[0][0],
                                   coords[0][1],
                                   coords[1][0],
                                   coords[1][1],
                                   coords[2][0],
                                   coords[2][1],
                                   coords[3][0],
                                   coords[3][1],
                                   coords[4][0],
                                   coords[4][1],
                                   coords[5][0],
                                   coords[5][1],
                                   fill=self.color,
                                   outline="gray",
                                   tags=self.tags)


# ---------------------------------------------------------
class App(Tk):
    def __init__(self, logs):
        Tk.__init__(self)
        self.title("Hexagon Grid")
        self.can = Canvas(self, width=550, height=500, bg="#ffffff")
        self.can.pack()

        self.hexagons = []
        self.hexDict = {}
        self.textDict = {}
        self.initGrid(9, 9, 30, debug=True)

        self.can.focus_set()
        self.can.bind("<Button-1>", self.click)
        self.can.bind("<Right>", self.rightKey)
        self.can.bind("<Left>", self.leftKey)
        self.log_index = 0
        self.action_index = 0
        self.title = self.can.create_text(250,40,text="")
        self.game_id = self.can.create_text(450, 20, text="Game 0")
        self.round = self.can.create_text(450, 40, text="0")
        self.red_name = self.can.create_text(150, 460, text="unknown", fill=COLOR_RED)
        self.blue_name = self.can.create_text(350, 460, text="unknown", fill=COLOR_BLUE)
        self.logs = logs

        self.updateHex()

    def initGrid(self, cols, rows, size, debug):
        margin = 100

        height = sqrt(3) * size
        for r in range(0,rows):
            for c in range(0,cols):
                if not capitals.valid_position((r, c)):
                    pass
                else:
                    x_pos = r * size * 1.5 + margin
                    y_pos = -1 * r * height/2 + c * height + margin
                    h = FillHexagon(self.can, x_pos, y_pos, size, COLOR_EMPTY, "{}.{}".format(r, c))
                    self.hexagons.append(h)
                    if r not in self.hexDict:
                        self.hexDict[r] = {}
                    self.hexDict[r][c]=h
                    if debug:
                        coords = "{}, {}".format(r, c)
                        text_id = self.can.create_text(x_pos + size/2, y_pos + 4*size/5, text="")

                        if r not in self.textDict:
                            self.textDict[r] = {}
                        self.textDict[r][c] = text_id

    def click(self, evt):
        pass

    def leftKey(self, event):
        self.action_index = self.action_index - 1
        if self.action_index < 0:
            if self.log_index == 0:
                self.action_index = 0
            else:
                self.log_index = self.log_index - 1
                self.action_index = len(self.logs[self.log_index]) - 1

        self.updateHex()

    def rightKey(self, event):
        self.action_index = self.action_index + 1
        if self.action_index >= len(self.logs[self.log_index]):
            if self.log_index == len(self.logs) - 1:
                self.action_index = len(self.logs[self.log_index]) - 1
            else:
                self.log_index = self.log_index + 1
                self.action_index = 0

        self.updateHex()

    def updateHex(self):
        state = self.logs[self.log_index].states[self.action_index]
        action = self.logs[self.log_index].actions[self.action_index]
        board = state.board
        self.can.itemconfigure(self.title, text="")
        self.can.itemconfigure(self.round, text=(str(state.round) + " - " + state.turn))
        self.can.itemconfigure(self.game_id, text="Game " + str(self.log_index))
        self.can.itemconfigure(self.red_name, text=self.logs[self.log_index].red_name)
        self.can.itemconfigure(self.blue_name, text=self.logs[self.log_index].blue_name)

        for pos in capitals.valid_positions():
            tile_type = board.get_tile(pos)
            x = pos[0]
            y = pos[1]
            self.can.itemconfigure(self.textDict[x][y], text="")
            if tile_type == capitals.RED_CAPITAL:
                self.can.itemconfigure(self.hexDict[x][y].tags, fill=COLOR_RED_CAPITAL)
                pass
            elif tile_type == capitals.BLUE_CAPITAL:
                self.can.itemconfigure(self.hexDict[x][y].tags, fill=COLOR_BLUE_CAPITAL)
                pass
            elif tile_type == capitals.RED:
                self.can.itemconfigure(self.hexDict[x][y].tags, fill=COLOR_RED)
                pass
            elif tile_type == capitals.BLUE:
                self.can.itemconfigure(self.hexDict[x][y].tags, fill=COLOR_BLUE)
                pass
            elif tile_type == capitals.EMPTY:
                self.can.itemconfigure(self.hexDict[x][y].tags, fill=COLOR_EMPTY)
                pass
            else:
                self.can.itemconfigure(self.hexDict[x][y].tags, fill=COLOR_LETTER)
                self.can.itemconfigure(self.textDict[x][y], text=str(tile_type)[7:])
                pass

        if action:
            self.can.itemconfigure(self.title, text=board.get_word(action))
            for pos in action:
                self.can.itemconfigure(self.hexDict[pos[0]][pos[1]].tags, fill=COLOR_SHADE)




# ----------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="capitals.py visualizer")
    parser.add_argument("logs", type=str, nargs="+", help="Logs to load & display")
    args = parser.parse_args()

    logs = []
    dictionary = capitals.Dictionary.from_file("dict.txt")
    lettergen = capitals.LetterGenerator()

    for logfile in args.logs:
        logs.append(capitals.GameLog.from_file(logfile, dictionary, lettergen))
        print("Loaded logfile '%s' (game had %d actions)" % (logfile, len(logs[-1])))

    app = App(logs)
    app.mainloop()
