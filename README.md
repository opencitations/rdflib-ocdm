<!--
SPDX-FileCopyrightText: 2023-2026 Arcangelo Massari <arcangelo.massari@unibo.it>

SPDX-License-Identifier: CC-BY-4.0
-->

[<img src="https://img.shields.io/badge/powered%20by-OpenCitations-%239931FC?labelColor=2D22DE" />](http://opencitations.net)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rdflib-ocdm?logo=python&logoColor=white)](https://pypi.org/project/rdflib-ocdm/)
[![Run tests](https://github.com/opencitations/rdflib-ocdm/actions/workflows/run_tests.yml/badge.svg)](https://github.com/opencitations/rdflib-ocdm/actions/workflows/run_tests.yml)
[![Coverage](https://opencitations.github.io/rdflib-ocdm/coverage-badge.svg)](https://opencitations.github.io/rdflib-ocdm/)
[![Pyright](https://github.com/opencitations/rdflib-ocdm/actions/workflows/pyright.yml/badge.svg)](https://github.com/opencitations/rdflib-ocdm/actions/workflows/pyright.yml)
[![Ruff](https://github.com/opencitations/rdflib-ocdm/actions/workflows/ruff.yml/badge.svg)](https://github.com/opencitations/rdflib-ocdm/actions/workflows/ruff.yml)
[![REUSE status](https://api.reuse.software/badge/github.com/opencitations/rdflib-ocdm)](https://api.reuse.software/info/github.com/opencitations/rdflib-ocdm)
[![PyPI version](https://img.shields.io/pypi/v/rdflib-ocdm?logo=pypi&logoColor=white)](https://pypi.org/project/rdflib-ocdm/)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/opencitations/rdflib-ocdm)

# rdflib-ocdm

rdflib-ocdm extends [RDFLib](https://github.com/RDFLib/rdflib) with provenance tracking based on the [OpenCitations Provenance Model](https://opencitations.net/model).

Its two main classes, `OCDMGraph` and `OCDMDataset`, inherit from RDFLib's `Graph` and `Dataset` respectively. The OCDM layer adds methods for recording who changed what and when.

Calling `generate_provenance()` creates timestamped provenance snapshots for entities whose tracked state changed. Snapshot sequence numbers are managed through counter handler backends (in-memory, filesystem, SQLite, Redis). Unlike [oc_ocdm](https://github.com/opencitations/oc_ocdm), which targets bibliographic data specifically, rdflib-ocdm is domain-agnostic.

## Installation

```bash
pip install rdflib-ocdm
```

## Usage

### Basic usage

```python
from rdflib import Literal, URIRef
from rdflib_ocdm.counter_handler.in_memory_counter_handler import InMemoryCounterHandler
from rdflib_ocdm.ocdm_graph import OCDMGraph

counter_handler = InMemoryCounterHandler()
g = OCDMGraph(counter_handler)

resp_agent = URIRef("https://orcid.org/0000-0002-8420-0696")
primary_source = URIRef("https://api.crossref.org/")
g.add(
    (
        URIRef("https://example.org/resource"),
        URIRef("http://purl.org/dc/terms/title"),
        Literal("Example Resource"),
    ),
    resp_agent=resp_agent,
    primary_source=primary_source,
)

g.generate_provenance()

print(g.serialize(format="turtle"))

prov = g.get_provenance_graphs()
print(prov.serialize(format="nquads"))
```

### Working with existing data

When working with pre-existing RDF data, you need to establish a baseline from which changes can be tracked. `preexisting_finished()` marks the current graph state as that baseline and creates an initial provenance snapshot for each entity. When you later call `generate_provenance()`, the system computes the delta between the baseline and the current state, recording exactly what changed, when, and by whom. Without calling `preexisting_finished()`, all triples are treated as newly created.

```python
from rdflib import Literal, URIRef
from rdflib_ocdm.counter_handler.in_memory_counter_handler import InMemoryCounterHandler
from rdflib_ocdm.ocdm_graph import OCDMGraph

g = OCDMGraph(InMemoryCounterHandler())
g.parse("existing_data.ttl", format="turtle")

resp_agent = URIRef("https://orcid.org/0000-0002-8420-0696")
primary_source = URIRef("https://example.org/data-source")
g.preexisting_finished(resp_agent=resp_agent, primary_source=primary_source)

g.add(
    (
        URIRef("https://example.org/resource"),
        URIRef("http://purl.org/dc/terms/description"),
        Literal("Updated description"),
    ),
    resp_agent=resp_agent,
    primary_source=primary_source,
)

g.generate_provenance()

prov_graphs = g.get_provenance_graphs()
```

For working with SPARQL endpoints, `Reader.import_entities_from_triplestore()` imports entities from a triplestore into an `OCDMGraph` or `OCDMDataset`, while `Storer.upload_all()` pushes graph changes back as batched update queries.

## Running tests

### Prerequisites

- [UV](https://docs.astral.sh/uv/) for dependency management
- Docker for running test databases (storer tests start/stop Virtuoso containers automatically via pytest fixtures)

### Setup

```bash
git clone https://github.com/opencitations/rdflib-ocdm.git
cd rdflib-ocdm
uv sync --locked --all-extras --dev
```

### Running tests

```bash
uv run pytest test/ -v
```

Run with coverage:

```bash
uv run coverage run
uv run coverage report
uv run coverage html
```

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project, including commit message conventions and how to trigger different types of releases.

## References

- Persiani, S., Daquino, M., Peroni, S. (2022). A Programming Interface for Creating Data According to the SPAR Ontologies and the OpenCitations Data Model. In: Groth, P., et al. The Semantic Web. ESWC 2022. Lecture Notes in Computer Science, vol 13261. Springer, Cham. [https://doi.org/10.1007/978-3-031-06981-9_18](https://doi.org/10.1007/978-3-031-06981-9_18)

## License

ISC License

## Related projects

- [oc_ocdm](https://github.com/opencitations/oc_ocdm): a Python library for creating and managing bibliographic RDF data according to the OpenCitations Data Model.

- [time-agnostic-library](https://github.com/opencitations/time-agnostic-library): a Python library for time-travel queries over RDF datasets that follow the OpenCitations provenance model.

- [heritrace](https://github.com/opencitations/heritrace): an editor for RDF data, with built-in provenance and change tracking.
