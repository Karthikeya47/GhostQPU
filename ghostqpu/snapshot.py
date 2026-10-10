"""Calibration snapshots: a Backend's published configuration and properties at one moment.

A snapshot is everything a Forger is allowed to know. It can be saved as JSON and
rebuilt into a simulatable backend the same way IBM's own fake backends are built.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from qiskit.providers import BackendV2
from qiskit_ibm_runtime.fake_provider.fake_backend import FakeBackendV2
from qiskit_ibm_runtime.utils.backend_decoder import (
    decode_backend_configuration,
    properties_from_server_data,
)


def _to_jsonable(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, complex):
        return [obj.real, obj.imag]
    if hasattr(obj, "tolist"):
        return obj.tolist()
    raise TypeError(f"not JSON serializable: {type(obj).__name__}")


def _jsonable_dict(d: dict) -> dict:
    return json.loads(json.dumps(d, default=_to_jsonable))


@dataclass(frozen=True)
class CalibrationSnapshot:
    backend_name: str
    captured_at: str
    configuration: dict
    properties: dict

    @classmethod
    def capture(cls, backend: BackendV2, at: datetime | None = None) -> CalibrationSnapshot:
        """Snapshot `backend` now, or as of `at` when the backend keeps calibration history."""
        if at is None:
            props = backend.properties(refresh=True)
        else:
            try:
                props = backend.properties(datetime=at)
            except TypeError:  # fake backends have no calibration history
                props = backend.properties()
        if props is None:
            raise ValueError(f"{backend.name} published no calibration properties")
        return cls(
            backend_name=backend.name,
            captured_at=(at or datetime.now(UTC)).isoformat(),
            configuration=_jsonable_dict(backend.configuration().to_dict()),
            properties=_jsonable_dict(props.to_dict()),
        )

    @property
    def cycle(self) -> str:
        """Identifies the Calibration cycle this snapshot belongs to."""
        return self.properties["last_update_date"]

    def readout_errors(self, qubit: int) -> tuple[float, float]:
        """(P(read 1 | prepared 0), P(read 0 | prepared 1)) as published for `qubit`."""
        values = {p["name"]: p["value"] for p in self.properties["qubits"][qubit]}
        return values["prob_meas1_prep0"], values["prob_meas0_prep1"]

    def simulator_backend(self) -> BackendV2:
        """A backend whose target and noise come only from this snapshot."""
        return _SnapshotBackend(self)

    def save(self, path: Path) -> None:
        Path(path).write_text(json.dumps(self.__dict__))

    @classmethod
    def load(cls, path: Path) -> CalibrationSnapshot:
        return cls(**json.loads(Path(path).read_text()))


class _SnapshotBackend(FakeBackendV2):
    """FakeBackendV2 fed from a snapshot instead of bundled JSON files."""

    dirname = None
    conf_filename = None
    props_filename = None

    def __init__(self, snapshot: CalibrationSnapshot):
        self._snapshot = snapshot
        self.backend_name = snapshot.backend_name
        super().__init__()

    def _get_conf_dict_from_json(self) -> dict:
        conf = copy.deepcopy(self._snapshot.configuration)
        decode_backend_configuration(conf)
        return conf

    def _set_props_dict_from_json(self) -> None:
        props = copy.deepcopy(self._snapshot.properties)
        properties_from_server_data(props)
        self._props_dict = props
