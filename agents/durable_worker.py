"""Durable Coder Agent — structured output, checkpointable."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

class CodingTaskOutput(BaseModel):
    summary: str = ""
    files_modified: list[str] = Field(default_factory=list)
    diff: str = ""
    tests_passed: bool = False
    confidence: float = 0.0

class DurableCoderAgent:
    def __init__(self, workspace: str = "/tmp/openminds/worktrees"):
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self._checkpoint = self.workspace / ".checkpoint.json"

    async def run(self, task: str) -> CodingTaskOutput:
        return CodingTaskOutput(
            summary=f"Recorded task: {task[:80]}",
            files_modified=[],
            diff="",
            tests_passed=False,
            confidence=0.0,
        )

    def checkpoint(self, state: dict):
        self._checkpoint.write_text(json.dumps(state))

    def load_checkpoint(self) -> Optional[dict]:
        if self._checkpoint.exists():
            return json.loads(self._checkpoint.read_text())
        return None
