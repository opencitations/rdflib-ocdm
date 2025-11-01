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

import unittest

from rdflib import Literal, Namespace, URIRef

from rdflib_ocdm.counter_handler.in_memory_counter_handler import \
    InMemoryCounterHandler
from rdflib_ocdm.ocdm_graph import OCDMGraph


class TestOCDMGraph(unittest.TestCase):

    def setUp(self):
        self.counter_handler = InMemoryCounterHandler()
        self.FOAF = Namespace("http://xmlns.com/foaf/0.1/")
        self.DCTERMS = Namespace("http://purl.org/dc/terms/")

    def test_merge_graph_basic(self):
        """Test merge operation with OCDMGraph (not Dataset)"""
        ocdm_graph = OCDMGraph(counter_handler=self.counter_handler)

        # Add some triples for entity A
        entity_a = URIRef('http://example.org/person/alice')
        ocdm_graph.add((entity_a, self.FOAF.name, Literal('Alice')))
        ocdm_graph.add((entity_a, self.FOAF.age, Literal(30)))

        # Add some triples for entity B
        entity_b = URIRef('http://example.org/person/bob')
        ocdm_graph.add((entity_b, self.FOAF.name, Literal('Bob')))
        ocdm_graph.add((entity_b, self.FOAF.age, Literal(25)))

        # Add reference to entity B as an object
        doc = URIRef('http://example.org/doc/1')
        ocdm_graph.add((doc, self.DCTERMS.creator, entity_b))

        ocdm_graph.preexisting_finished()

        # Merge B into A
        ocdm_graph.merge(entity_a, entity_b)

        # Check that B's triples are removed
        self.assertEqual(len(list(ocdm_graph.triples((entity_b, None, None)))), 0)

        # Check that reference to B now points to A
        creators = list(ocdm_graph.objects(doc, self.DCTERMS.creator))
        self.assertEqual(len(creators), 1)
        self.assertEqual(creators[0], entity_a)

        # Check that merge_index is updated
        self.assertIn(entity_a, ocdm_graph.merge_index)
        self.assertIn(entity_b, ocdm_graph.merge_index[entity_a])

        # Check that entity_index marks B as deleted
        self.assertTrue(ocdm_graph.entity_index[entity_b]['to_be_deleted'])

    def test_merge_graph_with_provenance(self):
        """Test merge operation generates correct provenance"""
        ocdm_graph = OCDMGraph(counter_handler=self.counter_handler)

        entity_a = URIRef('http://example.org/id/123')
        entity_b = URIRef('http://example.org/id/456')

        ocdm_graph.add((entity_a, self.DCTERMS.title, Literal('Entity A')))
        ocdm_graph.add((entity_b, self.DCTERMS.title, Literal('Entity B')))

        ocdm_graph.preexisting_finished()

        # Merge B into A
        ocdm_graph.merge(entity_a, entity_b)
        ocdm_graph.generate_provenance()

        # Check that provenance was created for both entities
        se_a_2 = ocdm_graph.get_entity(f'{entity_a}/prov/se/2')
        self.assertIsNotNone(se_a_2)
        self.assertIn('merged', se_a_2.get_description().lower())

        se_b_2 = ocdm_graph.get_entity(f'{entity_b}/prov/se/2')
        self.assertIsNotNone(se_b_2)
        self.assertTrue(se_b_2.get_description().endswith('has been deleted.'))

    def test_merge_graph_object_not_in_index(self):
        """Test merge when merged entity is not in entity_index"""
        ocdm_graph = OCDMGraph(counter_handler=self.counter_handler)

        entity_a = URIRef('http://example.org/entity/a')
        entity_b = URIRef('http://example.org/entity/b')

        # Add only entity A to the graph
        ocdm_graph.add((entity_a, self.FOAF.name, Literal('Entity A')))

        # Add a reference to entity B (which is not a subject)
        ocdm_graph.add((entity_a, self.FOAF.knows, entity_b))

        ocdm_graph.preexisting_finished()

        # Merge B into A (B is only an object, not a subject)
        ocdm_graph.merge(entity_a, entity_b)

        # Check that B was added to entity_index
        self.assertIn(entity_b, ocdm_graph.entity_index)
        self.assertTrue(ocdm_graph.entity_index[entity_b]['to_be_deleted'])


if __name__ == '__main__':
    unittest.main()
