# SPDX-FileCopyrightText: 2023-2026 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# SPDX-License-Identifier: ISC

import os
import shutil
import tempfile
from unittest.mock import patch

import pytest
from oc_ocdm.support.reporter import Reporter
from rdflib import Graph, Literal, URIRef

from rdflib_ocdm.ocdm_graph import OCDMDataset, OCDMGraph
from rdflib_ocdm.storer import Storer

LONG_TITLE = (
    "A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy"
)


class TestStorer:
    endpoint = "http://localhost:8890/sparql"

    @pytest.fixture(autouse=True)
    def setup(self, sparql_wrapper, subject, cur_time):
        self.subject = subject
        self.base_dir = "test/"
        self.cur_time = cur_time
        self.ocdm_graph = OCDMGraph()
        self.ocdm_graph.parse(os.path.join("test", "br_small.nq"))
        self.storer = Storer(self.ocdm_graph)
        self.ts = sparql_wrapper
        yield
        tp_err_dir = os.path.join(self.base_dir, "tp_err")
        if os.path.exists(tp_err_dir):
            shutil.rmtree(tp_err_dir)

    def test_upload_all_graph(self):
        ocdm_graph = OCDMDataset()
        ocdm_graph.preexisting_finished()
        ocdm_graph.parse(os.path.join("test", "br_small.nq"))
        storer = Storer(ocdm_graph)
        storer.upload_all(self.endpoint, self.base_dir)
        query = """
            SELECT ?s ?p ?o
            WHERE {
                VALUES (?s) {(<https://w3id.org/oc/meta/br/0605>) (<https://w3id.org/oc/meta/br/0636066666>)}
                ?s ?p ?o
            }
        """
        self.ts.setQuery(query)
        raw_results = self.ts.queryAndConvert()
        assert isinstance(raw_results, dict)
        results = {
            (result["s"]["value"], result["p"]["value"], result["o"]["value"])
            for result in raw_results["results"]["bindings"]
        }
        expected_results = {
            (
                "https://w3id.org/oc/meta/br/0636066666",
                "http://purl.org/dc/terms/title",
                "Ironing Out Tau'S Role In Parkinsonism",
            ),
            (
                "https://w3id.org/oc/meta/br/0605",
                "http://purl.org/dc/terms/title",
                LONG_TITLE,
            ),
        }
        assert results == expected_results
        ocdm_graph.commit_changes()
        ocdm_graph.remove(
            (
                URIRef(self.subject),
                URIRef("http://purl.org/dc/terms/title"),
                Literal(LONG_TITLE),
                Graph(identifier=URIRef("https://w3id.org/oc/meta/br/")),
            )
        )
        ocdm_graph.add(
            (
                URIRef(self.subject),
                URIRef("http://purl.org/dc/terms/title"),
                Literal("Bella zì"),
                Graph(identifier=URIRef("https://w3id.org/oc/meta/br/")),
            )
        )
        ocdm_graph.generate_provenance(c_time=self.cur_time)
        storer.upload_all(self.endpoint, self.base_dir)
        query = """
            SELECT ?s ?p ?o
            WHERE {
                VALUES (?s) {(<https://w3id.org/oc/meta/br/0605>) (<https://w3id.org/oc/meta/br/0636066666>)}
                ?s ?p ?o
            }
        """
        self.ts.setQuery(query)
        raw_results = self.ts.queryAndConvert()
        assert isinstance(raw_results, dict)
        results = {
            (result["s"]["value"], result["p"]["value"], result["o"]["value"])
            for result in raw_results["results"]["bindings"]
        }
        expected_results = {
            (
                "https://w3id.org/oc/meta/br/0636066666",
                "http://purl.org/dc/terms/title",
                "Ironing Out Tau'S Role In Parkinsonism",
            ),
            (
                "https://w3id.org/oc/meta/br/0605",
                "http://purl.org/dc/terms/title",
                "Bella zì",
            ),
        }
        assert results == expected_results

    def test_upload_all_provenance(self):
        ocdm_graph = OCDMDataset()
        ocdm_graph.parse(
            os.path.join("test", "br_small.nq"),
            resp_agent=URIRef("https://orcid.org/0000-0002-8420-0696"),
            primary_source=URIRef("https://api.crossref.org/"),
        )
        ocdm_graph.preexisting_finished(
            resp_agent="https://orcid.org/0000-0002-8420-0696",
            primary_source="https://api.crossref.org/",
            c_time=self.cur_time,
        )
        ocdm_graph.remove(
            (
                URIRef(self.subject),
                URIRef("http://purl.org/dc/terms/title"),
                Literal(LONG_TITLE),
                Graph(identifier=URIRef("https://w3id.org/oc/meta/br/")),
            )
        )
        ocdm_graph.add(
            (
                URIRef(self.subject),
                URIRef("http://purl.org/dc/terms/title"),
                Literal("Bella zì"),
                Graph(identifier=URIRef("https://w3id.org/oc/meta/br/")),
            ),
            resp_agent="https://orcid.org/0000-0002-8420-0696",
            primary_source="https://api.crossref.org/",
        )
        ocdm_graph.generate_provenance(c_time=self.cur_time)
        prov_storer = Storer(ocdm_graph.provenance)
        prov_storer.upload_all(self.endpoint)
        query = """
            PREFIX prov: <http://www.w3.org/ns/prov#>
            SELECT ?g ?s ?p ?o
            WHERE {
                GRAPH ?g {
                    ?s a prov:Entity;
                        ?p ?o.
                }
            }
        """
        self.ts.setQuery(query)
        raw_results = self.ts.queryAndConvert()
        assert isinstance(raw_results, dict)
        results = {
            (
                result["g"]["value"],
                result["s"]["value"],
                result["p"]["value"],
                result["o"]["value"],
            )
            for result in raw_results["results"]["bindings"]
        }
        expected_result = {
            (
                "https://w3id.org/oc/meta/br/0605/prov/",
                "https://w3id.org/oc/meta/br/0605/prov/se/2",
                "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
                "http://www.w3.org/ns/prov#Entity",
            ),
            (
                "https://w3id.org/oc/meta/br/0636066666/prov/",
                "https://w3id.org/oc/meta/br/0636066666/prov/se/1",
                "http://www.w3.org/ns/prov#generatedAtTime",
                "2020-12-07T21:17:34Z",
            ),
            (
                "https://w3id.org/oc/meta/br/0605/prov/",
                "https://w3id.org/oc/meta/br/0605/prov/se/1",
                "http://www.w3.org/ns/prov#generatedAtTime",
                "2020-12-07T21:17:34Z",
            ),
            (
                "https://w3id.org/oc/meta/br/0605/prov/",
                "https://w3id.org/oc/meta/br/0605/prov/se/1",
                "http://www.w3.org/ns/prov#invalidatedAtTime",
                "2020-12-07T21:17:39Z",
            ),
            (
                "https://w3id.org/oc/meta/br/0636066666/prov/",
                "https://w3id.org/oc/meta/br/0636066666/prov/se/1",
                "http://www.w3.org/ns/prov#specializationOf",
                "https://w3id.org/oc/meta/br/0636066666",
            ),
            (
                "https://w3id.org/oc/meta/br/0605/prov/",
                "https://w3id.org/oc/meta/br/0605/prov/se/2",
                "https://w3id.org/oc/ontology/hasUpdateQuery",
                "DELETE DATA {"
                " GRAPH <https://w3id.org/oc/meta/br/> {"
                " <https://w3id.org/oc/meta/br/0605>"
                " <http://purl.org/dc/terms/title>"
                f' "{LONG_TITLE}" . '
                "} }; INSERT DATA {"
                " GRAPH <https://w3id.org/oc/meta/br/> {"
                " <https://w3id.org/oc/meta/br/0605>"
                " <http://purl.org/dc/terms/title>"
                ' "Bella zì" . } }',
            ),
            (
                "https://w3id.org/oc/meta/br/0605/prov/",
                "https://w3id.org/oc/meta/br/0605/prov/se/2",
                "http://www.w3.org/ns/prov#hadPrimarySource",
                "https://api.crossref.org/",
            ),
            (
                "https://w3id.org/oc/meta/br/0605/prov/",
                "https://w3id.org/oc/meta/br/0605/prov/se/2",
                "http://www.w3.org/ns/prov#generatedAtTime",
                "2020-12-07T21:17:39Z",
            ),
            (
                "https://w3id.org/oc/meta/br/0605/prov/",
                "https://w3id.org/oc/meta/br/0605/prov/se/2",
                "http://www.w3.org/ns/prov#specializationOf",
                "https://w3id.org/oc/meta/br/0605",
            ),
            (
                "https://w3id.org/oc/meta/br/0605/prov/",
                "https://w3id.org/oc/meta/br/0605/prov/se/2",
                "http://purl.org/dc/terms/description",
                "The entity 'https://w3id.org/oc/meta/br/0605' was modified.",
            ),
            (
                "https://w3id.org/oc/meta/br/0605/prov/",
                "https://w3id.org/oc/meta/br/0605/prov/se/2",
                "http://www.w3.org/ns/prov#wasAttributedTo",
                "https://orcid.org/0000-0002-8420-0696",
            ),
            (
                "https://w3id.org/oc/meta/br/0605/prov/",
                "https://w3id.org/oc/meta/br/0605/prov/se/2",
                "http://www.w3.org/ns/prov#wasDerivedFrom",
                "https://w3id.org/oc/meta/br/0605/prov/se/1",
            ),
            (
                "https://w3id.org/oc/meta/br/0605/prov/",
                "https://w3id.org/oc/meta/br/0605/prov/se/1",
                "http://purl.org/dc/terms/description",
                "The entity 'https://w3id.org/oc/meta/br/0605' has been created.",
            ),
            (
                "https://w3id.org/oc/meta/br/0605/prov/",
                "https://w3id.org/oc/meta/br/0605/prov/se/1",
                "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
                "http://www.w3.org/ns/prov#Entity",
            ),
            (
                "https://w3id.org/oc/meta/br/0636066666/prov/",
                "https://w3id.org/oc/meta/br/0636066666/prov/se/1",
                "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
                "http://www.w3.org/ns/prov#Entity",
            ),
            (
                "https://w3id.org/oc/meta/br/0636066666/prov/",
                "https://w3id.org/oc/meta/br/0636066666/prov/se/1",
                "http://purl.org/dc/terms/description",
                "The entity 'https://w3id.org/oc/meta/br/0636066666' has been created.",
            ),
            (
                "https://w3id.org/oc/meta/br/0605/prov/",
                "https://w3id.org/oc/meta/br/0605/prov/se/1",
                "http://www.w3.org/ns/prov#specializationOf",
                "https://w3id.org/oc/meta/br/0605",
            ),
            (
                "https://w3id.org/oc/meta/br/0605/prov/",
                "https://w3id.org/oc/meta/br/0605/prov/se/1",
                "http://www.w3.org/ns/prov#wasAttributedTo",
                "https://orcid.org/0000-0002-8420-0696",
            ),
            (
                "https://w3id.org/oc/meta/br/0636066666/prov/",
                "https://w3id.org/oc/meta/br/0636066666/prov/se/1",
                "http://www.w3.org/ns/prov#hadPrimarySource",
                "https://api.crossref.org/",
            ),
            (
                "https://w3id.org/oc/meta/br/0636066666/prov/",
                "https://w3id.org/oc/meta/br/0636066666/prov/se/1",
                "http://www.w3.org/ns/prov#wasAttributedTo",
                "https://orcid.org/0000-0002-8420-0696",
            ),
            (
                "https://w3id.org/oc/meta/br/0605/prov/",
                "https://w3id.org/oc/meta/br/0605/prov/se/1",
                "http://www.w3.org/ns/prov#hadPrimarySource",
                "https://api.crossref.org/",
            ),
        }
        assert results == expected_result

    def test_storer_error_handling_with_base_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ocdm_graph = OCDMGraph()
            ocdm_graph.add(
                (
                    URIRef("http://example.org/s"),
                    URIRef("http://example.org/p"),
                    Literal("test"),
                )
            )
            storer = Storer(ocdm_graph)

            with patch(
                "rdflib_ocdm.storer.execute_with_retry",
                side_effect=ValueError("Connection failed"),
            ):
                result = storer.upload_all(
                    "http://invalid-endpoint:9999/sparql", base_dir=temp_dir
                )

                assert not result

                tp_err_dir = os.path.join(temp_dir, "tp_err")
                assert os.path.exists(tp_err_dir)

                error_files = os.listdir(tp_err_dir)
                assert len(error_files) == 1
                assert error_files[0].endswith("_not_uploaded.txt")

    def test_storer_error_handling_without_base_dir(self):
        ocdm_graph = OCDMGraph()
        ocdm_graph.add(
            (
                URIRef("http://example.org/s"),
                URIRef("http://example.org/p"),
                Literal("test"),
            )
        )
        storer = Storer(ocdm_graph)

        with patch(
            "rdflib_ocdm.storer.execute_with_retry",
            side_effect=ValueError("Connection failed"),
        ):
            result = storer.upload_all(
                "http://invalid-endpoint:9999/sparql", base_dir=None
            )

            assert not result

    def test_storer_unsupported_output_format(self):
        ocdm_graph = OCDMGraph()
        with pytest.raises(ValueError) as exc_info:
            Storer(ocdm_graph, output_format="unsupported-format")
        assert "not supported" in str(exc_info.value)
        assert "unsupported-format" in str(exc_info.value)

    def test_storer_custom_reporters(self):
        ocdm_graph = OCDMGraph()
        ocdm_graph.add(
            (
                URIRef("http://example.org/s"),
                URIRef("http://example.org/p"),
                Literal("test"),
            )
        )

        custom_repok = Reporter(prefix="[CUSTOM OK] ")
        custom_reperr = Reporter(prefix="[CUSTOM ERROR] ")

        storer = Storer(ocdm_graph, repok=custom_repok, reperr=custom_reperr)

        assert storer.repok == custom_repok
        assert storer.reperr == custom_reperr

    def test_storer_batch_upload_multiple_batches(self):
        ocdm_graph = OCDMDataset()
        ocdm_graph.preexisting_finished()

        for i in range(5):
            ocdm_graph.add(
                (
                    URIRef(f"http://example.org/entity/{i}"),
                    URIRef("http://purl.org/dc/terms/title"),
                    Literal(f"Entity {i}"),
                    Graph(identifier=URIRef("http://example.org/graph/")),
                )
            )

        storer = Storer(ocdm_graph)

        result = storer.upload_all(self.endpoint, self.base_dir, batch_size=2)

        assert result

        query = """
            SELECT (COUNT(?s) as ?count)
            WHERE {
                ?s <http://purl.org/dc/terms/title> ?o .
                FILTER(STRSTARTS(STR(?s), "http://example.org/entity/"))
            }
        """
        self.ts.setQuery(query)
        raw_results = self.ts.queryAndConvert()
        assert isinstance(raw_results, dict)
        count = int(raw_results["results"]["bindings"][0]["count"]["value"])
        assert count == 5

    def test_storer_negative_batch_size(self):
        ocdm_graph = OCDMDataset()
        ocdm_graph.preexisting_finished()
        ocdm_graph.add(
            (
                URIRef("http://example.org/s"),
                URIRef("http://example.org/p"),
                Literal("test"),
                Graph(identifier=URIRef("http://example.org/graph/")),
            )
        )

        storer = Storer(ocdm_graph)

        result = storer.upload_all(self.endpoint, self.base_dir, batch_size=-5)

        assert result

    def test_storer_zero_batch_size(self):
        ocdm_graph = OCDMDataset()
        ocdm_graph.preexisting_finished()
        ocdm_graph.add(
            (
                URIRef("http://example.org/s"),
                URIRef("http://example.org/p"),
                Literal("test"),
                Graph(identifier=URIRef("http://example.org/graph/")),
            )
        )

        storer = Storer(ocdm_graph)

        result = storer.upload_all(self.endpoint, self.base_dir, batch_size=0)

        assert result
