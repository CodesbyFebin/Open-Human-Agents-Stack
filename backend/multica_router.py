# backend/multica_router.py
# Multi-agent CLI gateway for local runtimes

import os
import subprocess
import json
from typing import Dict, Any, List

class MulticaRuntimeGateway:
    def __init__(self, runtime_id: str, sandbox_root: str):
        self.runtime_id = runtime_id
        self.sandbox_root = sandbox_root
        self.supported_clis = {
            "claude": ["claude", "code"],
            "aider": ["aider"],
            "cursor": ["cursor-agent"]
        }

    def detect_local_agent_clis(self) -> List[str]:
        available_tools = []
        for name, binary_args in self.supported_clis.items():
            try:
                result = subprocess.run(
                    ["which", binary_args[0]], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    text=True
                )
                if result.returncode == 0:
                    available_tools.append(name)
            except Exception:
                continue
        return available_tools

    def provision_issue_sandbox(self, issue_id: str, repository_url: str) -> str:
        target_sandbox_path = os.path.abspath(os.path.join(self.sandbox_root, issue_id))
        if not os.path.exists(target_sandbox_path):
            os.makedirs(target_sandbox_path, exist_ok=True)
        return target_sandbox_path

    def dispatch_agent_task(self, agent_cli: str, issue_description: str, workspace_path: str) -> Dict[str, Any]:
        if agent_cli not in self.supported_clis:
            raise ValueError(f"Unmapped runtime command execution string: {agent_cli}")
            
        cmd = self.supported_clis[agent_cli] + ["--message", issue_description]
        
        try:
            process = subprocess.run(
                cmd,
                cwd=workspace_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=1200
            )
            return {
                "exit_code": process.returncode,
                "execution_stdout": process.stdout,
                "execution_stderr": process.stderr
            }
        except subprocess.TimeoutExpired:
            return {"exit_code": -1, "error": "Autonomous script runtime loop exceeded boundaries."}
