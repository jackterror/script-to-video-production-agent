from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class ProviderCapability:
    name: str
    available: bool
    paid: bool
    manual_only: bool
    tested: bool
    notes: str


def manual_provider() -> ProviderCapability:
    return ProviderCapability(
        name="manual",
        available=True,
        paid=False,
        manual_only=True,
        tested=True,
        notes="Manual export works without any external service.",
    )


def detect_higgsfield() -> ProviderCapability:
    configured = bool(os.getenv("HIGGSFIELD_MCP_URL") or os.getenv("HIGGSFIELD_MCP_ENDPOINT"))
    return ProviderCapability(
        name="higgsfield",
        available=configured,
        paid=True,
        manual_only=not configured,
        tested=False,
        notes=(
            "Runtime detection checks explicit environment configuration only. "
            "This package does not assume callable MCP tool names or claim tested integration without evidence."
        ),
    )


def all_capabilities() -> list[ProviderCapability]:
    return [manual_provider(), detect_higgsfield()]
