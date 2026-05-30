# SPDX-FileCopyrightText: 2025 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# SPDX-License-Identifier: ISC

from rdflib import RDF, Dataset, Graph, Literal, URIRef

from rdflib_ocdm.support import (_get_match, create_literal, create_type,
                                 get_entity_subgraph, get_prov_count,
                                 is_string_empty)


class TestSupport:
    def test_get_match_no_match(self):
        result = _get_match(r"^test(\d+)$", 1, "no-match-here")
        assert result == ""

    def test_get_match_with_match(self):
        result = _get_match(r"^test(\d+)$", 1, "test123")
        assert result == "123"

    def test_is_string_empty_none(self):
        assert is_string_empty(None)

    def test_is_string_empty_whitespace(self):
        assert is_string_empty("   ")
        assert is_string_empty("\t\n")

    def test_is_string_empty_non_empty(self):
        assert not is_string_empty("test")
        assert not is_string_empty(" test ")

    def test_get_prov_count_valid(self):
        uri = URIRef('http://example.org/entity/123/prov/se/5')
        result = get_prov_count(uri)
        assert result == "5"

    def test_get_prov_count_invalid(self):
        uri = URIRef('http://example.org/entity/123')
        result = get_prov_count(uri)
        assert result is None

    def test_get_entity_subgraph_dataset(self):
        dataset = Dataset()
        entity = URIRef('http://example.org/entity')
        graph_id = URIRef('http://example.org/graph/')

        dataset.add((entity, URIRef('http://example.org/p1'), Literal('value1'), Graph(identifier=graph_id)))
        dataset.add((entity, URIRef('http://example.org/p2'), Literal('value2'), Graph(identifier=graph_id)))
        dataset.add((URIRef('http://example.org/other'), URIRef('http://example.org/p3'), Literal('value3'), Graph(identifier=graph_id)))

        subgraph = get_entity_subgraph(dataset, entity)
        assert len(subgraph) == 2
        assert isinstance(subgraph, Dataset)

    def test_get_entity_subgraph_graph(self):
        graph = Graph()
        entity = URIRef('http://example.org/entity')

        graph.add((entity, URIRef('http://example.org/p1'), Literal('value1')))
        graph.add((entity, URIRef('http://example.org/p2'), Literal('value2')))
        graph.add((URIRef('http://example.org/other'), URIRef('http://example.org/p3'), Literal('value3')))

        subgraph = get_entity_subgraph(graph, entity)
        assert len(subgraph) == 2
        assert isinstance(subgraph, Graph)

    def test_create_literal_valid(self):
        graph = Graph()
        res = URIRef('http://example.org/entity')
        p = URIRef('http://example.org/property')

        create_literal(graph, res, p, 'test value')
        values = list(graph.objects(res, p))
        assert len(values) == 1
        assert str(values[0]) == 'test value'

    def test_create_literal_empty_string(self):
        graph = Graph()
        res = URIRef('http://example.org/entity')
        p = URIRef('http://example.org/property')

        create_literal(graph, res, p, '')
        values = list(graph.objects(res, p))
        assert len(values) == 0

    def test_create_literal_none(self):
        graph = Graph()
        res = URIRef('http://example.org/entity')
        p = URIRef('http://example.org/property')

        create_literal(graph, res, p, None)
        values = list(graph.objects(res, p))
        assert len(values) == 0

    def test_create_type_dataset(self):
        dataset = Dataset()
        res = URIRef('http://example.org/entity')
        res_type = URIRef('http://example.org/Type')
        graph_id = 'http://example.org/graph/'

        create_type(dataset, res, res_type, graph_id)

        types = [o for s, p, o, g in dataset.quads((res, RDF.type, None, None))]
        assert len(types) == 1
        assert types[0] == res_type

    def test_create_type_graph(self):
        graph = Graph()
        res = URIRef('http://example.org/entity')
        res_type = URIRef('http://example.org/Type')

        create_type(graph, res, res_type)

        types = list(graph.objects(res, RDF.type))
        assert len(types) == 1
        assert types[0] == res_type
