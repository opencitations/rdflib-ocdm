#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2023 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# Permission to use, copy, modify, and/or distribute this software for any purpose
# with or without fee is hereby granted, provided that the above copyright notice
# and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED 'AS IS' AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT,
# OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE,
# DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
# SOFTWARE.

from __future__ import annotations

import os
from datetime import datetime
from typing import TYPE_CHECKING

from oc_ocdm.support.reporter import Reporter
from SPARQLWrapper import SPARQLWrapper

from rdflib_ocdm.ocdm_graph import OCDMGraph, OCDMGraphCommons
from rdflib_ocdm.query_utils import get_update_query

if TYPE_CHECKING:
    from rdflib import Graph


class Storer(object):

    def __init__(self, abstract_set: OCDMGraphCommons|Graph, repok: Reporter = None, reperr: Reporter = None) -> None:
        self.a_set = abstract_set
        if repok is None:
            self.repok: Reporter = Reporter(prefix="[Storer: INFO] ")
        else:
            self.repok: Reporter = repok

        if reperr is None:
            self.reperr: Reporter = Reporter(prefix="[Storer: ERROR] ")
        else:
            self.reperr: Reporter = reperr

    def _query(self, query_string: str, triplestore_url: str, base_dir: str = None,
               added_statements: int = 0, removed_statements: int = 0) -> bool:
        if query_string != "":
            try:
                sparql: SPARQLWrapper = SPARQLWrapper(triplestore_url)
                sparql.setQuery(query_string)
                sparql.setMethod('POST')

                sparql.query()

                self.repok.add_sentence(
                    f"Triplestore updated with {added_statements} added statements and "
                    f"with {removed_statements} removed statements.")

                return True
            except Exception as e:
                self.reperr.add_sentence("[3] "
                                         "Graph was not loaded into the "
                                         f"triplestore due to communication problems: {e}")
                if base_dir is not None:
                    tp_err_dir: str = base_dir + os.sep + "tp_err"
                    if not os.path.exists(tp_err_dir):
                        os.makedirs(tp_err_dir)
                    cur_file_err: str = tp_err_dir + os.sep + \
                        datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f_not_uploaded.txt')
                    with open(cur_file_err, 'wt', encoding='utf-8') as f:
                        f.write(query_string)
        return False
    
    def upload_all(self, triplestore_url: str, base_dir: str = None, batch_size: int = 10) -> bool:
        self.repok.new_article()
        self.reperr.new_article()
        if batch_size <= 0:
            batch_size = 10
        query_string: str = ""
        added_statements: int = 0
        removed_statements: int = 0
        skipped_queries: int = 0
        result: bool = True
        for idx, entity in enumerate(self.a_set.subjects(unique=True)):
            entity_type = 'graph' if isinstance(self.a_set, OCDMGraph) else 'prov'
            update_query, n_added, n_removed = get_update_query(self.a_set, entity, entity_type)
            if update_query == "":
                skipped_queries += 1
            else:
                index = idx - skipped_queries
                if index == 0:
                    # First query
                    query_string = update_query
                    added_statements = n_added
                    removed_statements = n_removed
                elif index % batch_size == 0:
                    # batch_size-multiple query
                    result &= self._query(query_string, triplestore_url, base_dir, added_statements, removed_statements)
                    query_string = update_query
                    added_statements = n_added
                    removed_statements = n_removed
                else:
                    # Accumulated query
                    query_string += " ; " + update_query
                    added_statements += n_added
                    removed_statements += n_removed
        if query_string != "":
            result &= self._query(query_string, triplestore_url, base_dir, added_statements, removed_statements)
        return result