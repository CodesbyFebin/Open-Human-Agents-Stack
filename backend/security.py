# backend/security.py
# Cryptographic guardrails and path isolation

import os
import hashlib
import hmac
from typing import List, Dict, Any

class CryptographicGuardrail:
    def __init__(self, security_enclave_dsn):
        self.dsn = security_enclave_dsn

    def verify_path_isolation(self, target_path: str, allowed_roots: List[str]) -> bool:
        resolved_target = os.path.abspath(target_path)
        for root in allowed_roots:
            resolved_root = os.path.abspath(root)
            if resolved_target.startswith(resolved_root):
                return True
        return False

    def scan_command_payload(self, execution_string: str, forbidden_patterns: List[str]) -> bool:
        normalized = execution_string.lower().strip()
        for pattern in forbidden_patterns:
            if pattern.lower() in normalized:
                return False
        return True

    def generate_operation_signature(self, private_key: bytes, message_payload: bytes) -> bytes:
        return hmac.new(private_key, message_payload, hashlib.sha256).digest()

    def scrub_outbound_payload(self, raw_payload: str, internal_secrets: List[str]) -> str:
        scrubbed = raw_payload
        for secret in internal_secrets:
            if secret in scrubbed:
                scrubbed = scrubbed.replace(secret, "[OMITTED_SECURITY_CREDENTIAL]")
        return scrubbed
