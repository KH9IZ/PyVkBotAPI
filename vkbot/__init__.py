# -*- coding: utf-8 -*-
import logging

import requests
from flask import json

from vk_types import Message

URL_BASE = "https://api.vk.com/method/{}"

log = logging.getLogger("main.vk_bot")


# log.setLevel(logging.DEBUG)
# fh = logging.FileHandler(r"/root/bots/vk/logs/out.log")
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# fh.setFormatter(formatter)
# log.addHandler(fh)


class Bot:
    def __init__(self, confirmation_key, access_token, group_id, secret_key=None):
        """ Constructor """
        self.__message_handlers = []
        self.__payload_handlers = []
        self.__next_step_handlers = []
        self.secret_key = secret_key
        self.confirmation_key = confirmation_key
        self.access_token = access_token
        self.api_version = 5.78
        self.group_id = group_id

    @staticmethod
    def __build_handler_dict(handler, **filters):
        return {
            'function': handler,
            'filters': filters,
        }

    def message_handler(self, regexp=None, func=None):
        def decorator(handler):
            handler_dict = self.__build_handler_dict(
                handler,
                regexp=regexp,
                func=func,
            )
            self.add_message_handler(handler_dict)
            return handler

        return decorator

    def add_message_handler(self, handler_dict):
        self.__message_handlers.append(handler_dict)

    def process_request(self, request):
        data = json.loads(request.data)
        if data['type'] == 'confirmation':
            return self.confirmation_key

        if data.get('secret') != self.secret_key:
            return "not-my-bot (*-_-)"

        if data['type'] == 'message_new':
            msg = Message(data['object'])
            # print(msg.user_id)
            if self.__check_next_step(msg):
                return 'ok'
            if msg.payload:
                # print(msg.payload)
                msg.payload = json.loads(msg.payload)
                self.process_payload(msg)
            self.process_message(msg)
        else:
            log.warning("unknown type {}".format(data['type']))
        return 'ok'

    def process_message(self, msg):
        for handler in self.__message_handlers:
            if self.test_message_handler(msg, handler):
                handler['function'](msg)
                msg.processed = True

    @staticmethod
    def test_message_handler(msg, handler):
        for filter_name, filter_value in handler['filters'].items():
            if filter_value is None:
                continue
            if (filter_name == 'regexp') and (filter_value != msg.text):
                return False
            if (filter_name == 'func') and (not bool(filter_value(msg))):
                return False
            return True

    def send_message(self, user_id, text, keyboard=None, photo=None):
        attachments = None
        if keyboard:
            keyboard = keyboard.to_json()
        if type(photo) is int:
            attachments = "photo-{}_{}".format(self.group_id, photo)
            log.debug(attachments)
        return self.make_request("messages.send",
                                 user_id=user_id,
                                 message=text,
                                 keyboard=keyboard,
                                 attachment=attachments,
                                 access_token=self.access_token,
                                 v=self.api_version)

    def get_user(self, user_id, fields):
        r = self.make_request("users.get", user_ids=user_id, fields=fields,
                              access_token=self.access_token, v=self.api_version)
        log.debug(str(r))
        return r['response'][0]

    @staticmethod
    def make_request(method_name, **data):
        data = dict((param, value) for param, value in data.items() if value is not None)
        url = URL_BASE.format(method_name)
        r = requests.post(url, data)
        log.debug(r.url)
        return r.json()

    def payload_handler(self, regexp=None, func=None):
        def decorator(handler):
            handler_dict = self.__build_handler_dict(
                handler,
                regexp=regexp,
                func=func,
            )
            self.add_payload_handler(handler_dict)
            return handler

        return decorator

    def add_payload_handler(self, handler_dict):
        self.__payload_handlers.append(handler_dict)

    def process_payload(self, msg):
        for handler in self.__payload_handlers:
            if self.test_payload_handler(msg, handler):
                handler['function'](msg)
                msg.processed = True

    @staticmethod
    def test_payload_handler(msg, handler):
        for filter_name, filter_value in handler['filters'].items():
            log.debug(handler['filters'].items())
            if filter_value is None:
                continue
            if (filter_name == 'regexp') and (filter_value != msg.payload.get("command")):
                return False
            if (filter_name == 'func') and (not bool(filter_value(msg))):
                return False
            return True

    def register_next_step_handler(self, user_id, call):
        handler_dict = self.__build_handler_dict(call,
                                                 user_id=user_id)
        self.__next_step_handlers.append(handler_dict)

    def __check_next_step(self, msg):
        for handler in self.__next_step_handlers:
            if msg.user_id == handler['filters']['user_id']:
                handler['function'](msg)
                self.__next_step_handlers.remove(handler)
                return True
        return False
