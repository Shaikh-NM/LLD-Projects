
from abc import ABC, abstractmethod
from enum import Enum, IntEnum
import heapq
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Callable, Any


# ==========================================
# 1. DOMAIN MODELS & ENUMS
# ==========================================

class TaskPriority(IntEnum):
    """Lower integer represents higher execution priority."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class TaskStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"


class Task:
    """Represents a schedulable, executable unit of work."""
    def __init__(
        self,
        task_id: str,
        priority: TaskPriority,
        executable_fn: Callable[[], Any],
        delay_seconds: float = 0.0,
        max_retries: int = 2
    ):
        self.task_id: str = task_id
        self.priority: TaskPriority = priority
        self.executable_fn: Callable[[], Any] = executable_fn
        self.scheduled_time: float = time.time() + delay_seconds
        self.max_retries: int = max_retries
        self.retry_count: int = 0
        self.status: TaskStatus = TaskStatus.PENDING
        self.assigned_worker_id: Optional[str] = None

    # Priority queue comparator (Priority first, then scheduled execution time)
    def __lt__(self, other: 'Task') -> bool:
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.scheduled_time < other.scheduled_time

    def is_ready(self) -> bool:
        return time.time() >= self.scheduled_time


# ==========================================
# 2. WORKER NODE (Concurrent Executor)
# ==========================================

class WorkerNode:
    """A worker managing dynamic concurrent task execution and heartbeats."""
    def __init__(self, worker_id: str, max_concurrent_tasks: int = 3):
        self.worker_id: str = worker_id
        self.max_concurrent_tasks: int = max_concurrent_tasks
        self.active_tasks: Dict[str, Task] = {}
        self._pool: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=max_concurrent_tasks)
        self._lock: threading.Lock = threading.Lock()
        self.last_heartbeat: float = time.time()
        self.is_alive: bool = True

    @property
    def current_load(self) -> int:
        with self._lock:
            return len(self.active_tasks)

    @property
    def is_available(self) -> bool:
        with self._lock:
            return self.is_alive and (len(self.active_tasks) < self.max_concurrent_tasks)

    def heartbeat(self) -> None:
        with self._lock:
            self.last_heartbeat = time.time()

    def submit_task(self, task: Task, on_complete_cb: Callable[[Task, bool], None]) -> bool:
        with self._lock:
            if not self.is_available:
                return False

            task.status = TaskStatus.RUNNING
            task.assigned_worker_id = self.worker_id
            self.active_tasks[task.task_id] = task

        # Submit execution to thread pool
        self._pool.submit(self._execute_wrapper, task, on_complete_cb)
        return True

    def _execute_wrapper(self, task: Task, on_complete_cb: Callable[[Task, bool], None]) -> None:
        success = False
        try:
            print(f"⚙️ [Worker-{self.worker_id}] Executing Task: {task.task_id} (Priority: {task.priority.name})")
            task.executable_fn()
            task.status = TaskStatus.COMPLETED
            success = True
            print(f"✅ [Worker-{self.worker_id}] Task Completed: {task.task_id}")
        except Exception as e:
            print(f"❌ [Worker-{self.worker_id}] Task Failed: {task.task_id}, Error: {e}")
            task.status = TaskStatus.FAILED
        finally:
            with self._lock:
                self.active_tasks.pop(task.task_id, None)
            on_complete_cb(task, success)

    def stop(self) -> None:
        with self._lock:
            self.is_alive = False
        self._pool.shutdown(wait=False)


# ==========================================
# 3. LOAD BALANCING STRATEGY
# ==========================================

class LoadBalancingStrategy(ABC):
    @abstractmethod
    def select_worker(self, workers: List[WorkerNode]) -> Optional[WorkerNode]:
        pass


class LeastLoadedStrategy(LoadBalancingStrategy):
    """Routes tasks to the healthy worker with the least active load."""
    def select_worker(self, workers: List[WorkerNode]) -> Optional[WorkerNode]:
        available = [w for w in workers if w.is_available]
        if not available:
            return None
        # Sort by lowest active load
        return min(available, key=lambda w: w.current_load)


# ==========================================
# 4. DISTRIBUTED SCHEDULER ORCHESTRATOR
# ==========================================

class DistributedTaskScheduler:
    """Coordinates task queuing, worker balancing, thread safety, and failover monitoring."""
    def __init__(
        self,
        load_strategy: Optional[LoadBalancingStrategy] = None,
        heartbeat_timeout_sec: float = 3.0
    ):
        self._task_queue: List[Task] = []
        self._workers: Dict[str, WorkerNode] = {}
        self._load_strategy: LoadBalancingStrategy = load_strategy or LeastLoadedStrategy()
        self._lock: threading.Lock = threading.Lock()
        self._heartbeat_timeout: float = heartbeat_timeout_sec
        self._is_running: bool = True

        # Background loops
        self._scheduler_thread = threading.Thread(target=self._dispatch_loop, daemon=True)
        self._monitor_thread = threading.Thread(target=self._health_monitor_loop, daemon=True)
        
        self._scheduler_thread.start()
        self._monitor_thread.start()

    def register_worker(self, worker: WorkerNode) -> None:
        with self._lock:
            self._workers[worker.worker_id] = worker
            print(f"📡 Registered Worker [{worker.worker_id}] (Capacity: {worker.max_concurrent_tasks})")

    def submit_task(self, task: Task) -> None:
        with self._lock:
            heapq.heappush(self._task_queue, task)
            print(f"📥 Enqueued Task [{task.task_id}] (Priority: {task.priority.name})")

    def _on_task_finished(self, task: Task, success: bool) -> None:
        if not success and task.retry_count < task.max_retries:
            task.retry_count += 1
            task.status = TaskStatus.RETRYING
            task.scheduled_time = time.time() + 1.0  # Backoff delay
            print(f"🔁 Re-queueing Task [{task.task_id}] for Retry ({task.retry_count}/{task.max_retries})")
            with self._lock:
                heapq.heappush(self._task_queue, task)

    def _dispatch_loop(self) -> None:
        """Continuously pulls ready tasks and dispatches to optimal workers."""
        while self._is_running:
            task_to_assign: Optional[Task] = None

            with self._lock:
                if self._task_queue and self._task_queue[0].is_ready():
                    # Peek highest priority ready task
                    candidate_worker = self._load_strategy.select_worker(list(self._workers.values()))
                    if candidate_worker:
                        task_to_assign = heapq.heappop(self._task_queue)

            if task_to_assign and candidate_worker:
                candidate_worker.submit_task(task_to_assign, self._on_task_finished)
            else:
                time.sleep(0.05)  # Yield CPU if no tasks or no workers available

    def _health_monitor_loop(self) -> None:
        """Detects dead workers and re-queues interrupted active tasks."""
        while self._is_running:
            time.sleep(1.0)
            now = time.time()
            with self._lock:
                for worker_id, worker in list(self._workers.items()):
                    if now - worker.last_heartbeat > self._heartbeat_timeout and worker.is_alive:
                        print(f"⚠️ [ALERT] Worker [{worker_id}] timed out! Marking DEAD and recovering tasks.")
                        worker.stop()

                        # Recover unfinished tasks back to the priority queue
                        for task in list(worker.active_tasks.values()):
                            task.status = TaskStatus.PENDING
                            task.assigned_worker_id = None
                            heapq.heappush(self._task_queue, task)
                            print(f"♻️ Recovered Task [{task.task_id}] from dead worker [{worker_id}]")

    def shutdown(self) -> None:
        self._is_running = False
        for worker in self._workers.values():
            worker.stop()


# ==========================================
# 5. RUNTIME DEMO & CONCURRENCY TEST
# ==========================================

if __name__ == "__main__":
    scheduler = DistributedTaskScheduler()

    # 1. Register 2 Workers
    w1 = WorkerNode("W1", max_concurrent_tasks=2)
    w2 = WorkerNode("W2", max_concurrent_tasks=2)
    scheduler.register_worker(w1)
    scheduler.register_worker(w2)

    # 2. Define Workloads
    def heavy_job(name: str, duration: float):
        def _job():
            time.sleep(duration)
        return _job

    def failing_job():
        time.sleep(0.2)
        raise RuntimeError("Network Timeout")

    print("\n--- Submitting Multi-Priority Tasks ---")
    # Low priority task
    scheduler.submit_task(Task("T_LOW", TaskPriority.LOW, heavy_job("T_LOW", 0.8)))
    # High priority task
    scheduler.submit_task(Task("T_HIGH", TaskPriority.HIGH, heavy_job("T_HIGH", 0.4)))
    # Critical priority task (Should preemptively execute before medium/low)
    scheduler.submit_task(Task("T_CRITICAL", TaskPriority.CRITICAL, heavy_job("T_CRITICAL", 0.2)))
    # Failing task with retries
    scheduler.submit_task(Task("T_FAIL", TaskPriority.MEDIUM, failing_job, max_retries=1))

    # Simulate heartbeat pinging
    for _ in range(3):
        time.sleep(0.5)
        w1.heartbeat()
        w2.heartbeat()

    print("\n--- Simulating Worker Failure ---")
    # Register worker W3, submit a task to it, and simulate sudden crash (stop heartbeat)
    w3 = WorkerNode("W3", max_concurrent_tasks=1)
    scheduler.register_worker(w3)
    scheduler.submit_task(Task("T_CRASH_TEST", TaskPriority.CRITICAL, heavy_job("T_CRASH", 2.0)))

    # Do not ping W3 -> Trigger health monitor failover recovery
    time.sleep(4.0)

    scheduler.shutdown()
    print("\n🎉 Scheduler simulation completed successfully.")