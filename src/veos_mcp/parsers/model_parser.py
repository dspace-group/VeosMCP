"""Signal summary extraction logic for VEOS model inspection."""

import json
from typing import Any

from veos_mcp.models.signal_summary import (
    VeosSignal,
    VeosSignalConnection,
    VeosSignalSummary,
)


def extract_signal_summary(stdout: str) -> VeosSignalSummary:
    """Flatten VEOS model JSON output into MCP-facing signal summary data."""
    root = json.loads(stdout)
    in_signals: dict[str, VeosSignal] = {}
    out_signals: dict[str, VeosSignal] = {}
    signal_connections: list[VeosSignalConnection] = []

    for vpu in root.get("Vpus", []):
        _collect_port_group_signals(vpu, in_signals, out_signals)

    for communication_package in root.get("CommunicationPackages", []):
        for connection in communication_package.get("SignalConnections", []):
            in_signal = _try_get_nested_string(connection, "InSignalReference", "ShortPath")
            out_signal = _try_get_nested_string(connection, "OutSignalReference", "ShortPath")
            if not in_signal or not out_signal:
                continue
            signal_connections.append(VeosSignalConnection(in_signal_reference=in_signal, out_signal_reference=out_signal))

    signal_connections.sort(key=lambda connection: (connection.in_signal_reference, connection.out_signal_reference))
    return VeosSignalSummary(
        in_signals=[in_signals[path] for path in sorted(in_signals)],
        out_signals=[out_signals[path] for path in sorted(out_signals)],
        signal_connections=signal_connections,
    )


def _collect_port_group_signals(
    container: dict[str, Any],
    in_signals: dict[str, VeosSignal],
    out_signals: dict[str, VeosSignal],
) -> None:
    for port in container.get("Ports", []):
        _collect_signal_paths(port, in_signals, out_signals)

    for port_group in container.get("PortGroups", []):
        _collect_port_group_signals(port_group, in_signals, out_signals)


def _collect_signal_paths(
    container: dict[str, Any],
    in_signals: dict[str, VeosSignal],
    out_signals: dict[str, VeosSignal],
) -> None:
    _collect_signal_array(container, "InSignals", in_signals)
    _collect_signal_array(container, "OutSignals", out_signals)

    for signal_group in container.get("SignalGroups", []):
        _collect_signal_paths(signal_group, in_signals, out_signals)


def _collect_signal_array(
    container: dict[str, Any],
    property_name: str,
    output: dict[str, VeosSignal],
) -> None:
    for signal in container.get(property_name, []):
        short_element_path = _get_required_string(signal, "ShortElementPath")
        output[short_element_path] = VeosSignal(
            path=short_element_path,
            data_type=_get_required_string(signal, "DataType"),
        )


def _try_get_nested_string(
    element: dict[str, Any],
    object_property_name: str,
    value_property_name: str,
) -> str | None:
    nested_element = element.get(object_property_name)
    if not isinstance(nested_element, dict):
        return None
    property_value = nested_element.get(value_property_name)
    return property_value if isinstance(property_value, str) else None


def _get_required_string(element: dict[str, Any], property_name: str) -> str:
    property_value = element.get(property_name)
    if not isinstance(property_value, str):
        raise ValueError(f"Required property '{property_name}' is missing or is not a string.")
    return property_value
