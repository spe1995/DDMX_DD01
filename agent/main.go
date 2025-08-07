package main

import (
    "bytes"
    "encoding/json"
    "log"
    "net/http"
    "os"
    "time"
)

// RegisterReq 定义注册请求结构
type RegisterReq struct {
    ServerID       string            `json:"server_id"`
    Group          []string          `json:"group"`
    MaxConcurrency map[string]int    `json:"max_concurrency"`
    IP             string            `json:"ip"`
    Timestamp      int64             `json:"timestamp"`
}

// Task 表示一次压测任务
type Task struct {
    Targets      []string `json:"targets"`
    Layer        string   `json:"layer"`
    Concurrency  int      `json:"concurrency"`
    Duration     int      `json:"duration"`
    AttackMethod string   `json:"attack_method"`
    TaskID       string   `json:"task_id"`
}

// register 向管理端注册自身能力
func register(managerURL, serverID string) {
    req := RegisterReq{
        ServerID:       serverID,
        Group:          []string{"L7"},
        MaxConcurrency: map[string]int{"L7": 100},
        IP:             "127.0.0.1",
        Timestamp:      time.Now().Unix(),
    }
    data, _ := json.Marshal(req)
    _, err := http.Post(managerURL+"/api/server/register", "application/json", bytes.NewBuffer(data))
    if err != nil {
        log.Println("register error:", err)
    } else {
        log.Println("registered to manager")
    }
}

func main() {
    managerURL := os.Getenv("MANAGER_URL")
    if managerURL == "" {
        managerURL = "http://localhost:8000"
    }
    serverID := os.Getenv("SERVER_ID")
    if serverID == "" {
        serverID = "agent-1"
    }

    register(managerURL, serverID)

    // 处理来自管理端的任务执行请求
    http.HandleFunc("/run_task", func(w http.ResponseWriter, r *http.Request) {
        var task Task
        if err := json.NewDecoder(r.Body).Decode(&task); err != nil {
            w.WriteHeader(http.StatusBadRequest)
            return
        }
        log.Printf("start task %s: %v\n", task.TaskID, task)
        // 简单模拟并发执行：为每个并发启动一个 goroutine
        for i := 0; i < task.Concurrency; i++ {
            go func(id int) {
                log.Printf("goroutine %d executing target %s\n", id, task.Targets[0])
                time.Sleep(time.Duration(task.Duration) * time.Second)
            }(i)
        }
        w.WriteHeader(http.StatusOK)
    })

    log.Println("agent listening on :8081")
    log.Fatal(http.ListenAndServe(":8081", nil))
}
