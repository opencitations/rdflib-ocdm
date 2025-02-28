#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2016, Silvio Peroni <essepuntato@gmail.com>
# Copyright (c) 2023, Arcangelo Massari <arcangelo.massari@unibo.it>
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

from typing import TYPE_CHECKING

from rdflib import Namespace, URIRef

if TYPE_CHECKING:
    from rdflib_ocdm.prov.provenance import OCDMProvenance

from rdflib_ocdm.abstract_entity import AbstractEntity

if TYPE_CHECKING:
    from typing import ClassVar, Dict


class ProvEntity(AbstractEntity):
    """Snapshot of entity metadata: a particular snapshot recording the
    metadata associated with an individual entity at a particular date and time, 
    including the agent, such as a person, organisation or automated process 
    that created or modified the entity metadata.
    """

    DCTERMS: ClassVar[Namespace] = Namespace("http://purl.org/dc/terms/")
    OCO: ClassVar[Namespace] = Namespace("https://w3id.org/oc/ontology/")
    PROV: ClassVar[Namespace] = Namespace("http://www.w3.org/ns/prov#")

    iri_entity: ClassVar[URIRef] = PROV.Entity
    iri_generated_at_time: ClassVar[URIRef] = PROV.generatedAtTime
    iri_invalidated_at_time: ClassVar[URIRef] = PROV.invalidatedAtTime
    iri_specialization_of: ClassVar[URIRef] = PROV.specializationOf
    iri_was_derived_from: ClassVar[URIRef] = PROV.wasDerivedFrom
    iri_had_primary_source: ClassVar[URIRef] = PROV.hadPrimarySource
    iri_was_attributed_to: ClassVar[URIRef] = PROV.wasAttributedTo
    iri_description: ClassVar[URIRef] = DCTERMS.description
    iri_has_update_query: ClassVar[URIRef] = OCO.hasUpdateQuery

    short_name_to_type_iri: ClassVar[Dict[str, URIRef]] = {
        'se': iri_entity
    }

    def __init__(self, prov_subject: str, g: OCDMProvenance, count: str) -> None:
        super(ProvEntity, self).__init__()
        self.prov_subject = prov_subject
        self.res = URIRef(prov_subject + '/prov/se/' + count)
        self.g: OCDMProvenance = g
        self._create_type(ProvEntity.iri_entity, prov_subject + '/prov/')
        if str(self.res) not in g.res_to_entity:
            g.res_to_entity[str(self.res)] = self
            g.all_entities.add(self.res)