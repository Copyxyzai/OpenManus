"""
Examples of async task execution patterns for OpenManus
"""

import asyncio

from app.utils.async_tasks import (
    AsyncTaskManager,
    run_in_batches,
    run_parallel_tasks,
    run_with_timeout,
)


# Example 1: Basic parallel execution
async def example_basic_parallel():
    """Run multiple independent tasks in parallel"""

    async def fetch_data(source: str, delay: float):
        await asyncio.sleep(delay)
        return f"Data from {source}"

    # Method 1: Using helper function
    results = await run_parallel_tasks(
        fetch_data("API-1", 1.0),
        fetch_data("API-2", 1.5),
        fetch_data("API-3", 0.5),
        max_concurrent=3,
    )

    print("Results:", results)


# Example 2: Using AsyncTaskManager with priorities
async def example_with_priorities():
    """Execute tasks with different priorities"""

    manager = AsyncTaskManager(max_concurrent=2)

    async def important_task():
        await asyncio.sleep(0.5)
        return "Important result"

    async def normal_task(n: int):
        await asyncio.sleep(1.0)
        return f"Normal result {n}"

    # Add tasks with priorities (higher = more important)
    manager.add_task(important_task(), name="Critical", priority=10)
    manager.add_task(normal_task(1), name="Task 1", priority=5)
    manager.add_task(normal_task(2), name="Task 2", priority=5)
    manager.add_task(normal_task(3), name="Task 3", priority=1)

    # Run all tasks (highest priority first)
    results = await manager.run_parallel()

    for result in results:
        if result.succeeded:
            print(f"{result.task_id}: {result.result} (took {result.duration:.2f}s)")


# Example 3: Tasks with dependencies
async def example_with_dependencies():
    """Execute tasks with dependencies"""

    manager = AsyncTaskManager()

    async def load_config():
        await asyncio.sleep(0.5)
        return {"api_key": "secret"}

    async def fetch_user_data(config):
        await asyncio.sleep(1.0)
        return {"user": "samuel", "role": "admin"}

    async def fetch_projects(user_data):
        await asyncio.sleep(1.0)
        return ["OpenManus", "ProjectX"]

    # Add tasks with dependencies
    task1 = manager.add_task(load_config(), name="Load Config")
    task2 = manager.add_task(
        fetch_user_data(None), name="Fetch User", dependencies=[task1]
    )
    task3 = manager.add_task(
        fetch_projects(None), name="Fetch Projects", dependencies=[task2]
    )

    # Run respecting dependencies
    results = await manager.run_with_dependencies()

    for task_id, result in results.items():
        print(f"{task_id}: {result.status} - {result.result}")


# Example 4: Batch processing
async def example_batch_processing():
    """Process large number of tasks in batches"""

    async def process_item(item_id: int):
        await asyncio.sleep(0.1)
        return f"Processed item {item_id}"

    # Create 50 tasks
    tasks = [process_item(i) for i in range(50)]

    # Process in batches of 10
    results = await run_in_batches(tasks, batch_size=10)

    print(f"Processed {len(results)} items")


# Example 5: Timeout handling
async def example_with_timeout():
    """Handle tasks that might take too long"""

    async def slow_operation():
        await asyncio.sleep(10)  # Very slow
        return "Done"

    try:
        result = await run_with_timeout(slow_operation(), timeout=2.0)
        print(result)
    except asyncio.TimeoutError:
        print("⏱️ Operation timed out!")


# Example 6: Real-world - Multiple tool execution
async def example_parallel_tool_execution():
    """Execute multiple OpenManus tools in parallel"""

    from app.tools.core.python_execute import PythonExecute
    from app.tools.web.web_search import WebSearch

    manager = AsyncTaskManager(max_concurrent=3)

    # Simulate multiple tool calls
    async def search_task(query: str):
        tool = WebSearch()
        return await tool.execute(query=query, num_results=3)

    async def python_task(code: str):
        tool = PythonExecute()
        return await tool.execute(code=code)

    # Add multiple tool executions
    manager.add_task(search_task("Python async programming"), name="Search 1")
    manager.add_task(search_task("FastAPI best practices"), name="Search 2")
    manager.add_task(
        python_task("print('Hello from parallel task')"), name="Python Exec"
    )

    # Execute all in parallel
    results = await manager.run_parallel()

    for result in results:
        if result.succeeded:
            print(f"✅ {result.result}")


# Example 7: Error handling with continue
async def example_error_handling():
    """Continue execution even if some tasks fail"""

    async def task_that_fails():
        await asyncio.sleep(0.5)
        raise ValueError("Something went wrong!")

    async def task_that_works(n: int):
        await asyncio.sleep(0.5)
        return f"Success {n}"

    results = await run_parallel_tasks(
        task_that_works(1),
        task_that_fails(),
        task_that_works(2),
        return_exceptions=True,  # Don't stop on error
    )

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Task {i} failed: {result}")
        else:
            print(f"Task {i} succeeded: {result}")


# Run examples
async def main():
    print("\n=== Example 1: Basic Parallel ===")
    await example_basic_parallel()

    print("\n=== Example 2: With Priorities ===")
    await example_with_priorities()

    print("\n=== Example 4: Batch Processing ===")
    await example_batch_processing()

    print("\n=== Example 5: Timeout ===")
    await example_with_timeout()

    print("\n=== Example 7: Error Handling ===")
    await example_error_handling()


if __name__ == "__main__":
    asyncio.run(main())
