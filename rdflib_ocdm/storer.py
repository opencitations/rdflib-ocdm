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
import random
import time
from datetime import datetime
from typing import TYPE_CHECKING

from oc_ocdm.support.reporter import Reporter
from rdflib_ocdm.ocdm_graph import (OCDMConjunctiveGraph, OCDMGraph,
                                    OCDMGraphCommons)
from rdflib_ocdm.query_utils import get_update_query
from rdflib_ocdm.retry_utils import execute_with_retry
from SPARQLWrapper import SPARQLWrapper

if TYPE_CHECKING:
    from typing import Set

    from rdflib import Graph


class Storer(object):

    def __init__(self, abstract_set: OCDMGraphCommons|Graph, repok: Reporter = None, reperr: Reporter = None, output_format: str = "json-ld", zip_output: bool = False,) -> None:
        self.a_set = abstract_set
        supported_formats: Set[str] = {'application/n-triples', 'ntriples', 'nt', 'nt11',
                                       'application/n-quads', 'nquads', 'json-ld'}
        if output_format not in supported_formats:
            raise ValueError(f"Given output_format '{self.output_format}' is not supported."
                             f" Available formats: {supported_formats}.")
        else:
            self.output_format: str = output_format
        self.zip_output = zip_output
        if repok is None:
            self.repok: Reporter = Reporter(prefix="[Storer: INFO] ")
        else:
            self.repok: Reporter = repok

        if reperr is None:
            self.reperr: Reporter = Reporter(prefix="[Storer: ERROR] ")
        else:
            self.reperr: Reporter = reperr

    def _query(self, query_string: str, triplestore_url: str, base_dir: str = None,
               added_statements: int = 0, removed_statements: int = 0, max_retries: int = 5) -> bool:
        if query_string != "":
            try:
                # Use the retry utility function with custom error handling
                def execute_query():
                    sparql: SPARQLWrapper = SPARQLWrapper(triplestore_url)
                    sparql.setQuery(query_string)
                    sparql.setMethod('POST')
                    sparql.query()
                    return True
                
                execute_with_retry(
                    execute_query,
                    max_retries=max_retries,
                    reporter=self.repok
                )
                
                self.repok.add_sentence(
                    f"Triplestore updated with {added_statements} added statements and "
                    f"with {removed_statements} removed statements.")
                
                return True
            except ValueError as e:
                # Handle the case when all retries failed
                self.reperr.add_sentence(f"[3] Graph was not loaded into the triplestore due to communication problems: {e}")
                if base_dir is not None:
                    tp_err_dir: str = base_dir + os.sep + "tp_err"
                    if not os.path.exists(tp_err_dir):
                        os.makedirs(tp_err_dir)
                    cur_file_err: str = tp_err_dir + os.sep + \
                        datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f_not_uploaded.txt')
                    with open(cur_file_err, 'wt', encoding='utf-8') as f:
                        f.write(query_string)
                return False
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
        entity_type = 'graph' if isinstance(self.a_set, OCDMGraph) or isinstance(self.a_set, OCDMConjunctiveGraph) else 'prov'
        for idx, entity in enumerate(list(self.a_set.all_entities)):
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

    # def store_all(self, base_dir: str, base_iri: str, context_path: str = None) -> List[str]:
    #     self.repok.new_article()
    #     self.reperr.new_article()

    #     self.repok.add_sentence("Starting the process")

    #     for relevant_path, entities_in_path in relevant_paths.items():
    #         stored_g = None
    #         # Here we try to obtain a reference to the currently stored graph
    #         output_filepath = relevant_path.replace(os.path.splitext(relevant_path)[1], ".zip") if self.zip_output else relevant_path
    #         if os.path.exists(output_filepath):
    #             stored_g = Reader(repok=self.repok, reperr=self.reperr).load(output_filepath)
    #         if stored_g is None:
    #             stored_g = ConjunctiveGraph()
    #         for entity_in_path in entities_in_path:
    #             self.store(entity_in_path, stored_g, relevant_path, context_path, False)
    #         self._store_in_file(stored_g, relevant_path, context_path)

    #     return list(relevant_paths.keys())

    # def _store_in_file(self, cur_g: Graph|ConjunctiveGraph, cur_file_path: str, context_path: str = None) -> None:
    #     # Note: the following lines from here and until 'cur_json_ld' are a sort of hack for including all
    #     # the triples of the input graph into the final stored file. Somehow, some of them are not written
    #     # in such file otherwise - in particular the provenance ones.
    #     new_g: ConjunctiveGraph = ConjunctiveGraph()
    #     for s, p, o in cur_g.triples((None, None, None)):
    #         g_iri: Optional[URIRef] = None
    #         for g_context in cur_g.contexts((s, p, o)):
    #             g_iri = g_context.identifier
    #             break

    #         new_g.addN([(s, p, o, g_iri)])
    #     zip_file_path = cur_file_path.replace(os.path.splitext(cur_file_path)[1], ".zip")
    #     lock = FileLock(f"{zip_file_path}.lock") if self.zip_output else FileLock(f"{cur_file_path}.lock")
    #     with lock:
    #         if self.zip_output:
    #             zip_file = ZipFile(zip_file_path, mode="w", compression=ZIP_DEFLATED, allowZip64=True)
    #         if self.output_format == "json-ld":
    #             cur_json_ld: Any = json.loads(new_g.serialize(format="json-ld"))
    #             if self.zip_output:
    #                 dumped_json: bytes = json.dumps(cur_json_ld, ensure_ascii=False).encode('utf-8')
    #                 zip_file.writestr(zinfo_or_arcname=os.path.basename(cur_file_path), data=dumped_json)
    #             else:
    #                 with open(cur_file_path, 'wt', encoding='utf-8') as f:
    #                     json.dump(cur_json_ld, f, ensure_ascii=False)
    #         else:
    #             if self.zip_output:
    #                 rdf_serialization: bytes = new_g.serialize(destination=None, format=self.output_format, encoding="utf-8")
    #                 zip_file.writestr(zinfo_or_arcname=os.path.basename(cur_file_path), data=rdf_serialization)
    #             else:
    #                 new_g.serialize(destination=cur_file_path, format=self.output_format, encoding="utf-8")
    #         if self.zip_output:
    #             zip_file.close()
    #     self.repok.add_sentence(f"File '{cur_file_path}' added.")