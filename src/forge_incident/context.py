from __future__ import annotations

from pathlib import Path

from forge_context import ContextEngine
from forge_context.config import Settings
from forge_context.factory import make_backend, make_embedder
from forge_context.indexer import RepositoryIndexer


class OperationalContext:
    """Build and retrieve grounded repository/runbook/postmortem context."""

    def __init__(self) -> None:
        settings = Settings.from_env()
        embedder = make_embedder(settings)
        backend = make_backend(settings, dimensions=embedder.dimensions)
        self.settings = settings
        self.backend = backend
        self.embedder = embedder
        self.engine = ContextEngine(backend, embedder)

    def pack(self, root: Path, question: str) -> dict:
        root = root.resolve()
        if self.backend.count() == 0:
            RepositoryIndexer(self.backend, self.settings, self.embedder).sync(root)
        return self.engine.context_pack(root, question, limit=8, decision_limit=16).model_dump(mode="json")
