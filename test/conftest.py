# SPDX-FileCopyrightText: 2025 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# SPDX-License-Identifier: ISC

import os
import random
import subprocess
import time

import fakeredis
import pytest
from SPARQLWrapper import JSON, POST, SPARQLWrapper

VIRTUOSO_IMAGE = "openlink/virtuoso-opensource-7@sha256:c08d54120b8085234f8244951232553428e235543412e41d75705736a3026f1b"
DATASET_CONTAINER = "rdflib_ocdm_dataset_db"
PROV_CONTAINER = "rdflib_ocdm_provenance_db"
NETWORK = "virtuoso-net"


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, capture_output=True, text=True)


@pytest.fixture(scope="session")
def virtuoso_databases():
    _run(["docker", "stop", DATASET_CONTAINER, PROV_CONTAINER])
    _run(["docker", "rm", DATASET_CONTAINER, PROV_CONTAINER])
    _run(["docker", "network", "create", NETWORK])

    os.makedirs("test/dataset_db", exist_ok=True)
    os.makedirs("test/prov_db", exist_ok=True)

    for name, host_port, host_isql, vol_dir in [
        (DATASET_CONTAINER, "8890", "1111", "test/dataset_db"),
        (PROV_CONTAINER, "8891", "1112", "test/prov_db"),
    ]:
        subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                name,
                "--network",
                NETWORK,
                "-p",
                f"{host_port}:8890",
                "-p",
                f"{host_isql}:1111",
                "-e",
                "DBA_PASSWORD=dba",
                "-e",
                "SPARQL_UPDATE=true",
                "-v",
                f"{os.path.abspath(vol_dir)}:/database",
                VIRTUOSO_IMAGE,
            ],
            check=True,
        )

    time.sleep(15)

    for container in [DATASET_CONTAINER, PROV_CONTAINER]:
        isql = "/opt/virtuoso-opensource/bin/isql"
        subprocess.run(
            [
                "docker",
                "exec",
                container,
                isql,
                "-U",
                "dba",
                "-P",
                "dba",
                "exec=DB.DBA.RDF_DEFAULT_USER_PERMS_SET ('nobody', 7);",
            ],
            check=True,
        )
        subprocess.run(
            [
                "docker",
                "exec",
                container,
                isql,
                "-U",
                "dba",
                "-P",
                "dba",
                "exec=DB.DBA.USER_GRANT_ROLE ('SPARQL', 'SPARQL_UPDATE');",
            ],
            check=True,
        )

    yield

    _run(["docker", "stop", DATASET_CONTAINER, PROV_CONTAINER])
    _run(["docker", "rm", DATASET_CONTAINER, PROV_CONTAINER])
    _run(["docker", "network", "rm", NETWORK])


@pytest.fixture
def subject() -> str:
    return "https://w3id.org/oc/meta/br/0605"


@pytest.fixture
def cur_time() -> float:
    return 1607375859.846196


@pytest.fixture
def cur_time_str() -> str:
    return "2020-12-07T21:17:34+00:00"


@pytest.fixture
def reset_server():
    def _reset():
        subprocess.run(
            [
                "docker",
                "exec",
                DATASET_CONTAINER,
                "/opt/virtuoso-opensource/bin/isql",
                "-U",
                "dba",
                "-P",
                "dba",
                "exec=RDF_GLOBAL_RESET();",
            ],
            capture_output=True,
            text=True,
        )

    return _reset


@pytest.fixture
def sparql_wrapper(virtuoso_databases, reset_server):
    reset_server()
    ts = SPARQLWrapper("http://localhost:8890/sparql")
    ts.setMethod(POST)
    ts.setReturnFormat(JSON)

    max_retries = 5
    base_wait_time = 1
    for attempt in range(max_retries + 1):
        try:
            ts.query()
            break
        except Exception as e:
            if attempt < max_retries:
                wait_time = (base_wait_time * (2**attempt)) + (random.random() * 0.5)
                time.sleep(wait_time)
            else:
                raise Exception(
                    f"Failed to connect to triplestore after {max_retries} attempts: {e}"
                )
    return ts


@pytest.fixture(scope="class")
def fake_redis():
    return fakeredis.FakeStrictRedis()
