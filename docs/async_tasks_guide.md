# Guia de Uso - Sistema de Tarefas Assíncronas

## Visão Geral

O OpenManus agora possui um sistema completo de gerenciamento de tarefas assíncronas que permite executar múltiplas operações em paralelo para melhorar performance.

## Componentes

### 1. AsyncTaskManager
Gerenciador principal para execução de tarefas assíncronas.

**Recursos:**
- ✅ Execução paralela com limite de concorrência
- ✅ Sistema de prioridades
- ✅ Gerenciamento de dependências entre tarefas
- ✅ Timeout configurável
- ✅ Rastreamento de resultados

### 2. Funções Helper
Funções auxiliares para casos de uso comuns.

## Exemplos de Uso

### Exemplo 1: Execução Paralela Básica

```python
import asyncio
from app.utils.async_tasks import run_parallel_tasks

async def fetch_data(source: str):
    await asyncio.sleep(1)  # Simula I/O
    return f"Data from {source}"

# Executar 3 tarefas em paralelo
results = await run_parallel_tasks(
    fetch_data("API-1"),
    fetch_data("API-2"),
    fetch_data("API-3"),
    max_concurrent=3
)

print(results)  # ['Data from API-1', 'Data from API-2', 'Data from API-3']
```

### Exemplo 2: Com Prioridades

```python
from app.utils.async_tasks import AsyncTaskManager

manager = AsyncTaskManager(max_concurrent=2)

async def critical_task():
    return "Critical result"

async def normal_task():
    return "Normal result"

# Tarefas críticas executam primeiro
manager.add_task(critical_task(), name="Critical", priority=10)
manager.add_task(normal_task(), name="Normal 1", priority=5)
manager.add_task(normal_task(), name="Normal 2", priority=5)

results = await manager.run_parallel()
```

### Exemplo 3: Com Dependências

```python
manager = AsyncTaskManager()

async def load_config():
    return {"api_key": "secret"}

async def fetch_data(config):
    return f"Data with {config['api_key']}"

# Task 2 depende de Task 1
task1 = manager.add_task(load_config(), name="Load Config")
task2 = manager.add_task(
    fetch_data(None),
    name="Fetch Data",
    dependencies=[task1]  # Só executa após task1
)

results = await manager.run_with_dependencies()
```

### Exemplo 4: Processamento em Lotes

```python
from app.utils.async_tasks import run_in_batches

# Processar 100 itens, 10 por vez
async def process_item(item_id):
    return f"Processed {item_id}"

tasks = [process_item(i) for i in range(100)]
results = await run_in_batches(tasks, batch_size=10)
```

### Exemplo 5: Com Timeout

```python
from app.utils.async_tasks import run_with_timeout

async def slow_operation():
    await asyncio.sleep(10)
    return "Done"

try:
    result = await run_with_timeout(slow_operation(), timeout=5.0)
except asyncio.TimeoutError:
    print("Operação demorou demais!")
```

### Exemplo 6: Tratamento de Erros

```python
async def may_fail():
    raise ValueError("Erro!")

async def works():
    return "Sucesso"

# Continue mesmo se algumas tarefas falharem
results = await run_parallel_tasks(
    works(),
    may_fail(),
    works(),
    return_exceptions=True
)

for result in results:
    if isinstance(result, Exception):
        print(f"Falhou: {result}")
    else:
        print(f"Sucesso: {result}")
```

## Uso no Agent

### Executar Múltiplas Ferramentas em Paralelo

```python
from app.utils.async_tasks import AsyncTaskManager
from app.tools.web.web_search import WebSearch
from app.tools.core.python_execute import PythonExecute

manager = AsyncTaskManager(max_concurrent=5)

# Executar buscas em paralelo
search_tool = WebSearch()
manager.add_task(
    search_tool.execute(query="Python async", num_results=3),
    name="Search Python"
)
manager.add_task(
    search_tool.execute(query="FastAPI tutorial", num_results=3),
    name="Search FastAPI"
)

# Executar código em paralelo
python_tool = PythonExecute()
manager.add_task(
    python_tool.execute(code="print('Task 1')"),
    name="Python Task 1"
)

results = await manager.run_parallel()
```

## Padrões Recomendados

### 1. **I/O-bound tasks**: Use execução paralela
```python
# ANTES (sequencial - lento)
result1 = await fetch_url("url1")
result2 = await fetch_url("url2")
result3 = await fetch_url("url3")
# Total: 3 * tempo_de_fetch

# DEPOIS (paralelo - rápido)
results = await run_parallel_tasks(
    fetch_url("url1"),
    fetch_url("url2"),
    fetch_url("url3")
)
# Total: max(tempos_de_fetch)
```

### 2. **Limite de concorrência**: Evite sobrecarga
```python
# Processar 1000 itens, mas só 10 por vez
manager = AsyncTaskManager(max_concurrent=10)
for i in range(1000):
    manager.add_task(process_item(i))

results = await manager.run_parallel()
```

### 3. **Timeouts**: Evite travamentos
```python
# Sempre use timeout para operações externas
result = await run_with_timeout(
    api_call(),
    timeout=30.0  # 30 segundos
)
```

## Performance

### Ganhos Esperados

**Exemplo: 10 buscas web**
- Sequencial: ~20 segundos (10 × 2s cada)
- Paralelo (max_concurrent=5): ~4 segundos (2 lotes × 2s)
- **Ganho: 5x mais rápido**

**Exemplo: Processar 100 arquivos**
- Sequencial: 100 segundos
- Paralelo (max_concurrent=20): ~5 segundos
- **Ganho: 20x mais rápido**

## Melhores Práticas

✅ **Use para**: Chamadas API, I/O, web scraping, processamento de arquivos
❌ **Não use para**: CPU-bound tasks (use ProcessPoolExecutor)

✅ **Defina**: max_concurrent razoável (5-20 para I/O)
❌ **Evite**: Concorrência ilimitada (pode sobrecarregar)

✅ **Implemente**: Timeout para operações externas
❌ **Não ignore**: Tratamento de erros

## Integração com OpenManus Agent

O sistema pode ser integrado facilmente no fluxo do agent para:

1. **Buscar múltiplas fontes simultaneamente**
2. **Processar listas de itens em paralelo**
3. **Executar ferramentas independentes ao mesmo tempo**
4. **Melhorar tempo de resposta geral**

## Arquivo de Implementação

- **Core**: `app/utils/async_tasks.py`
- **Exemplos**: `examples/async_tasks_examples.py`

## Testes

Para testar o sistema:

```bash
# Executar exemplos
python -c "import sys; sys.path.insert(0, '.'); from examples.async_tasks_examples import main; import asyncio; asyncio.run(main())"
```

## Recursos Avançados

### Monitoramento de Progresso

```python
manager = AsyncTaskManager()

# Adicionar várias tarefas
for i in range(10):
    manager.add_task(process(i), name=f"Task {i}")

results = await manager.run_parallel()

# Verificar resultados
for task in manager.tasks.values():
    if task.result:
        print(f"{task.name}: {task.result.status} ({task.result.duration:.2f}s)")
```

### Pipeline de Dados

```python
# Processar dados em pipeline
async def stage1(data):
    return data.upper()

async def stage2(data):
    return data + " processed"

manager = AsyncTaskManager()
t1 = manager.add_task(stage1("input"), name="Stage 1")
t2 = manager.add_task(stage2(None), name="Stage 2", dependencies=[t1])

await manager.run_with_dependencies()
```
