"""
Async Task Manager for OpenManus
Provides utilities for parallel task execution and task management.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class TaskStatus(Enum):
    """Task execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskResult:
    """Result of an async task execution"""

    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[Exception] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None

    @property
    def succeeded(self) -> bool:
        return self.status == TaskStatus.COMPLETED

    @property
    def failed(self) -> bool:
        return self.status == TaskStatus.FAILED


@dataclass
class Task:
    """Represents an async task"""

    id: str
    coroutine: Coroutine
    name: str = ""
    priority: int = 0
    dependencies: List[str] = field(default_factory=list)
    result: Optional[TaskResult] = None


class AsyncTaskManager:
    """
    Manager for async task execution with parallel processing support.

    Features:
    - Execute tasks in parallel
    - Task dependencies
    - Priority-based execution
    - Timeout management
    - Result tracking
    """

    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.tasks: Dict[str, Task] = {}
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self._task_counter = 0

    def add_task(
        self,
        coro: Coroutine,
        name: str = "",
        priority: int = 0,
        dependencies: List[str] = None,
    ) -> str:
        """
        Add a task to the manager.

        Args:
            coro: Coroutine to execute
            name: Task name for logging
            priority: Higher priority tasks execute first
            dependencies: List of task IDs that must complete first

        Returns:
            Task ID
        """
        task_id = f"task_{self._task_counter}"
        self._task_counter += 1

        task = Task(
            id=task_id,
            coroutine=coro,
            name=name or task_id,
            priority=priority,
            dependencies=dependencies or [],
        )

        self.tasks[task_id] = task
        logger.info(f"Added task {task_id}: {task.name}")
        return task_id

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute a single task with semaphore control"""
        result = TaskResult(
            task_id=task.id, status=TaskStatus.RUNNING, start_time=datetime.now()
        )

        async with self.semaphore:
            try:
                logger.info(f"🚀 Starting task: {task.name}")
                result.result = await task.coroutine
                result.status = TaskStatus.COMPLETED
                logger.info(f"✅ Completed task: {task.name}")

            except asyncio.CancelledError:
                result.status = TaskStatus.CANCELLED
                logger.warning(f"⚠️ Cancelled task: {task.name}")
                raise

            except Exception as e:
                result.status = TaskStatus.FAILED
                result.error = e
                logger.error(f"❌ Failed task: {task.name} - {e}")

            finally:
                result.end_time = datetime.now()
                if result.start_time:
                    result.duration = (
                        result.end_time - result.start_time
                    ).total_seconds()

        return result

    async def run_parallel(
        self, task_ids: Optional[List[str]] = None, return_exceptions: bool = True
    ) -> List[TaskResult]:
        """
        Run multiple tasks in parallel.

        Args:
            task_ids: List of task IDs to run (None = all tasks)
            return_exceptions: If True, exceptions are returned as results

        Returns:
            List of task results
        """
        if task_ids is None:
            tasks_to_run = list(self.tasks.values())
        else:
            tasks_to_run = [self.tasks[tid] for tid in task_ids if tid in self.tasks]

        # Sort by priority (higher first)
        tasks_to_run.sort(key=lambda t: t.priority, reverse=True)

        logger.info(
            f"🔄 Running {len(tasks_to_run)} tasks in parallel (max concurrent: {self.max_concurrent})"
        )

        # Create async tasks
        async_tasks = [
            asyncio.create_task(self.execute_task(task)) for task in tasks_to_run
        ]

        # Wait for all tasks to complete
        results = await asyncio.gather(
            *async_tasks, return_exceptions=return_exceptions
        )

        # Store results
        for task, result in zip(tasks_to_run, results):
            if isinstance(result, TaskResult):
                task.result = result

        return results

    async def run_sequential(self, task_ids: List[str]) -> List[TaskResult]:
        """Run tasks sequentially in order"""
        results = []
        for task_id in task_ids:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                result = await self.execute_task(task)
                task.result = result
                results.append(result)
        return results

    async def run_with_dependencies(self) -> Dict[str, TaskResult]:
        """
        Run tasks respecting dependencies.
        Tasks with no dependencies run first in parallel.
        """
        completed = set()
        results = {}

        while len(completed) < len(self.tasks):
            # Find tasks that can run now (dependencies met)
            ready_tasks = [
                task
                for task in self.tasks.values()
                if task.id not in completed
                and all(dep in completed for dep in task.dependencies)
            ]

            if not ready_tasks:
                # Deadlock or all complete
                break

            # Run ready tasks in parallel
            logger.info(f"🔄 Running {len(ready_tasks)} tasks with met dependencies")
            task_results = await self.run_parallel([t.id for t in ready_tasks])

            for task, result in zip(ready_tasks, task_results):
                if isinstance(result, TaskResult):
                    results[task.id] = result
                    if result.succeeded:
                        completed.add(task.id)

        return results

    async def run_with_timeout(
        self, task_ids: List[str], timeout: float
    ) -> List[TaskResult]:
        """
        Run tasks with a timeout.

        Args:
            task_ids: Task IDs to run
            timeout: Timeout in seconds

        Returns:
            List of results (may include TimeoutError)
        """
        try:
            return await asyncio.wait_for(self.run_parallel(task_ids), timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"⏱️ Tasks timed out after {timeout}s")
            return [
                TaskResult(
                    task_id=tid,
                    status=TaskStatus.FAILED,
                    error=asyncio.TimeoutError(f"Task timed out after {timeout}s"),
                )
                for tid in task_ids
            ]

    def cancel_all(self):
        """Cancel all pending tasks"""
        self._cancelled = True
        logger.warning("🛑 Cancelling all tasks...")

    def clear(self):
        """Clear all tasks and reset metrics"""
        self.tasks.clear()
        self._task_counter = 0
        self._cancelled = False
        if self.enable_metrics:
            self.metrics = {
                "total_tasks": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0,
                "retries": 0,
                "total_duration": 0.0,
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        if not self.enable_metrics:
            return {}

        metrics = self.metrics.copy()

        if metrics["total_tasks"] > 0:
            metrics["success_rate"] = (
                metrics["completed"] / metrics["total_tasks"]
            ) * 100
            metrics["avg_duration"] = metrics["total_duration"] / metrics["total_tasks"]
        else:
            metrics["success_rate"] = 0.0
            metrics["avg_duration"] = 0.0

        return metrics

    def print_metrics(self):
        """Print formatted metrics"""
        metrics = self.get_metrics()
        if not metrics:
            print("Metrics disabled")
            return

        print("\n📊 Task Execution Metrics:")
        print("=" * 40)
        print(f"Total Tasks:    {metrics['total_tasks']}")
        print(f"Completed:      {metrics['completed']} ✅")
        print(f"Failed:         {metrics['failed']} ❌")
        print(f"Cancelled:      {metrics['cancelled']} ⚠️")
        print(f"Retries:        {metrics['retries']} 🔄")
        print(f"Success Rate:   {metrics['success_rate']:.1f}%")
        print(f"Avg Duration:   {metrics['avg_duration']:.2f}s")
        print(f"Total Duration: {metrics['total_duration']:.2f}s")
        print("=" * 40)


# Convenience functions for common patterns


async def run_parallel_tasks(
    *coroutines: Coroutine, max_concurrent: int = 10, return_exceptions: bool = True
) -> List[Any]:
    """
    Simple helper to run multiple coroutines in parallel.

    Example:
        results = await run_parallel_tasks(
            fetch_url("http://example.com"),
            fetch_url("http://google.com"),
            fetch_url("http://github.com"),
            max_concurrent=2
        )
    """
    manager = AsyncTaskManager(max_concurrent=max_concurrent)

    for i, coro in enumerate(coroutines):
        manager.add_task(coro, name=f"task_{i}")

    results = await manager.run_parallel(return_exceptions=return_exceptions)
    return [r.result for r in results if isinstance(r, TaskResult)]


async def run_with_timeout(coro: Coroutine, timeout: float) -> Any:
    """
    Run a coroutine with timeout.

    Example:
        result = await run_with_timeout(slow_function(), timeout=5.0)
    """
    return await asyncio.wait_for(coro, timeout=timeout)


async def run_in_batches(coroutines: List[Coroutine], batch_size: int) -> List[Any]:
    """
    Run coroutines in batches to limit concurrency.

    Example:
        # Run 100 tasks, 10 at a time
        results = await run_in_batches(all_tasks, batch_size=10)
    """
    results = []

    for i in range(0, len(coroutines), batch_size):
        batch = coroutines[i : i + batch_size]
        logger.info(f"🔄 Processing batch {i//batch_size + 1} ({len(batch)} tasks)")

        batch_results = await asyncio.gather(*batch, return_exceptions=True)
        results.extend(batch_results)

    return results
