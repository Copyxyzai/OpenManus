"""
Advanced async task examples with new features:
- Retry logic
- Progress tracking
- Rate limiting
- Performance metrics
"""

import asyncio
import random

from app.utils.async_tasks import AsyncTaskManager


# Example 1: Retry Logic
async def demo_retry_logic():
    """Demonstra retry automático em falhas"""
    print("\n" + "=" * 60)
    print("DEMO: Retry Logic")
    print("=" * 60)

    manager = AsyncTaskManager(max_concurrent=3)

    async def unreliable_task(success_rate: float):
        """Tarefa que falha aleatoriamente"""
        await asyncio.sleep(0.5)
        if random.random() > success_rate:
            raise ConnectionError("Network error!")
        return "Success!"

    # Callback para retry
    def on_retry(task_id: str, attempt: int, error: Exception):
        print(f"  🔄 {task_id} - Tentativa {attempt}: {error}")

    # Adicionar tarefas com retry
    for i in range(3):
        manager.add_task(
            unreliable_task(0.3),  # 30% de chance de sucesso
            name=f"Unreliable-{i}",
            max_retries=3,
            retry_delay=0.5,
            on_retry=on_retry,
        )

    results = await manager.run_parallel()

    print("\nResultados:")
    for result in results:
        status = "✅" if result.succeeded else "❌"
        retries = manager.tasks[result.task_id].retry_count
        print(f"  {status} {result.task_id}: {result.status} (retries: {retries})")

    manager.print_metrics()


# Example 2: Progress Tracking
async def demo_progress_tracking():
    """Demonstra rastreamento de progresso"""
    print("\n" + "=" * 60)
    print("DEMO: Progress Tracking")
    print("=" * 60)

    manager = AsyncTaskManager()

    async def long_task(task_id: str, duration: float, on_progress):
        """Tarefa longa com updates de progresso"""
        steps = 10
        for i in range(steps + 1):
            progress = (i / steps) * 100
            on_progress(task_id, progress)
            await asyncio.sleep(duration / steps)
        return "Completed!"

    # Callback de progresso
    progress_tracker = {}

    def on_progress(task_id: str, progress: float):
        progress_tracker[task_id] = progress
        bar = "█" * int(progress / 5)
        print(f"\r  {task_id}: [{bar:<20}] {progress:.0f}%", end="", flush=True)
        if progress >= 100:
            print()  # New line when complete

    # Adicionar tarefas com progress
    for i in range(3):
        task_id = manager.add_task(
            long_task(f"Task-{i}", 2.0, on_progress),
            name=f"Long-Task-{i}",
            on_progress=on_progress,
        )

    await manager.run_parallel()
    manager.print_metrics()


# Example 3: Rate Limiting
async def demo_rate_limiting():
    """Demonstra rate limiting"""
    print("\n" + "=" * 60)
    print("DEMO: Rate Limiting")
    print("=" * 60)

    manager = AsyncTaskManager(max_concurrent=10)

    async def api_call(endpoint: str):
        """S imula chamada API"""
        await asyncio.sleep(0.1)
        return f"Data from {endpoint}"

    print("\nSem rate limit (10 paralelos):")
    import time

    start = time.time()

    for i in range(10):
        manager.add_task(api_call(f"/endpoint{i}"), name=f"API-NoLimit-{i}")

    await manager.run_parallel()
    no_limit_time = time.time() - start
    print(f"  ⏱️  Tempo: {no_limit_time:.2f}s")

    # Limpar para próximo teste
    manager.clear()

    print("\nCom rate limit (5 req/s):")
    start = time.time()

    for i in range(10):
        manager.add_task(
            api_call(f"/endpoint{i}"),
            name=f"API-Limited-{i}",
            rate_limit=5.0,  # 5 requests por segundo
        )

    await manager.run_parallel()
    limited_time = time.time() - start
    print(f"  ⏱️  Tempo: {limited_time:.2f}s")
    print(f"  ℹ️  Rate limit respeitou: 10 req / 5 req/s = ~2s")


# Example 4: Timeout with Retry
async def demo_timeout_retry():
    """Demonstra timeout com retry"""
    print("\n" + "=" * 60)
    print("DEMO: Timeout with Retry")
    print("=" * 60)

    manager = AsyncTaskManager()

    async def sometimes_slow_task():
        """Tarefa que às vezes demora"""
        delay = random.choice([0.5, 0.5, 0.5, 3.0])  # 75% rápido, 25% lento
        await asyncio.sleep(delay)
        return f"Completed after {delay}s"

    # Adicionar com timeout e retry
    for i in range(5):
        manager.add_task(
            sometimes_slow_task(),
            name=f"Timeout-Task-{i}",
            timeout=1.5,  # Timeout de 1.5s
            max_retries=2,  # Retry 2 vezes
            retry_delay=0.2,
        )

    results = await manager.run_parallel()

    print("\nResultados:")
    for result in results:
        status = "✅" if result.succeeded else "❌"
        duration = result.duration or 0
        print(f"  {status} {result.task_id}: {duration:.2f}s")

    manager.print_metrics()


# Example 5: Cancellation
async def demo_cancellation():
    """Demonstra cancelamento de tarefas"""
    print("\n" + "=" * 60)
    print("DEMO: Task Cancellation")
    print("=" * 60)

    manager = AsyncTaskManager()

    async def long_running_task(task_id: int):
        """Tarefa que demora"""
        print(f"  🚀 Starting long task {task_id}")
        await asyncio.sleep(10)  # Muito tempo
        return f"Task {task_id} done"

    # Adicionar tarefas lentas
    for i in range(5):
        manager.add_task(long_running_task(i), name=f"Long-{i}")

    # Iniciar execução
    async def cancel_after_delay():
        await asyncio.sleep(2)  # Esperar 2s
        print("\n  🛑 Cancelling all tasks...")
        manager.cancel_all()

    # Executar com cancelamento
    await asyncio.gather(
        manager.run_parallel(), cancel_after_delay(), return_exceptions=True
    )

    print("\nResultados após cancelamento:")
    for task in manager.tasks.values():
        if task.result:
            print(f"  {task.result.status}: {task.name}")

    manager.print_metrics()


# Example 6: Complete Real-World Scenario
async def demo_real_world_complete():
    """Cenário completo com todos os recursos"""
    print("\n" + "=" * 60)
    print("DEMO: Real-World Complete Scenario")
    print("=" * 60)

    manager = AsyncTaskManager(max_concurrent=5, enable_metrics=True)

    # Simular diferentes tipos de tarefas
    async def fetch_data(source: str):
        """Fetch com possível falha"""
        await asyncio.sleep(random.uniform(0.5, 2.0))
        if random.random() < 0.2:  # 20% de falha
            raise ConnectionError(f"Failed to fetch from {source}")
        return {"source": source, "data": "some data"}

    async def process_data(data: dict):
        """Processamento"""
        await asyncio.sleep(1.0)
        return f"Processed: {data['source']}"

    async def save_result(result: str):
        """Salvar com timeout"""
        await asyncio.sleep(random.uniform(0.3, 1.5))
        return f"Saved: {result}"

    # Progress tracker
    def progress_callback(task_id: str, progress: float):
        if progress >= 100:
            print(f"  ✅ {task_id} completed")

    # Retry callback
    def retry_callback(task_id: str, attempt: int, error: Exception):
        print(f"  🔄 {task_id} retry {attempt}: {error}")

    # Pipeline de tarefas
    print("\nExecutando pipeline com retry, timeout, rate limit...")

    # Fetch tasks (com retry)
    fetch_tasks = []
    for i in range(10):
        task_id = manager.add_task(
            fetch_data(f"API-{i}"),
            name=f"Fetch-{i}",
            max_retries=2,
            retry_delay=0.5,
            timeout=3.0,
            rate_limit=5.0,  # Max 5 fetches/segundo
            on_progress=progress_callback,
            on_retry=retry_callback,
        )
        fetch_tasks.append(task_id)

    # Execute
    results = await manager.run_parallel()

    print("\n📊 Métricas Finais:")
    manager.print_metrics()


# Main
async def main():
    print("\n" + "=" * 60)
    print("🚀 Advanced Async Task Features Demo")
    print("=" * 60)

    await demo_retry_logic()
    await demo_progress_tracking()
    await demo_rate_limiting()
    await demo_timeout_retry()
    await demo_cancellation()
    await demo_real_world_complete()

    print("\n" + "=" * 60)
    print("✅ All demos completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
