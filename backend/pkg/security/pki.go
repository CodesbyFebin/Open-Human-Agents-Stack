package security

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"fmt"
	"math/big"
	"net"
	"time"
)

type GeneratedKeypairBundle struct {
	CertificatePEM []byte
	PrivateKeyPEM  []byte
}

func SetupAuthorityAnchor() (*rsa.PrivateKey, *x509.Certificate, *GeneratedKeypairBundle, error) {
	caPrivateKey, err := rsa.GenerateKey(rand.Reader, 4096)
	if err != nil {
		return nil, nil, nil, fmt.Errorf("failed to generate 4096-bit RSA keys: %w", err)
	}
	serialNumberLimit := new(big.Int).Lsh(big.NewInt(1), 128)
	serialNumber, err := rand.Int(rand.Reader, serialNumberLimit)
	if err != nil {
		return nil, nil, nil, fmt.Errorf("failed to generate serial token matrix: %w", err)
	}
	caTemplate := &x509.Certificate{
		SerialNumber: serialNumber,
		Subject: pkix.Name{
			Organization: []string{"OpenMinds Autonomous Fleet System"},
			CommonName:   "OpenMinds Root CA v2",
			Country:      []string{"IN"},
			Province:     []string{"Kerala"},
			Locality:     []string{"Ernakulam"},
		},
		NotBefore:             time.Now(),
		NotAfter:              time.Now().AddDate(10, 0, 0),
		IsCA:                  true,
		ExtKeyUsage:           []x509.ExtKeyUsage{x509.ExtKeyUsageClientAuth, x509.ExtKeyUsageServerAuth},
		KeyUsage:              x509.KeyUsageDigitalSignature | x509.KeyUsageCertSign,
		BasicConstraintsValid: true,
	}
	caBytes, err := x509.CreateCertificate(rand.Reader, caTemplate, caTemplate, &caPrivateKey.PublicKey, caPrivateKey)
	if err != nil {
		return nil, nil, nil, fmt.Errorf("failed to compile CA binary envelope: %w", err)
	}
	caCertPEM := pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: caBytes})
	caKeyPEM := pem.EncodeToMemory(&pem.Block{Type: "RSA PRIVATE KEY", Bytes: x509.MarshalPKCS1PrivateKey(caPrivateKey)})
	return caPrivateKey, caTemplate, &GeneratedKeypairBundle{CertificatePEM: caCertPEM, PrivateKeyPEM: caKeyPEM}, nil
}

func SignComputeNodeCertificate(caKey *rsa.PrivateKey, caCert *x509.Certificate, runnerID string, targetIP string) (*GeneratedKeypairBundle, error) {
	nodeKey, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize runner RSA key: %w", err)
	}
	serialNumberLimit := new(big.Int).Lsh(big.NewInt(1), 128)
	serialNumber, err := rand.Int(rand.Reader, serialNumberLimit)
	if err != nil {
		return nil, fmt.Errorf("failed to generate serial token data: %w", err)
	}
	nodeTemplate := &x509.Certificate{
		SerialNumber: serialNumber,
		Subject: pkix.Name{
			Organization: []string{"OpenMinds Compute Runner Array"},
			CommonName:   fmt.Sprintf("runner-%s.openminds.internal", runnerID),
		},
		NotBefore:   time.Now(),
		NotAfter:    time.Now().AddDate(2, 0, 0),
		KeyUsage:    x509.KeyUsageDigitalSignature | x509.KeyUsageKeyEncipherment,
		ExtKeyUsage: []x509.ExtKeyUsage{x509.ExtKeyUsageClientAuth, x509.ExtKeyUsageServerAuth},
	}
	if ip := net.ParseIP(targetIP); ip != nil {
		nodeTemplate.IPAddresses = append(nodeTemplate.IPAddresses, ip)
	}
	certBytes, err := x509.CreateCertificate(rand.Reader, nodeTemplate, caCert, &nodeKey.PublicKey, caKey)
	if err != nil {
		return nil, fmt.Errorf("failed to sign endpoint node tracking certificate: %w", err)
	}
	certPEM := pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: certBytes})
	keyPEM := pem.EncodeToMemory(&pem.Block{Type: "RSA PRIVATE KEY", Bytes: x509.MarshalPKCS1PrivateKey(nodeKey)})
	return &GeneratedKeypairBundle{CertificatePEM: certPEM, PrivateKeyPEM: keyPEM}, nil
}
