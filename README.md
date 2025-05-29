[<img src="https://img.shields.io/badge/powered%20by-OpenCitations-%239931FC?labelColor=2D22DE" />](http://opencitations.net)
[![Run tests](https://github.com/opencitations/rdflib-ocdm/actions/workflows/run_tests.yml/badge.svg)](https://github.com/opencitations/rdflib-ocdm/actions/workflows/run_tests.yml)
![Coverage](https://byob.yarr.is/arcangelo7/badges/opencitations-rdflib-ocdm-coverage-main)
![PyPI](https://img.shields.io/pypi/pyversions/rdflib-ocdm)
[![PyPI version](https://badge.fury.io/py/rdflib-ocdm.svg)](https://badge.fury.io/py/rdflib-ocdm)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/opencitations/rdflib-ocdm)

# rdflib-ocdm

A Python library that extends [RDFLib](https://github.com/RDFLib/rdflib) to support the OpenCitations Provenance Model, providing provenance tracking and change management capabilities for RDF data.

## Overview

`rdflib-ocdm` is designed to be fully compatible with RDFLib while adding specialized functionality for handling provenance information according to the OpenCitations Provenance Model. It provides mechanisms for:

- Tracking provenance information for RDF entities
- Managing entity snapshots to record changes over time
- Handling entity creation, modification, and merging with proper provenance
- Storing and retrieving RDF data with provenance information

This library serves as a retrocompatible extension to RDFLib that adds support for the OpenCitations Provenance Model, particularly focusing on provenance tracking and change management.

While [oc_ocdm](https://github.com/opencitations/oc_ocdm) is a Python interface specifically designed for creating and managing bibliographic data according to the OpenCitations Data Model, `rdflib-ocdm` can be considered a subset of both RDFlib and oc_ocdm. The key advantage of `rdflib-ocdm` is that it allows you to use the OpenCitations provenance model with **any type of data**, not just bibliographic data.

## Key Features

- **Extended Graph Classes**: `OCDMGraph` and `OCDMConjunctiveGraph` that inherit from RDFLib's `Graph` and `ConjunctiveGraph` classes
- **Provenance Tracking**: Automatic generation of provenance information when entities are created or modified
- **Snapshot Management**: Creation and management of snapshot entities to record the state of entities at different points in time
- **Counter Handlers**: Various implementations for managing entity identifiers (in-memory, filesystem, SQLite)
- **Storer**: Utilities for storing RDF data in various formats and endpoints
- **Domain Agnostic**: Unlike oc_ocdm which is specific to bibliographic data, rdflib-ocdm can be used with any type of RDF data

## Installation

```bash
pip install rdflib-ocdm
```

## Usage

### Basic Usage

```python
from rdflib import URIRef, Literal
from rdflib_ocdm.ocdm_graph import OCDMGraph
from rdflib_ocdm.counter_handler.in_memory_counter_handler import InMemoryCounterHandler
from rdflib_ocdm.storer import Storer

# Create a new OCDM graph with a counter handler
counter_handler = InMemoryCounterHandler()
g = OCDMGraph(counter_handler)

# Add triples with provenance tracking
resp_agent = URIRef("https://orcid.org/0000-0002-8420-0696")
primary_source = URIRef("https://api.crossref.org/")
g.add((URIRef("https://example.org/resource"), 
       URIRef("http://purl.org/dc/terms/title"), 
       Literal("Example Resource")),
       resp_agent=resp_agent,
       primary_source=primary_source)

# Generate provenance information
g.generate_provenance()

# Store the graph
storer = Storer(g, output_format="json-ld")
storer.store_graphs_in_file("output.json")
```

### Working with Existing Data

When working with pre-existing RDF data, you need to establish a baseline state from which changes can be tracked. The `preexisting_finished` method serves this critical purpose:

1. It marks a specific point in time as the baseline state of your graph
2. It creates a snapshot of this baseline state for each entity
3. When you later call `generate_provenance()`, the system will calculate the differences (deltas) between the current state and this baseline

This delta calculation is essential for accurate provenance tracking, as it allows the system to record exactly what changed, when it changed, and who made the change.

```python
from rdflib import URIRef, Literal
from rdflib_ocdm.ocdm_graph import OCDMGraph
from rdflib_ocdm.counter_handler.in_memory_counter_handler import InMemoryCounterHandler

# Create a graph and load existing data
g = OCDMGraph(InMemoryCounterHandler())
g.parse("existing_data.ttl", format="turtle")

# Mark the current state as the baseline for delta calculation
# This is crucial for the system to know what's "original" vs. what's "changed"
resp_agent = URIRef("https://orcid.org/0000-0002-8420-0696")
primary_source = URIRef("https://example.org/data-source")
g.preexisting_finished(resp_agent=resp_agent, primary_source=primary_source)

# Now you can make changes to the graph
g.add((URIRef("https://example.org/resource"), 
       URIRef("http://purl.org/dc/terms/description"), 
       Literal("Updated description")),
       resp_agent=resp_agent,
       primary_source=primary_source)

# Generate provenance information that will calculate and record the deltas
# between the baseline state and the current state
g.generate_provenance()

# Get the provenance graphs that contain the delta information
prov_graphs = g.get_provenance_graphs()

## Running Tests

The project includes a comprehensive test suite to ensure functionality and maintain code quality. To run the tests locally:

### Prerequisites

- [Poetry](https://python-poetry.org/) for dependency management
- Docker for running test databases (used by some tests)

### Setup

1. Clone the repository and install dependencies:
   ```bash
   git clone https://github.com/opencitations/rdflib-ocdm.git
   cd rdflib-ocdm
   poetry install --with dev
   ```

2. Start the test databases (if needed):
   ```bash
   # On Linux/macOS
   ./test/start-test-databases.sh
   
   # On Windows
   .\test\start-test-databases.ps1
   ```

### Running Tests

Run the tests with coverage:
```bash
poetry run python -m coverage run --rcfile=test/coverage/.coveragerc 
```

Generate and view the coverage report:
```bash
poetry run coverage report  # Console output
poetry run coverage html    # HTML report (available in htmlcov/ directory)
```

### Cleanup

After running tests, stop the test databases:
```bash
# On Linux/macOS
./test/stop-test-databases.sh

# On Windows
.\test\stop-test-databases.ps1
```

Note: On Linux/macOS, you may need to make the test scripts executable before running them. Use the following command:
```bash
chmod +x test/start-test-databases.sh test/stop-test-databases.sh
```

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project, including commit message conventions and how to trigger different types of releases.

## References

- Persiani, S., Daquino, M., Peroni, S. (2022). A Programming Interface for Creating Data According to the SPAR Ontologies and the OpenCitations Data Model. In: Groth, P., et al. The Semantic Web. ESWC 2022. Lecture Notes in Computer Science, vol 13261. Springer, Cham. [https://doi.org/10.1007/978-3-031-06981-9_18](https://doi.org/10.1007/978-3-031-06981-9_18)

## License

ISC License

## Related Projects

- [oc_ocdm](https://github.com/opencitations/oc_ocdm): A Python library for importing, creating, modifying, and exporting RDF data structures compliant with the OpenCitations Data Model (OCDM v2.0.1). It provides a specialized interface for working with bibliographic data according to the OpenCitations specifications.

- [time-agnostic-library](https://github.com/opencitations/time-agnostic-library): A Python library that enables time-travel queries on RDF datasets compliant with the OpenCitations provenance model. It allows users to query different versions of the data at specific points in time, supporting version materialization and various structured query types across versions and deltas.

- [heritrace](https://github.com/opencitations/heritrace): HERITRACE (Heritage Enhanced Repository Interface for Tracing, Research, Archival Curation, and Engagement) is a semantic editor designed for GLAM professionals (galleries, libraries, archives, museums). It enables non-technical domain experts to enrich and edit metadata with robust semantic capabilities, focusing on user-friendliness, provenance tracking, and change management.
