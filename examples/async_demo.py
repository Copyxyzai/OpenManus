"""
Simple standalone demo of async parallel tasks
Run with: python examples/async_demo.py
"""

import asyncio
import time
from typing import List

# ============================================================================
# Example 1: Basic Parallel Execution
# ============================================================================


async def download_file(file_id: int, size_mb: int) -> str:
    """Simula download de arquivo"""
    print(f"📥 Downloading file {file_id} ({size_mb}MB)...")
    await asyncio.sleep(size_mb * 0.5)  # Simula tempo de download
    print(f"✅ File {file_id} downloaded!")
    return f"file_{file_id}.dat"


async def demo_parallel_downloads():
    """Download múltiplos arquivos em paralelo"""
    print("\n" + "=" * 60)
    print("DEMO 1: Downloads Paralelos")
    print("=" * 60)

    start = time.time()

    # SEQUENCIAL (lento)
    print("\n--- Sequencial ---")
    seq_start = time.time()
    file1 = await download_file(1, 2)
    file2 = await download_file(2, 2)
    file3 = await download_file(3, 2)
    seq_time = time.time() - seq_start
    print(f"⏱️  Tempo sequencial: {seq_time:.1f}s")

    # PARALELO (rápido)
    print("\n--- Paralelo ---")
    par_start = time.time()
    results = await asyncio.gather(
        download_file(4, 2),
        download_file(5, 2),
        download_file(6, 2),
    )
    par_time = time.time() - par_start
    print(f"⏱️  Tempo paralelo: {par_time:.1f}s")
    print(f"🚀 Ganho: {seq_time/par_time:.1f}x mais rápido!")


# ============================================================================
# Example 2: Controlled Concurrency with Semaphore
# ============================================================================


async def api_call(api_id: int) -> dict:
    """Simula chamada API"""
    print(f"  🌐 Calling API {api_id}...")
    await asyncio.sleep(1)
    return {"api": api_id, "data": "result"}


async def demo_limited_concurrency():
    """Controlar número de requisições simultâneas"""
    print("\n" + "=" * 60)
    print("DEMO 2: Concorrência Limitada")
    print("=" * 60)

    # Limitar a 3 requisições simultâneas
    semaphore = asyncio.Semaphore(3)

    async def controlled_call(api_id: int):
        async with semaphore:
            return await api_call(api_id)

    print(f"\nChamando 10 APIs (máx 3 simultâneas)...")
    start = time.time()
    results = await asyncio.gather(*[controlled_call(i) for i in range(10)])
    elapsed = time.time() - start

    print(f"\n✅ {len(results)} chamadas completadas em {elapsed:.1f}s")
    print(f"   (10 APIs / 3 paralelos = ~4 lotes × 1s = ~4s)")


# ============================================================================
# Example 3: Batch Processing
# ============================================================================


async def process_item(item_id: int) -> str:
    """Processa um item"""
    await asyncio.sleep(0.5)
    return f"Item {item_id} processed"


async def demo_batch_processing():
    """Processar itens em lotes"""
    print("\n" + "=" * 60)
    print("DEMO 3: Processamento em Lotes")
    print("=" * 60)

    items = list(range(20))
    batch_size = 5

    print(f"\nProcessando {len(items)} itens em lotes de {batch_size}...")

    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        print(f"  📦 Processando lote {i//batch_size + 1} ({len(batch)} itens)...")

        batch_results = await asyncio.gather(*[process_item(item) for item in batch])
        results.extend(batch_results)

    print(f"\n✅ Processados {len(results)} itens!")


# ============================================================================
# Example 4: Timeout Handling
# ============================================================================


async def slow_operation(delay: float):
    """Operação que pode demorar"""
    await asyncio.sleep(delay)
    return f"Completed after {delay}s"


async def demo_timeout():
    """Lidar com timeouts"""
    print("\n" + "=" * 60)
    print("DEMO 4: Timeout")
    print("=" * 60)

    # Operação rápida (sucesso)
    try:
        print("\n⏱️  Operação rápida (timeout: 2s)...")
        result = await asyncio.wait_for(slow_operation(1), timeout=2.0)
        print(f"✅ {result}")
    except asyncio.TimeoutError:
        print("❌ Timeout!")

    # Operação lenta (timeout)
    try:
        print("\n⏱️  Operação lenta (timeout: 2s)...")
        result = await asyncio.wait_for(slow_operation(5), timeout=2.0)
        print(f"✅ {result}")
    except asyncio.TimeoutError:
        print("❌ Timeout! Operação cancelada.")


# ============================================================================
# Example 5: Error Handling
# ============================================================================


async def task_that_fails(task_id: int):
    """Tarefa que pode falhar"""
    await asyncio.sleep(0.5)
    if task_id == 2:
        raise ValueError(f"Task {task_id} failed!")
    return f"Task {task_id} succeeded"


async def demo_error_handling():
    """Continuar mesmo com erros"""
    print("\n" + "=" * 60)
    print("DEMO 5: Tratamento de Erros")
    print("=" * 60)

    print("\nExecutando 5 tarefas (uma vai falhar)...")

    results = await asyncio.gather(
        task_that_fails(1),
        task_that_fails(2),  # Esta vai falhar
        task_that_fails(3),
        task_that_fails(4),
        task_that_fails(5),
        return_exceptions=True,  # Não parar em erros
    )

    print("\nResultados:")
    for i, result in enumerate(results, 1):
        if isinstance(result, Exception):
            print(f"  ❌ Task {i}: FALHOU - {result}")
        else:
            print(f"  ✅ Task {i}: {result}")


# ============================================================================
# Example 6: Real-world Scenario
# ============================================================================


async def fetch_user_profile(user_id: int) -> dict:
    """Busca perfil do usuário"""
    await asyncio.sleep(1)
    return {"id": user_id, "name": f"User {user_id}"}


async def fetch_user_posts(user_id: int) -> List[dict]:
    """Busca posts do usuário"""
    await asyncio.sleep(1.5)
    return [{"id": i, "text": f"Post {i}"} for i in range(3)]


async def fetch_user_friends(user_id: int) -> List[int]:
    """Busca amigos do usuário"""
    await asyncio.sleep(0.8)
    return [user_id + 1, user_id + 2]


async def demo_real_world():
    """Cenário real: carregar dados de usuário"""
    print("\n" + "=" * 60)
    print("DEMO 6: Cenário Real - Dashboard de Usuário")
    print("=" * 60)

    user_id = 42

    # SEQUENCIAL (lento)
    print("\n--- Sequencial ---")
    seq_start = time.time()
    profile = await fetch_user_profile(user_id)
    posts = await fetch_user_posts(user_id)
    friends = await fetch_user_friends(user_id)
    seq_time = time.time() - seq_start
    print(f"⏱️  Tempo: {seq_time:.1f}s (1.0 + 1.5 + 0.8 = 3.3s)")

    # PARALELO (rápido)
    print("\n--- Paralelo ---")
    par_start = time.time()
    profile, posts, friends = await asyncio.gather(
        fetch_user_profile(user_id),
        fetch_user_posts(user_id),
        fetch_user_friends(user_id),
    )
    par_time = time.time() - par_start
    print(f"⏱️  Tempo: {par_time:.1f}s (max(1.0, 1.5, 0.8) = 1.5s)")
    print(f"🚀 Ganho: {seq_time/par_time:.1f}x mais rápido!")

    print(f"\n✅ Dashboard carregado:")
    print(f"   - Profile: {profile}")
    print(f"   - Posts: {len(posts)} posts")
    print(f"   - Friends: {len(friends)} amigos")


# ============================================================================
# Main
# ============================================================================


async def main():
    """Executar todas as demos"""
    print("\n🚀 DEMOS - Tarefas Assíncronas em Paralelo")
    print("=" * 60)

    await demo_parallel_downloads()
    await demo_limited_concurrency()
    await demo_batch_processing()
    await demo_timeout()
    await demo_error_handling()
    await demo_real_world()

    print("\n" + "=" * 60)
    print("✅ Todas as demos completadas!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
