# [2.0.0](https://github.com/opencitations/rdflib-ocdm/compare/v1.0.7...v2.0.0) (2026-05-30)


* build!: drop Python 3.9 support ([916ddb0](https://github.com/opencitations/rdflib-ocdm/commit/916ddb0cc559b09ed760a1dc17b1d3759285bf27))


### Bug Fixes

* add proper resource cleanup for SQLite database connections in SqliteCounterHandler and update rdflib to 7.4.0 ([0656b40](https://github.com/opencitations/rdflib-ocdm/commit/0656b40d38347088964d260ef4e88ffb8e5d5085))
* enforce ruff linting [release] ([36d72e5](https://github.com/opencitations/rdflib-ocdm/commit/36d72e5d3a10cc0b32ec471463cff01d5283ec58))
* upgrade oc-ocdm from 9.x to 11.x [release] ([0bdcd83](https://github.com/opencitations/rdflib-ocdm/commit/0bdcd83a74164ee401cbcaa7d1716abede9d226f))


### BREAKING CHANGES

* projects running on Python 3.9 must upgrade
to Python 3.10 or later.

<!--
SPDX-FileCopyrightText: 2025 Arcangelo Massari <arcangelo.massari@unibo.it>

SPDX-License-Identifier: ISC
-->

## [1.0.7](https://github.com/opencitations/rdflib-ocdm/compare/v1.0.6...v1.0.7) (2025-11-01)


### Bug Fixes

* Store graph_iri in entity_index during add/parse operations instead of ([144cc3c](https://github.com/opencitations/rdflib-ocdm/commit/144cc3cf57540106dbd13e29afa903b5aa6e64a7))

## [1.0.6](https://github.com/opencitations/rdflib-ocdm/compare/v1.0.5...v1.0.6) (2025-11-01)


### Bug Fixes

* fix bug in storer.py where ValueError message referenced ([520b472](https://github.com/opencitations/rdflib-ocdm/commit/520b472b11d6ff5f82817afb047e71ece8e1f3c7))

## [1.0.5](https://github.com/opencitations/rdflib-ocdm/compare/v1.0.4...v1.0.5) (2025-10-29)


### Bug Fixes

* remove extra space [release] ([6b0ea31](https://github.com/opencitations/rdflib-ocdm/commit/6b0ea31a5e1beed3c13022ba35d30fddf1c9dfec))

## [1.0.4](https://github.com/opencitations/rdflib-ocdm/compare/v1.0.3...v1.0.4) (2025-05-30)


### Bug Fixes

* **deps:** update dependencies and improve database management scripts ([e67b7e0](https://github.com/opencitations/rdflib-ocdm/commit/e67b7e015e4da360b65550a3a905d8e85e1acd0d))

## [1.0.3](https://github.com/opencitations/rdflib-ocdm/compare/v1.0.2...v1.0.3) (2025-05-29)


### Bug Fixes

* [release] ([cba8dbb](https://github.com/opencitations/rdflib-ocdm/commit/cba8dbb7d83d66c9abdef33dd57ebf24fcd07212))

## [1.0.2](https://github.com/opencitations/rdflib-ocdm/compare/v1.0.1...v1.0.2) (2025-03-13)


### Bug Fixes

* [release] Literal instantiation ([f6300f3](https://github.com/opencitations/rdflib-ocdm/commit/f6300f3470e1433aa2edd2a13af3268125c0c3d1))

## [1.0.1](https://github.com/opencitations/rdflib-ocdm/compare/v1.0.0...v1.0.1) (2025-02-28)


### Bug Fixes

* add compatibility with Time Agnostic Library 4.6.14 ([98f1cc8](https://github.com/opencitations/rdflib-ocdm/commit/98f1cc8340c9863c1247f0b76238bf260f8c8d93))

# 1.0.0 (2025-02-28)


### Bug Fixes

* [release] Fixed an issue where there was no retry mechanism and incremental backoff when executing queries. ([14b4715](https://github.com/opencitations/rdflib-ocdm/commit/14b4715d61eec30b43164778b5f98dbd34e5cb04))

# Changelog

All notable changes to this project will be documented in this file. This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
