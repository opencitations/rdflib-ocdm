#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2016, Silvio Peroni <essepuntato@gmail.com>
#
# Permission to use, copy, modify, and/or distribute this software for any purpose
# with or without fee is hereby granted, provided that the above copyright notice
# and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT,
# OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE,
# DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
# SOFTWARE.
from __future__ import annotations

import json
import os

from rdflib_ocdm.counter_handler.counter_handler import CounterHandler
from rdflib_ocdm.support import is_string_empty


class FilesystemCounterHandler(CounterHandler):
    """A concrete implementation of the ``CounterHandler`` interface that persistently stores
    the counter values within the filesystem."""

    def __init__(self, info_dir: str) -> None:
        """
        Constructor of the ``FilesystemCounterHandler`` class.

        :param info_dir: The path to the folder that does/will contain the counter values.
        :type info_dir: str
        :raises ValueError: if ``info_dir`` is None or an empty string.
        """
        if info_dir is None or is_string_empty(info_dir):
            raise ValueError("info_dir parameter is required!")

        if info_dir[-1] != os.sep:
            info_dir += os.sep

        self.info_dir: str = info_dir
        self.prov_files = dict()
        self.provenance_index_filename = 'provenance_index.json'

    def set_counter(self, new_value: int, entity_name: str) -> None:
        """
        It allows to set the counter value of provenance entities.

        :param new_value: The new counter value to be set
        :type new_value: int
        :param entity_name: The entity name
        :type entity_name: str
        :raises ValueError: if ``new_value`` is a negative integer.
        :return: None
        """
        entity_name = str(entity_name)
        if new_value < 0:
            raise ValueError("new_value must be a non negative integer!")
        file_path: str = self._get_prov_path()
        self.__initialize_file_if_not_existing(file_path, entity_name)
        with open(file_path, 'r', encoding='utf8') as file:
            data = json.load(file)
        with open(file_path, 'w', encoding='utf8') as outfile:
            data[entity_name] = new_value
            json.dump(obj=data, fp=outfile, ensure_ascii=False, indent=False)

    def read_counter(self, entity_name: str) -> int:
        """
        It allows to read the counter value of provenance entities.

        :param entity_name: The entity name
        :type entity_name: str
        :return: The requested counter value.
        """
        entity_name = str(entity_name)
        file_path: str = self._get_prov_path()
        return self._read_number(file_path, entity_name)

    def increment_counter(self, entity_name: str) -> int:
        """
        It allows to increment the counter value of provenance entities by one unit.

        :param entity_name: The entity name
        :type entity_name: str
        :return: The newly-updated (already incremented) counter value.
        """
        entity_name = str(entity_name)
        file_path: str = self._get_prov_path()
        return self._add_number(file_path, entity_name)

    def _get_prov_path(self) -> str:
        return os.path.join(self.info_dir, self.provenance_index_filename)

    def __initialize_file_if_not_existing(self, file_path: str, entity_name: str):
        entity_name = str(entity_name)
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        if not os.path.isfile(file_path):
            with open(file_path, 'w', encoding='utf8') as outfile:
                json.dump({entity_name: 0}, ensure_ascii=False, indent=None, fp=outfile)

    def _read_number(self, file_path: str, entity_name: str) -> int:
        self.__initialize_file_if_not_existing(file_path, entity_name)
        with open(file_path, 'r', encoding='utf8') as file:
            data = json.load(file)
            if entity_name in data:
                self.prov_files[entity_name] = data[entity_name]
            else:
                self.prov_files[entity_name] = 0
        return self.prov_files[entity_name]

    def _add_number(self, file_path: str, entity_name: str) -> int:
        self.__initialize_file_if_not_existing(file_path, entity_name)
        cur_number = self._read_number(file_path, entity_name)
        cur_number += 1
        with open(file_path, 'r', encoding='utf8') as file:
            data = json.load(file)
        with open(file_path, 'w', encoding='utf8') as outfile:
            data[entity_name] = cur_number
            json_object = json.dumps(data, ensure_ascii=False, indent=None)
            outfile.write(json_object)
        return cur_number