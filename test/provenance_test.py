# SPDX-FileCopyrightText: 2023-2025 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# SPDX-License-Identifier: ISC

import json
import os

import pytest
from rdflib import Literal, URIRef

from rdflib_ocdm.counter_handler.filesystem_counter_handler import \
    FilesystemCounterHandler
from rdflib_ocdm.counter_handler.in_memory_counter_handler import \
    InMemoryCounterHandler
from rdflib_ocdm.counter_handler.sqlite_counter_handler import \
    SqliteCounterHandler
from rdflib_ocdm.ocdm_graph import OCDMDataset, OCDMGraph
from rdflib_ocdm.prov.provenance import OCDMProvenance
from rdflib_ocdm.prov.snapshot_entity import SnapshotEntity


class TestOCDMProvenance:
    @pytest.fixture(autouse=True)
    def setup(self, subject, cur_time, cur_time_str):
        self.subject = subject
        self.cur_time = cur_time
        self.cur_time_str = cur_time_str
        yield
        db_path = os.path.join('test', 'database.db')
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except Exception:
                pass

    def test_add_se(self):
        ocdm_graph = OCDMGraph()
        ocdm_prov_memory = OCDMProvenance(ocdm_graph)
        ocdm_graph.add((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('Bella zì')))
        se = ocdm_prov_memory.add_se(prov_subject=URIRef(self.subject))
        assert se is not None
        assert isinstance(se, SnapshotEntity)
        assert str(se.res) == 'https://w3id.org/oc/meta/br/0605/prov/se/1'

    def test_generate_provenance_creation_no_snapshot_modification_ocdm_graph(self):
        ocdm_graph = OCDMGraph()
        ocdm_graph.parse(os.path.join('test', 'br.nt'))
        ocdm_graph.preexisting_finished(resp_agent='https://orcid.org/0000-0002-8420-0696', primary_source='https://api.crossref.org/', c_time=self.cur_time)
        result = ocdm_graph.generate_provenance(c_time=self.cur_time)
        assert result is None
        se_a = ocdm_graph.get_entity(f'{self.subject}/prov/se/1')
        assert se_a is not None
        assert isinstance(se_a, SnapshotEntity)
        assert URIRef(self.subject) == se_a.get_is_snapshot_of()
        assert self.cur_time_str == se_a.get_generation_time()
        assert f"The entity '{self.subject}' has been created." == se_a.get_description()
        assert se_a.get_primary_source() == URIRef('https://api.crossref.org/')
        assert se_a.get_resp_agent() == URIRef('https://orcid.org/0000-0002-8420-0696')
        ocdm_graph.generate_provenance(c_time=self.cur_time)
        se_a_2 = ocdm_graph.get_entity(f'{self.subject}/prov/se/2')
        assert se_a_2 is None
        ocdm_graph.remove((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy')))
        ocdm_graph.add((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('Bella zì')))
        ocdm_graph.generate_provenance()
        se_a_2 = ocdm_graph.get_entity(f'{self.subject}/prov/se/2')
        assert se_a_2 is not None
        assert se_a_2.get_update_action() == 'DELETE DATA { <https://w3id.org/oc/meta/br/0605> <http://purl.org/dc/terms/title> "A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy" . }; INSERT DATA { <https://w3id.org/oc/meta/br/0605> <http://purl.org/dc/terms/title> "Bella zì" . }'
        assert se_a_2.get_description() == f"The entity '{self.subject}' was modified."
        assert isinstance(ocdm_graph.provenance.counter_handler, InMemoryCounterHandler)
        assert ocdm_graph.provenance.counter_handler.prov_counters == {self.subject: 2, 'https://w3id.org/oc/meta/br/0636066666': 1}

    def test_generate_provenance_modification_ocdm_conjunctive_graph_filesystem_counter(self):
        counter_handler = FilesystemCounterHandler(os.path.join('test', 'info_dir'))
        ocdm_conjunctive_graph = OCDMDataset(counter_handler=counter_handler)
        ocdm_conjunctive_graph.parse(os.path.join('test', 'br.nq'))
        ocdm_conjunctive_graph.provenance.counter_handler.set_counter(1, self.subject)
        ocdm_conjunctive_graph.preexisting_finished()
        ocdm_conjunctive_graph.remove((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy')))
        ocdm_conjunctive_graph.add((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('Bella zì')))
        ocdm_conjunctive_graph.generate_provenance()
        se_a_2 = ocdm_conjunctive_graph.get_entity(f'{self.subject}/prov/se/2')
        assert se_a_2 is not None
        assert se_a_2.get_description() == f"The entity '{self.subject}' was modified."
        assert se_a_2.get_is_snapshot_of() == URIRef(self.subject)
        assert se_a_2.get_derives_from()[0].res == URIRef('https://w3id.org/oc/meta/br/0605/prov/se/1')
        assert se_a_2.get_update_action() == 'DELETE DATA { GRAPH <https://w3id.org/oc/meta/br/> { <https://w3id.org/oc/meta/br/0605> <http://purl.org/dc/terms/title> "A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy" . } }; INSERT DATA { GRAPH <https://w3id.org/oc/meta/br/> { <https://w3id.org/oc/meta/br/0605> <http://purl.org/dc/terms/title> "Bella zì" . } }'
        with open(os.path.join('test', 'info_dir', 'provenance_index.json'), 'r', encoding='utf8') as outfile:
            assert json.load(outfile) == {'https://w3id.org/oc/meta/br/0605': 2, 'https://w3id.org/oc/meta/br/0636066666': 1, 'https://w3id.org/oc/meta/id/0636064270': 1, 'https://w3id.org/oc/meta/id/0605': 1}

    def test_generate_provenance_modification_ocdm_conjunctive_graph_database_counter(self):
        counter_handler = SqliteCounterHandler(os.path.join('test', 'database.db'))
        try:
            ocdm_conjunctive_graph = OCDMDataset(counter_handler=counter_handler)
            ocdm_conjunctive_graph.parse(os.path.join('test', 'br.nq'))
            ocdm_conjunctive_graph.provenance.counter_handler.set_counter(1, self.subject)
            ocdm_conjunctive_graph.preexisting_finished()
            ocdm_conjunctive_graph.provenance.counter_handler.set_counter(1, self.subject)
            ocdm_conjunctive_graph.remove((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy')))
            ocdm_conjunctive_graph.add((URIRef(self.subject), URIRef('http://purl.org/dc/terms/title'), Literal('Bella zì')))
            ocdm_conjunctive_graph.generate_provenance()
            se_a_2 = ocdm_conjunctive_graph.get_entity(f'{self.subject}/prov/se/2')
            assert se_a_2 is not None
            assert se_a_2.get_description() == f"The entity '{self.subject}' was modified."
            assert se_a_2.get_is_snapshot_of() == URIRef(self.subject)
            assert se_a_2.get_derives_from()[0].res == URIRef('https://w3id.org/oc/meta/br/0605/prov/se/1')
            assert se_a_2.get_update_action() == 'DELETE DATA { GRAPH <https://w3id.org/oc/meta/br/> { <https://w3id.org/oc/meta/br/0605> <http://purl.org/dc/terms/title> "A Review Of Hemolytic Uremic Syndrome In Patients Treated With Gemcitabine Therapy" . } }; INSERT DATA { GRAPH <https://w3id.org/oc/meta/br/> { <https://w3id.org/oc/meta/br/0605> <http://purl.org/dc/terms/title> "Bella zì" . } }'
        finally:
            counter_handler.close()

    def test_generate_provenance_after_merge(self):
        ocdm_conjunctive_graph = OCDMDataset()
        ocdm_conjunctive_graph.parse(os.path.join('test', 'br.nq'))
        ocdm_conjunctive_graph.preexisting_finished()
        ocdm_conjunctive_graph.merge(URIRef('https://w3id.org/oc/meta/id/0605'), URIRef('https://w3id.org/oc/meta/id/0636064270'))
        ocdm_conjunctive_graph.generate_provenance()
        se_a_2 = ocdm_conjunctive_graph.get_entity(f'https://w3id.org/oc/meta/id/0605/prov/se/2')
        assert se_a_2 is not None
        assert se_a_2.get_description() == "The entity 'https://w3id.org/oc/meta/id/0605' was merged with 'https://w3id.org/oc/meta/id/0636064270'."
        assert se_a_2.get_update_action() is None
        assert {str(se.res) for se in se_a_2.get_derives_from()} == {'https://w3id.org/oc/meta/id/0605/prov/se/1', 'https://w3id.org/oc/meta/id/0636064270/prov/se/1'}
        se_b_1 = ocdm_conjunctive_graph.get_entity(f'https://w3id.org/oc/meta/id/0636064270/prov/se/1')
        assert se_b_1 is not None
        assert se_b_1.get_description() == "The entity 'https://w3id.org/oc/meta/id/0636064270' has been created."
        se_br_1 = ocdm_conjunctive_graph.get_entity('https://w3id.org/oc/meta/br/0636066666/prov/se/1')
        assert se_br_1 is not None
        assert se_br_1.get_description() == "The entity 'https://w3id.org/oc/meta/br/0636066666' has been created."
        se_br_2 = ocdm_conjunctive_graph.get_entity('https://w3id.org/oc/meta/br/0636066666/prov/se/2')
        assert se_br_2 is not None
        assert se_br_2.get_description() == "The entity 'https://w3id.org/oc/meta/br/0636066666' was modified."
        assert se_br_2.get_update_action() == "DELETE DATA { GRAPH <https://w3id.org/oc/meta/br/> { <https://w3id.org/oc/meta/br/0636066666> <http://purl.org/spar/datacite/hasIdentifier> <https://w3id.org/oc/meta/id/0636064270> . } }; INSERT DATA { GRAPH <https://w3id.org/oc/meta/br/> { <https://w3id.org/oc/meta/br/0636066666> <http://purl.org/spar/datacite/hasIdentifier> <https://w3id.org/oc/meta/id/0605> . } }"
        assert se_a_2.get_derives_from()[0].res == URIRef('https://w3id.org/oc/meta/id/0605/prov/se/1')
        se_id_0636064270_1 = ocdm_conjunctive_graph.get_entity(f'https://w3id.org/oc/meta/id/0636064270/prov/se/1')
        assert se_id_0636064270_1 is not None
        se_id_0636064270_2 = ocdm_conjunctive_graph.get_entity(f'https://w3id.org/oc/meta/id/0636064270/prov/se/2')
        assert se_id_0636064270_2 is not None
        assert se_id_0636064270_1.get_description() == "The entity 'https://w3id.org/oc/meta/id/0636064270' has been created."
        assert se_id_0636064270_2.get_description() == "The entity 'https://w3id.org/oc/meta/id/0636064270' has been deleted."
        assert se_id_0636064270_2.get_update_action() == "DELETE DATA { GRAPH <https://w3id.org/oc/meta/id/> { <https://w3id.org/oc/meta/id/0636064270> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://purl.org/spar/datacite/Identifier> . } }"

    def test_restore_deleted_entity(self):
        ocdm_graph = OCDMGraph()
        subject_uri = URIRef(self.subject)
        ocdm_graph.add((subject_uri, URIRef('http://purl.org/dc/terms/title'), Literal('Test Title')))
        ocdm_graph.preexisting_finished(c_time=self.cur_time)

        initial_snapshot = ocdm_graph.get_entity(f'{self.subject}/prov/se/1')
        assert initial_snapshot is not None
        assert initial_snapshot.get_description() == f"The entity '{self.subject}' has been created."

        ocdm_graph.mark_as_deleted(subject_uri)
        deletion_time = '2020-12-08T21:17:34+00:00'
        ocdm_graph.generate_provenance(c_time=1607462254.846196)

        deletion_snapshot = ocdm_graph.get_entity(f'{self.subject}/prov/se/2')
        assert deletion_snapshot is not None
        assert deletion_snapshot.get_generation_time() == deletion_time
        assert deletion_snapshot.get_invalidation_time() == deletion_time
        assert deletion_snapshot.get_description() == f"The entity '{self.subject}' has been deleted."

        ocdm_graph.mark_as_restored(subject_uri)
        ocdm_graph.add((subject_uri, URIRef('http://purl.org/dc/terms/title'), Literal('Restored Title')))

        restore_time = '2020-12-09T21:17:34+00:00'
        ocdm_graph.generate_provenance(c_time=1607548654.846196)

        restore_snapshot = ocdm_graph.get_entity(f'{self.subject}/prov/se/3')
        assert restore_snapshot is not None
        assert restore_snapshot.get_generation_time() == restore_time
        assert restore_snapshot.get_invalidation_time() is None
        assert restore_snapshot.get_description() == f"The entity '{self.subject}' has been restored."
        assert restore_snapshot.get_derives_from()[0].res == deletion_snapshot.res
        assert restore_snapshot.get_update_action() is not None

    def test_entity_deleted_after_mark_with_graph_context(self):
        ocdm_dataset = OCDMDataset()
        ocdm_dataset.parse(os.path.join('test', 'br.nq'))
        ocdm_dataset.preexisting_finished(c_time=self.cur_time)

        entity_uri = URIRef('https://w3id.org/oc/meta/id/0605')

        assert entity_uri in ocdm_dataset.entity_index
        assert ocdm_dataset.entity_index[entity_uri]['graph_iri'] == URIRef('https://w3id.org/oc/meta/id/')

        ocdm_dataset.mark_as_deleted(entity_uri)
        ocdm_dataset.generate_provenance(c_time=self.cur_time + 100)

        deletion_snapshot = ocdm_dataset.get_entity(f'{entity_uri}/prov/se/2')
        assert deletion_snapshot is not None
        assert deletion_snapshot.get_description() == f"The entity '{entity_uri}' has been deleted."

        update_action = deletion_snapshot.get_update_action()
        assert update_action is not None
        assert 'GRAPH <https://w3id.org/oc/meta/id/>' in update_action
        assert 'DELETE DATA' in update_action
        assert str(entity_uri) in update_action
