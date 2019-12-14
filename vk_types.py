# -*- coding: utf-8 -*-

from json import dumps


class Message:
    def __init__(self, obj):
        self.message_id = obj.get('id')
        self.user_id = obj['from_id']
        self.from_user_id = obj.get('from_user')
        self.date = obj['date']
        self.read_state = bool(obj.get('read_state'))
        self.out = bool(obj.get('out'))
        self.title = obj.get('title')
        self.text = obj.get('text')
        self.important = bool(obj.get('important'))
        self.payload = obj.get('payload')
        self.processed = False


class Keyboard:
    def __init__(self, row_width=3, one_time=False):
        self.one_time = one_time
        self.row_width = row_width
        self.buttons = []

    def row(self, *buttons):
        row = []
        for button in buttons:
            row.append(button.__dict__)
        self.buttons.append(row)

    def add(self, *args):
        i = 1
        row = []
        for button in args:
            # print(button.__dict__)
            row.append(button.__dict__)
            if i % self.row_width == 0:
                self.buttons.append(row)
                row = []
            i += 1
        if len(row) > 0:
            self.buttons.append(row)

    def to_json(self):
        json_dict = {
            "one_time": self.one_time,
            'buttons': self.buttons,
        }
        return dumps(json_dict, ensure_ascii=False)


class Color:
    Blue = "primary"
    White = "default"
    Red = "negative"
    Green = "positive"


class Button:

    def __init__(self, text, payload=None, color=Color.White):
        self.action = {
            'type': 'text',
            'payload': payload,
            'label': text
        }
        self.color = color
        if type(payload) is str:
            payload = {'command': payload}
            self.action.update({'payload': dumps(payload, ensure_ascii=False)})
        if type(payload) is dict:
            self.action.update({'payload': dumps(payload, ensure_ascii=False)})
