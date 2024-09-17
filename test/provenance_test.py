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

import json
import os
import unittest

from rdflib import Literal, URIRef

from rdflib_ocdm.counter_handler.filesystem_counter_handler import \
    FilesystemCounterHandler
from rdflib_ocdm.counter_handler.sqlite_counter_handler import \
    SqliteCounterHandler
from rdflib_ocdm.ocdm_graph import OCDMConjunctiveGraph, OCDMGraph
from rdflib_ocdm.prov.provenance import OCDMProvenance
from rdflib_ocdm.prov.snapshot_entity import SnapshotEntity


class TestOCDMProvenance(unittest.TestCase):
    def setUp(self):
        self.subject = 'https://w3id.org/oc/meta/br/0605'

    def test_add_se(self):
        ocdm_graph = OCDMGraph()
        ocdm_prov_memory = OCDMProvenance(ocdm_graph)
        ocdm_graph.add((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('Bella zì')))
        se = ocdm_prov_memory.add_se(prov_subject=URIRef(self.subject))
        self.assertIsNotNone(se)
        self.assertIsInstance(se, SnapshotEntity)
        self.assertEqual(str(se.res), 'https://w3id.org/oc/meta/br/0605/prov/se/1')

    def test_generate_provenance(self):
        cur_time = 1607375859.846196
        cur_time_str = '2020-12-07T21:17:34+00:00'
        with self.subTest('Creation -> No snapshot -> Modification. OCDMGraph. in-memory counter'):
            ocdm_graph = OCDMGraph()
            ocdm_graph.parse(os.path.join('test', 'br.nt'))
            ocdm_graph.preexisting_finished(resp_agent='https://orcid.org/0000-0002-8420-0696', source='https://api.crossref.org/', c_time=cur_time)
            result = ocdm_graph.generate_provenance(c_time=cur_time)
            self.assertIsNone(result)
            se_a: SnapshotEntity = ocdm_graph.get_entity(f'{self.subject}/prov/se/1')
            self.assertIsNotNone(se_a)
            self.assertIsInstance(se_a, SnapshotEntity)
            self.assertEqual(URIRef(self.subject), se_a.get_is_snapshot_of())
            self.assertEqual(cur_time_str, se_a.get_generation_time())
            self.assertEqual(f"The entity '{self.subject}' has been created.", se_a.get_description())
            self.assertEqual(se_a.get_primary_source(), URIRef('https://api.crossref.org/'))
            self.assertEqual(se_a.get_resp_agent(), URIRef('https://orcid.org/0000-0002-8420-0696'))
            ocdm_graph.generate_provenance(c_time=cur_time)
            se_a_2: SnapshotEntity = ocdm_graph.get_entity(f'{self.subject}/prov/se/2')
            self.assertIsNone(se_a_2)
            ocdm_graph.remove((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy')))
            ocdm_graph.add((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('Bella zì')))
            ocdm_graph.generate_provenance()
            se_a_2: SnapshotEntity = ocdm_graph.get_entity(f'{self.subject}/prov/se/2')
            self.assertEqual(se_a_2.get_update_action(), 'DELETE DATA { <https://w3id.org/oc/meta/br/0605> <http://purl.org/dc/terms/title> "A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy" . }; INSERT DATA { <https://w3id.org/oc/meta/br/0605> <http://purl.org/dc/terms/title> "Bella zì" . }')
            self.assertEqual(se_a_2.get_description(), f"The entity '{self.subject}' was modified.")
            self.assertEqual(ocdm_graph.provenance.counter_handler.prov_counters, {self.subject: 2, 'https://w3id.org/oc/meta/br/0636066666': 1})
        with self.subTest('Modification. OCDMConjunctiveGraph. filesystem counter'):
            counter_handler = FilesystemCounterHandler(os.path.join('test', 'info_dir'))
            ocdm_conjunctive_graph = OCDMConjunctiveGraph(counter_handler=counter_handler)
            ocdm_conjunctive_graph.parse(os.path.join('test', 'br.nq'))
            ocdm_conjunctive_graph.provenance.counter_handler.set_counter(1, self.subject)
            ocdm_conjunctive_graph.preexisting_finished()
            ocdm_conjunctive_graph.remove((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy')))
            ocdm_conjunctive_graph.add((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('Bella zì')))
            ocdm_conjunctive_graph.generate_provenance()
            se_a_2: SnapshotEntity = ocdm_conjunctive_graph.get_entity(f'{self.subject}/prov/se/2')
            self.assertEqual(se_a_2.get_description(), f"The entity '{self.subject}' was modified.")
            self.assertEqual(se_a_2.get_is_snapshot_of(), URIRef(self.subject))
            self.assertEqual(se_a_2.get_derives_from()[0].res, URIRef('https://w3id.org/oc/meta/br/0605/prov/se/1'))
            self.assertEqual(se_a_2.get_update_action(), 'DELETE DATA { GRAPH <https://w3id.org/oc/meta/br/> { <https://w3id.org/oc/meta/br/0605> <http://purl.org/dc/terms/title> "A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy" . } }; INSERT DATA { GRAPH <https://w3id.org/oc/meta/br/> { <https://w3id.org/oc/meta/br/0605> <http://purl.org/dc/terms/title> "Bella zì" . } }')
            with open(os.path.join('test', 'info_dir', 'provenance_index.json'), 'r', encoding='utf8') as outfile:
                self.assertEqual(json.load(outfile), {'https://w3id.org/oc/meta/br/0605': 2, 'https://w3id.org/oc/meta/br/0636066666': 1, 'https://w3id.org/oc/meta/id/0636064270': 1, 'https://w3id.org/oc/meta/id/0605': 1})
        with self.subTest('Modification. OCDMConjunctiveGraph. database counter'):
            counter_handler = SqliteCounterHandler(os.path.join('test', 'database.db'))
            ocdm_conjunctive_graph = OCDMConjunctiveGraph(counter_handler=counter_handler)
            ocdm_conjunctive_graph.parse(os.path.join('test', 'br.nq'))
            ocdm_conjunctive_graph.provenance.counter_handler.set_counter(1, self.subject)
            ocdm_conjunctive_graph.preexisting_finished()
            ocdm_conjunctive_graph.provenance.counter_handler.set_counter(1, self.subject)
            ocdm_conjunctive_graph.remove((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy')))
            ocdm_conjunctive_graph.add((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('Bella zì')))
            ocdm_conjunctive_graph.generate_provenance()
            se_a_2: SnapshotEntity = ocdm_conjunctive_graph.get_entity(f'{self.subject}/prov/se/2')
            self.assertEqual(se_a_2.get_description(), f"The entity '{self.subject}' was modified.")
            self.assertEqual(se_a_2.get_is_snapshot_of(), URIRef(self.subject))
            self.assertEqual(se_a_2.get_derives_from()[0].res, URIRef('https://w3id.org/oc/meta/br/0605/prov/se/1'))
            self.assertEqual(se_a_2.get_update_action(), 'DELETE DATA { GRAPH <https://w3id.org/oc/meta/br/> { <https://w3id.org/oc/meta/br/0605> <http://purl.org/dc/terms/title> "A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy" . } }; INSERT DATA { GRAPH <https://w3id.org/oc/meta/br/> { <https://w3id.org/oc/meta/br/0605> <http://purl.org/dc/terms/title> "Bella zì" . } }')
    
    def test_generate_provenance_after_merge(self):
        ocdm_conjunctive_graph = OCDMConjunctiveGraph()
        ocdm_conjunctive_graph.parse(os.path.join('test', 'br.nq'))
        ocdm_conjunctive_graph.preexisting_finished()
        ocdm_conjunctive_graph.merge(URIRef('https://w3id.org/oc/meta/id/0605'), URIRef('https://w3id.org/oc/meta/id/0636064270'))
        ocdm_conjunctive_graph.generate_provenance()
        se_a_2: SnapshotEntity = ocdm_conjunctive_graph.get_entity(f'https://w3id.org/oc/meta/id/0605/prov/se/2')
        self.assertIsNotNone(se_a_2)
        self.assertEqual(se_a_2.get_description(), "The entity 'https://w3id.org/oc/meta/id/0605' was merged with 'https://w3id.org/oc/meta/id/0636064270'.")
        self.assertIsNone(se_a_2.get_update_action())
        self.assertEqual({str(se.res) for se in se_a_2.get_derives_from()}, {'https://w3id.org/oc/meta/id/0605/prov/se/1', 'https://w3id.org/oc/meta/id/0636064270/prov/se/1'})
        se_b_1: SnapshotEntity = ocdm_conjunctive_graph.get_entity(f'https://w3id.org/oc/meta/id/0636064270/prov/se/1')
        self.assertIsNotNone(se_b_1)
        self.assertEqual(se_b_1.get_description(), "The entity 'https://w3id.org/oc/meta/id/0636064270' has been created.")
        se_br_1 = ocdm_conjunctive_graph.get_entity('https://w3id.org/oc/meta/br/0636066666/prov/se/1')
        self.assertEqual(se_br_1.get_description(), "The entity 'https://w3id.org/oc/meta/br/0636066666' has been created.")
        se_br_2 = ocdm_conjunctive_graph.get_entity('https://w3id.org/oc/meta/br/0636066666/prov/se/2')
        self.assertEqual(se_br_2.get_description(), "The entity 'https://w3id.org/oc/meta/br/0636066666' was modified.")
        self.assertEqual(se_br_2.get_update_action(), "DELETE DATA { GRAPH <https://w3id.org/oc/meta/br/> { <https://w3id.org/oc/meta/br/0636066666> <http://purl.org/spar/datacite/hasIdentifier> <https://w3id.org/oc/meta/id/0636064270> . } }; INSERT DATA { GRAPH <https://w3id.org/oc/meta/br/> { <https://w3id.org/oc/meta/br/0636066666> <http://purl.org/spar/datacite/hasIdentifier> <https://w3id.org/oc/meta/id/0605> . } }")
        self.assertEqual(se_a_2.get_derives_from()[0].res, URIRef('https://w3id.org/oc/meta/id/0605/prov/se/1'))
        se_id_0636064270_1 = ocdm_conjunctive_graph.get_entity(f'https://w3id.org/oc/meta/id/0636064270/prov/se/1')
        se_id_0636064270_2 = ocdm_conjunctive_graph.get_entity(f'https://w3id.org/oc/meta/id/0636064270/prov/se/2')
        self.assertEqual(se_id_0636064270_1.get_description(), "The entity 'https://w3id.org/oc/meta/id/0636064270' has been created.")
        self.assertEqual(se_id_0636064270_2.get_description(), "The entity 'https://w3id.org/oc/meta/id/0636064270' has been deleted.")
        self.assertEqual(se_id_0636064270_2.get_update_action(), "DELETE DATA { GRAPH <https://w3id.org/oc/meta/id/> { <https://w3id.org/oc/meta/id/0636064270> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://purl.org/spar/datacite/Identifier> . } }")

if __name__ == '__main__':
    unittest.main()