# SPDX-FileCopyrightText: 2023-2025 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# SPDX-License-Identifier: ISC

import warnings

import pytest
from rdflib import Literal, Namespace, URIRef

from rdflib_ocdm.counter_handler.in_memory_counter_handler import \
    InMemoryCounterHandler
from rdflib_ocdm.ocdm_graph import OCDMConjunctiveGraph, OCDMDataset, OCDMGraph


class TestOCDMGraph:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.counter_handler = InMemoryCounterHandler()
        self.FOAF = Namespace("http://xmlns.com/foaf/0.1/")
        self.DCTERMS = Namespace("http://purl.org/dc/terms/")

    def test_merge_graph_basic(self):
        ocdm_graph = OCDMGraph(counter_handler=self.counter_handler)

        entity_a = URIRef('http://example.org/person/alice')
        ocdm_graph.add((entity_a, self.FOAF.name, Literal('Alice')))
        ocdm_graph.add((entity_a, self.FOAF.age, Literal(30)))

        entity_b = URIRef('http://example.org/person/bob')
        ocdm_graph.add((entity_b, self.FOAF.name, Literal('Bob')))
        ocdm_graph.add((entity_b, self.FOAF.age, Literal(25)))

        doc = URIRef('http://example.org/doc/1')
        ocdm_graph.add((doc, self.DCTERMS.creator, entity_b))

        ocdm_graph.preexisting_finished()

        ocdm_graph.merge(entity_a, entity_b)

        assert len(list(ocdm_graph.triples((entity_b, None, None)))) == 0

        creators = list(ocdm_graph.objects(doc, self.DCTERMS.creator))
        assert len(creators) == 1
        assert creators[0] == entity_a

        assert entity_a in ocdm_graph.merge_index
        assert entity_b in ocdm_graph.merge_index[entity_a]

        assert ocdm_graph.entity_index[entity_b]['to_be_deleted']

    def test_merge_graph_with_provenance(self):
        ocdm_graph = OCDMGraph(counter_handler=self.counter_handler)

        entity_a = URIRef('http://example.org/id/123')
        entity_b = URIRef('http://example.org/id/456')

        ocdm_graph.add((entity_a, self.DCTERMS.title, Literal('Entity A')))
        ocdm_graph.add((entity_b, self.DCTERMS.title, Literal('Entity B')))

        ocdm_graph.preexisting_finished()

        ocdm_graph.merge(entity_a, entity_b)
        ocdm_graph.generate_provenance()

        se_a_2 = ocdm_graph.get_entity(f'{entity_a}/prov/se/2')
        assert se_a_2 is not None
        description_a = se_a_2.get_description()
        assert description_a is not None
        assert 'merged' in description_a.lower()

        se_b_2 = ocdm_graph.get_entity(f'{entity_b}/prov/se/2')
        assert se_b_2 is not None
        description_b = se_b_2.get_description()
        assert description_b is not None
        assert description_b.endswith('has been deleted.')

    def test_merge_graph_object_not_in_index(self):
        ocdm_graph = OCDMGraph(counter_handler=self.counter_handler)

        entity_a = URIRef('http://example.org/entity/a')
        entity_b = URIRef('http://example.org/entity/b')

        ocdm_graph.add((entity_a, self.FOAF.name, Literal('Entity A')))
        ocdm_graph.add((entity_a, self.FOAF.knows, entity_b))

        ocdm_graph.preexisting_finished()

        ocdm_graph.merge(entity_a, entity_b)

        assert entity_b in ocdm_graph.entity_index
        assert ocdm_graph.entity_index[entity_b]['to_be_deleted']

    def test_backward_compatibility_ocdm_conjunctive_graph(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            ocdm_graph = OCDMConjunctiveGraph(counter_handler=self.counter_handler)

            our_warnings = [
                warning for warning in w
                if issubclass(warning.category, DeprecationWarning)
                and "OCDMConjunctiveGraph is deprecated" in str(warning.message)
            ]

            assert len(our_warnings) == 1
            assert "use OCDMDataset instead" in str(our_warnings[0].message)

            assert isinstance(ocdm_graph, OCDMDataset)

            entity = URIRef('http://example.org/entity')
            ocdm_graph.add((entity, self.FOAF.name, Literal('Test')))
            assert len(list(ocdm_graph.quads((entity, None, None, None)))) == 1
