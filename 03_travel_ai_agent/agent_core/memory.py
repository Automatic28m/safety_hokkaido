"""Deprecated import path kept for callers outside node 03.

``02_api_backend/main.py`` still does::

    from agent_core.memory import global_memory
    create_app(..., reset_memory=global_memory.clear)

Node 03 no longer keeps a process-wide shared history. The object exported here
stores nothing; its only operation, ``clear()``, empties every per-conversation
memory in ``context_manager.memory_store`` (the debug reset endpoint's intent).

Owner of node 02: switch the import to
``from agent_core.context_manager import memory_store`` and pass
``reset_memory=memory_store.clear_all``. This module can then be removed.
"""
from __future__ import annotations

from agent_core.context_manager import memory_store

__all__ = ["global_memory"]


class _LegacyResetHandle:
    """Reset-only handle. Holds no conversation data and cannot read or append history."""

    __slots__ = ()

    def clear(self) -> None:
        memory_store.clear_all()


global_memory = _LegacyResetHandle()
