package main

import (
	"context"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/redis/go-redis/v9"
)

type MultiTenantRateLimiter struct {
	RedisClient *redis.Client
	Ctx         context.Context
}

func NewMultiTenantRateLimiter(rdb *redis.Client) *MultiTenantRateLimiter {
	return &MultiTenantRateLimiter{
		RedisClient: rdb,
		Ctx:         context.Background(),
	}
}

func (limiter *MultiTenantRateLimiter) PreventTokenOverrunGate(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")

		tenantID, ok := r.Context().Value("tenant_user_identity").(string)
		if !ok || tenantID == "" {
			tenantID = "global-anonymous-pool"
		}

		currentMinuteKey := fmt.Sprintf("rate:%s:%d", tenantID, time.Now().Unix()/60)
		budgetKey := fmt.Sprintf("budget:%s:accumulated", tenantID)

		currentRequests, err := limiter.RedisClient.Incr(limiter.Ctx, currentMinuteKey).Result()
		if err == nil && currentRequests == 1 {
			limiter.RedisClient.Expire(limiter.Ctx, currentMinuteKey, 90*time.Second)
		}

		if currentRequests > 120 {
			w.WriteHeader(http.StatusTooManyRequests)
			_, _ = w.Write([]byte(`{"system_error_message": "Rate Limit Exceeded: Velocity threshold hit for this agent pool."}`))
			return
		}

		accumulatedCostStr, err := limiter.RedisClient.Get(limiter.Ctx, budgetKey).Result()
		if err == nil {
			accumulatedCost, parseErr := strconv.ParseFloat(accumulatedCostStr, 64)
			if parseErr == nil && accumulatedCost >= 50.00 {
				w.WriteHeader(http.StatusPaymentRequired)
				_, _ = w.Write([]byte(`{"system_error_message": "Execution Halted: Credit limits depleted for the assigned workspace."}`))
				return
			}
		}

		w.Header().Set("X-OpenMinds-Pool-Velocity", strconv.FormatInt(currentRequests, 10))
		next.ServeHTTP(w, r)
	}
}
