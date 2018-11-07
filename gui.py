#!/usr/bin/python
# -*- coding: utf-8 -*-

from tkinter import *
from math import cos, sin, sqrt, radians
import csv
import _pickle as pickle
import codecs
import capitals

COLOR_EMPTY = "#f9f9f9"
COLOR_LETTER = "#e6e6e6"
COLOR_RED = "#cc0000"
COLOR_BLUE = "#0000cc"
COLOR_RED_CAPITAL = "#660000"
COLOR_BLUE_CAPITAL = "#000066"
COLOR_SHADE = "#a6a6a6"

RED_CAPITAL = "RED_CAPITAL"
BLUE_CAPITAL = "BLUE_CAPITAL"
RED = "RED"
BLUE = "BLUE"
EMPTY = "EMPTY"
LETTER_PREFIX="LETTER_"
# ------------------------------------------------------------------------------
class Field:
    types = {
        "grass": "#000000",
        "water": "#60ace6",
        "moutain": "#a1603a"
    }

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
    def __init__(self):
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
        self.index = 0
        self.title = self.can.create_text(250,40,text="")
        self.round = self.can.create_text(450, 40, text="0")
        self.gameData = []

        with open("game1.log", 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                unpickled = pickle.loads(codecs.decode(row[0].encode(), "base64"))
                self.gameData.append(unpickled)

        self.updateHex()

    def initGrid(self, cols, rows, size, debug):
        margin = 100

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

        height = sqrt(3) * size
        for r in range(0,rows):
            for c in range(0,cols):
                if (r>BOARD_CONSTRAINTS[c][1] or r<BOARD_CONSTRAINTS[c][0]):
                    pass
                else:
                    x_pos = r * size * 1.5 + margin
                    y_pos = -1 * r * height/2 + c * height + margin
                    h = FillHexagon(self.can,
                                    x_pos,
                                    y_pos,
                                    size,
                                    COLOR_EMPTY,
                                    "{}.{}".format(r, c))
                    self.hexagons.append(h)
                    if r not in self.hexDict:
                        self.hexDict[r] = {}
                    self.hexDict[r][c]=h
                    if debug:
                        coords = "{}, {}".format(r, c)
                        text_id = self.can.create_text(x_pos + size/2, y_pos + 4*size/5,
                                             text="")

                        if r not in self.textDict:
                            self.textDict[r] = {}
                        self.textDict[r][c] = text_id

    def click(self, evt):
        self.can.itemconfigure(self.hexDict[0][0].tags, fill=COLOR_EMPTY)

    def leftKey(self, event):
        self.index = max(self.index-1,0)
        self.updateHex()

    def rightKey(self, event):
        self.index = min(self.index+1, 2*len(self.gameData)-1)
        self.updateHex()

    def updateHex(self):
        idx = int(self.index/2)
        action = True if self.index%2==1 else False
        state = self.gameData[idx]
        board = state[0].board
        self.can.itemconfigure(self.title, text="")
        self.can.itemconfigure(self.round, text=str(self.index))
        for pos, tile_type in board.items():
            x = pos[0]
            y = pos[1]
            self.can.itemconfigure(self.textDict[x][y], text="")
            if tile_type == RED_CAPITAL:
                self.can.itemconfigure(self.hexDict[x][y].tags, fill=COLOR_RED_CAPITAL)
                pass
            elif tile_type == BLUE_CAPITAL:
                self.can.itemconfigure(self.hexDict[x][y].tags, fill=COLOR_BLUE_CAPITAL)
                pass
            elif tile_type == RED:
                self.can.itemconfigure(self.hexDict[x][y].tags, fill=COLOR_RED)
                pass
            elif tile_type == BLUE:
                self.can.itemconfigure(self.hexDict[x][y].tags, fill=COLOR_BLUE)
                pass
            elif tile_type == EMPTY:
                self.can.itemconfigure(self.hexDict[x][y].tags, fill=COLOR_EMPTY)
                pass
            else:
                self.can.itemconfigure(self.hexDict[x][y].tags, fill=COLOR_LETTER)
                self.can.itemconfigure(self.textDict[x][y], text=str(tile_type)[7:])
                pass

        if action:
            self.can.itemconfigure(self.title, text=state[2])
            for pos in state[1]:
                self.can.itemconfigure(self.hexDict[pos[0]][pos[1]].tags, fill=COLOR_SHADE)




# ----------------------------------------------------------
if __name__ == '__main__':
    app = App()
    app.mainloop()

"""
RED_CAPITAL = "RED_CAPITAL"
BLUE_CAPITAL = "BLUE_CAPITAL"
RED = "RED"
BLUE = "BLUE"
EMPTY = "EMPTY"
LETTER_PREFIX="LETTER_"
"""