"""Pydantic schemas for VEOS model signal parsing results."""

from __future__ import annotations

from pydantic import BaseModel, Field


class VeosSignal(BaseModel):
    """A single VEOS signal or port."""

    path: str = Field()
    data_type: str = Field()


class VeosSignalConnection(BaseModel):
    """A connection between an output signal and an input signal."""

    in_signal_reference: str = Field(serialization_alias="InSignalReference")
    out_signal_reference: str = Field(serialization_alias="OutSignalReference")


class VeosSignalSummary(BaseModel):
    """Flattened summary of VEOS signals and their connections."""

    in_signals: list[VeosSignal] = Field(serialization_alias="InSignals")
    out_signals: list[VeosSignal] = Field(serialization_alias="OutSignals")
    signal_connections: list[VeosSignalConnection] = Field(
        serialization_alias="SignalConnections"
    )
