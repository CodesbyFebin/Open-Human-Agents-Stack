"""Fail-closed PKI material checks."""
from backend.security.pki_status import crypto_status


def test_missing_certificates_never_claim_mtls(monkeypatch, tmp_path):
    monkeypatch.setenv("MTLS_CA_CERT_PATH", str(tmp_path / "missing-ca.crt"))
    monkeypatch.setenv("MTLS_SERVER_CERT_PATH", str(tmp_path / "missing-server.crt"))
    monkeypatch.setenv("MTLS_SERVER_KEY_PATH", str(tmp_path / "missing-server.key"))
    result = crypto_status()
    assert result["material_loadable"] is False
    assert result["mutual_tls_enforced"] is False
