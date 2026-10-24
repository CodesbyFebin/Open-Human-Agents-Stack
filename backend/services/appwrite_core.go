package services

import (
	"bytes"
	"context"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"time"
)

type AppwriteClient struct {
	Endpoint   string
	ProjectID  string
	APIKey     string
	HTTPClient *http.Client
}

type EphemeralUserSession struct {
	SessionID string `json:"$id"`
	UserID    string `json:"userId"`
	Expire    string `json:"expire"`
	Provider  string `json:"provider"`
	IsActive  bool   `json:"active"`
}

func NewAppwriteClient(endpoint, projectId, apiKey string) *AppwriteClient {
	return &AppwriteClient{
		Endpoint:  endpoint,
		ProjectID: projectId,
		APIKey:    apiKey,
		HTTPClient: &http.Client{
			Timeout: 15 * time.Second,
			Transport: &http.Transport{
				TLSClientConfig: &tls.Config{InsecureSkipVerify: false},
			},
		},
	}
}

func (c *AppwriteClient) ValidateTenantSession(ctx context.Context, sessionToken string) (*EphemeralUserSession, error) {
	reqUrl := fmt.Sprintf("%s/account/sessions/current", c.Endpoint)
	req, err := http.NewRequestWithContext(ctx, "GET", reqUrl, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize auth request context: %w", err)
	}
	req.Header.Set("X-Appwrite-Project", c.ProjectID)
	req.Header.Set("X-Appwrite-JWT", sessionToken)
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("appwrite handshake validation loop failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("session rejected by auth tier with structural status code: %d", resp.StatusCode)
	}

	var session EphemeralUserSession
	if err := json.NewDecoder(resp.Body).Decode(&session); err != nil {
		return nil, fmt.Errorf("failed to unmarshal current session payload metrics: %w", err)
	}
	return &session, nil
}

func (c *AppwriteClient) UploadAgentArtifact(ctx context.Context, bucketID, fileID string, fileName string, fileContent []byte) (string, error) {
	reqUrl := fmt.Sprintf("%s/storage/buckets/%s/files", c.Endpoint, bucketID)
	bodyBuf := &bytes.Buffer{}
	bodyWriter := multipart.NewWriter(bodyBuf)

	fileWriter, err := bodyWriter.CreateFormFile("file", fileName)
	if err != nil {
		return "", fmt.Errorf("failed to allocate form file memory buffer payload: %w", err)
	}
	if _, err = io.Copy(fileWriter, bytes.NewReader(fileContent)); err != nil {
		return "", fmt.Errorf("failed to copy binary sequence array matrix: %w", err)
	}
	_ = bodyWriter.WriteField("fileId", fileID)
	if err = bodyWriter.Close(); err != nil {
		return "", fmt.Errorf("failed to finalize multipart boundary compilation: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, "POST", reqUrl, bodyBuf)
	if err != nil {
		return "", fmt.Errorf("failed to map raw HTTP stream: %w", err)
	}
	req.Header.Set("X-Appwrite-Project", c.ProjectID)
	req.Header.Set("X-Appwrite-Key", c.APIKey)
	req.Header.Set("Content-Type", bodyWriter.FormDataContentType())

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return "", fmt.Errorf("artifact transport pipe failed structurally: %w", err)
	}
	defer resp.Body.Close()

	respBytes, _ := io.ReadAll(resp.Body)
	if resp.StatusCode != http.StatusCreated && resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("appwrite vault upload rejected: %s", string(respBytes))
	}

	var responseMap map[string]interface{}
	_ = json.Unmarshal(respBytes, &responseMap)
	if createdID, ok := responseMap["$id"].(string); ok {
		return createdID, nil
	}
	return fileID, nil
}
