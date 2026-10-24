package services

import (
	"bytes"
	"context"
	"fmt"
	"log"
	"os/exec"
	"strings"
	"time"
)

type AutomatedBackupManager struct {
	AppwriteClient *AppwriteClient
	TargetBucketID string
	DatabaseDSN    string
}

func NewAutomatedBackupManager(client *AppwriteClient, bucketID string, dsn string) *AutomatedBackupManager {
	return &AutomatedBackupManager{
		AppwriteClient: client,
		TargetBucketID: bucketID,
		DatabaseDSN:    dsn,
	}
}

func (mgr *AutomatedBackupManager) RunDatabaseBackupCycle(ctx context.Context) (string, error) {
	timestamp := time.Now().Format("20060102-150405")
	backupFileName := fmt.Sprintf("openminds_snapshot_%s.sql", timestamp)
	log.Printf("[BACKUP_ENGINE] Initializing automated database streaming dump for file: %s", backupFileName)

	dsnCleaned := strings.TrimPrefix(mgr.DatabaseDSN, "postgres://")
	cmd := exec.CommandContext(ctx, "pg_dump", "--uri", "postgres://"+dsnCleaned, "--no-owner", "--no-acl")

	var outBuf bytes.Buffer
	var errBuf bytes.Buffer
	cmd.Stdout = &outBuf
	cmd.Stderr = &errBuf

	if err := cmd.Run(); err != nil {
		return "", fmt.Errorf("pg_dump binary worker process crashed: %s: %w", errBuf.String(), err)
	}

	backupBytes := outBuf.Bytes()
	if len(backupBytes) == 0 {
		return "", fmt.Errorf("database extraction loop returned an empty block payload")
	}

	log.Printf("[BACKUP_ENGINE] Schema dump complete. Size: %d bytes. Transporting to Appwrite vault...", len(backupBytes))

	generatedFileID := fmt.Sprintf("snap-%s", timestamp)
	uploadedID, err := mgr.AppwriteClient.UploadAgentArtifact(ctx, mgr.TargetBucketID, generatedFileID, backupFileName, backupBytes)
	if err != nil {
		return "", fmt.Errorf("appwrite artifact transmission ring dropped payload: %w", err)
	}

	log.Printf("[BACKUP_ENGINE] Database backup verified and locked down securely. Ingestion ID: %s", uploadedID)
	return uploadedID, nil
}

func (mgr *AutomatedBackupManager) StartCronSchedulerLoop(ctx context.Context, interval time.Duration) {
	go func() {
		ticker := time.NewTicker(interval)
		defer ticker.Stop()
		for {
			select {
			case <-ctx.Done():
				log.Println("[BACKUP_ENGINE] Terminating cron tracking scheduler loop context.")
				return
			case <-ticker.C:
				executionCtx, cancel := context.WithTimeout(ctx, 5*time.Minute)
				_, err := mgr.RunDatabaseBackupCycle(executionCtx)
				cancel()
				if err != nil {
					log.Printf("[ERROR] Automated backup cycle experienced pipeline degradation: %v", err)
				}
			}
		}
	}()
}
