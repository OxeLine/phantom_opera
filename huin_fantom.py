import json
import logging
import os
import random
import socket
from logging.handlers import RotatingFileHandler

import protocol

host = "localhost"
port = 12000
# HEADERSIZE = 10

"""
set up fantom logging
"""
fantom_logger = logging.getLogger()
fantom_logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s :: %(levelname)s :: %(message)s", "%H:%M:%S")
# file
if os.path.exists("./logs/fantom.log"):
    os.remove("./logs/fantom.log")
file_handler = RotatingFileHandler('./logs/fantom.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
fantom_logger.addHandler(file_handler)
# stream
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.WARNING)
fantom_logger.addHandler(stream_handler)


class Player():

    def __init__(self):

        self.end = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.character = None

    def connect(self):
        self.socket.connect((host, port))

    def reset(self):
        self.socket.close()

    def get_fantom_character(self, characters, fantom_color):
        for c in characters:
            if c["color"] == fantom_color:
                return c
        return None

    def is_alone(self, characters, fantom):
        for c in characters:
            if c["position"] == fantom["position"]:
                return False
        return True

    def chose_character(self, fantom, data, game_state):
        characters = game_state["characters"]

        res = -1

        for idx, c in enumerate(data):
            if c["color"] == "red":
                return idx
            if self.is_alone(characters, self.get_fantom_character(characters, fantom)):
                if c["color"] != fantom and not self.is_alone(characters, c):
                    res = idx
            else:
                if c["color"] != fantom and self.is_alone(characters, c):
                    res = idx

        return res

    def is_empty(self, characters, p):
        for c in characters:
            if c["position"] == p:
                return False
        return True

    def chose_position(self, fantom, data, game_state):
        characters = game_state["characters"]

        res = -1

        for idx, p in enumerate(data):
            if self.is_alone(characters, self.get_fantom_character(characters, fantom)):
                if self.is_empty(characters, p):
                    res = idx
            else:
                if not self.is_empty(characters, p):
                    res = idx
        return res

    def get_number_of_characters(self, characters, position):
        nb = 0
        for c in characters:
            if c["position"] == position:
                nb += 1
        return nb

    def answer(self, question):
        # work
        data = question["data"]
        game_state = question["game state"]
        question_type = question["question type"]
        fantom = game_state["fantom"]

        response_index = -1
        if question_type == "select character":
            response_index = self.chose_character(fantom, data, game_state)
        elif question_type == "select position":
            response_index = self.chose_position(fantom, data, game_state)

        if response_index == -1:
            response_index = random.randint(0, len(data)-1)

        if question_type == "select character":
            self.character = data[response_index]

        # log
        fantom_logger.debug("|\n|")
        fantom_logger.debug("fantom answers")
        fantom_logger.debug(f"question type ----- {question['question type']}")
        fantom_logger.debug(f"data -------------- {data}")
        fantom_logger.debug(f"response index ---- {response_index}")
        fantom_logger.debug(f"response ---------- {data[response_index]}")
        return response_index

    def handle_json(self, data):
        data = json.loads(data)
        response = self.answer(data)
        # send back to server
        bytes_data = json.dumps(response).encode("utf-8")
        protocol.send_json(self.socket, bytes_data)

    def run(self):

        self.connect()

        while self.end is not True:
            received_message = protocol.receive_json(self.socket)
            if received_message:
                self.handle_json(received_message)
            else:
                print("no message, finished learning")
                self.end = True


p = Player()

p.run()
