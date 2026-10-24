package services

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"sync"

	"github.com/redis/go-redis/v9"
)

type RedisEventMeshBroker struct {
	Client     *redis.Client
	Ctx        context.Context
	CancelFunc context.CancelFunc
	WaitGroups sync.WaitGroup
}

type MeshEventPayload struct {
	EventUUID      string                 `json:"event_uuid"`
	TimestampEpoch int64                  `json:"timestamp_epoch"`
	SourceEngine   string                 `json:"source_engine"`
	EventType      string                 `json:"event_type"`
	PayloadData    map[string]interface{} `json:"payload_data"`
}

func NewRedisEventMeshBroker(redisAddress string, redisPassword string, dbIndex int) *RedisEventMeshBroker {
	ctx, cancel := context.WithCancel(context.Background())
	rdb := redis.NewClient(&redis.Options{
		Addr:     redisAddress,
		Password: redisPassword,
		DB:       dbIndex,
		PoolSize: 50,
	})
	return &RedisEventMeshBroker{
		Client:     rdb,
		Ctx:        ctx,
		CancelFunc: cancel,
	}
}

func (broker *RedisEventMeshBroker) BroadcastMeshEvent(channelName string, event *MeshEventPayload) error {
	jsonData, err := json.Marshal(event)
	if err != nil {
		return fmt.Errorf("failed to serialize event telemetry payload: %w", err)
	}
	err = broker.Client.Publish(broker.Ctx, channelName, jsonData).Err()
	if err != nil {
		return fmt.Errorf("redis event mesh publish transaction rejected: %w", err)
	}
	return nil
}

func (broker *RedisEventMeshBroker) InitializePipelineListener(channelName string, eventRouterFunc func(event MeshEventPayload)) {
	broker.WaitGroups.Add(1)
	go func() {
		defer broker.WaitGroups.Done()
		pubsub := broker.Client.Subscribe(broker.Ctx, channelName)
		defer pubsub.Close()
		ch := pubsub.Channel()
		log.Printf("[EVENT_MESH] High-throughput listener listening on cluster channel: %s", channelName)
		for {
			select {
			case <-broker.Ctx.Done():
				log.Printf("[EVENT_MESH] Gracefully shutting down channel interface: %s", channelName)
				return
			case msg, ok := <-ch:
				if !ok {
					return
				}
				var event MeshEventPayload
				if err := json.Unmarshal([]byte(msg.Payload), &event); err != nil {
					log.Printf("[ERROR] Dropping unparsable message signature block: %v", err)
					continue
				}
				eventRouterFunc(event)
			}
		}
	}()
}

func (broker *RedisEventMeshBroker) CloseMeshBroker() {
	broker.CancelFunc()
	broker.Client.Close()
	broker.WaitGroups.Wait()
	log.Println("[EVENT_MESH] Operational cleanup sequence complete for internal event bus ring.")
}
