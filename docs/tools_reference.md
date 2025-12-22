# Tools Reference - OpenManus

## 📑 Índice

1. [Visão Geral](#visão-geral)
2. [Web Tools](#web-tools)
3. [File Tools](#file-tools)
4. [Code Tools](#code-tools)
5. [AI Tools](#ai-tools)
6. [MCP Tools](#mcp-tools)
7. [System Tools](#system-tools)

---

## 🎯 Visão Geral

OpenManus possui **80+ ferramentas** organizadas por categoria. Todas as ferramentas seguem a interface `BaseTool`:

```python
class BaseTool:
    name: str  # Tool identifier
    description: str  # What it does
    parameters: dict  # JSON schema for parameters

    async def execute(self, **kwargs) -> str:
        """Execute tool logic"""
        pass
```

---

## 🌐 Web Tools

### 1. WebSearch

**Descrição**: Pesquisa web via DuckDuckGo e Baidu (fallback)

**Parâmetros**:
```python
{
    "query": str,          # Search query
    "max_results": int,    # Max results (default: 10)
    "region": str          # Region code (optional)
}
```

**Exemplo**:
```python
result = await web_search.execute(
    query="Python async best practices",
    max_results=5
)
# Returns: [{title, url, snippet}, ...]
```

**Fallback**: DuckDuckGo → Baidu (auto)

---

### 2. BrowserUse

**Descrição**: Automação de browser com Playwright

**Ações disponíveis**:
- `go_to_url`: Navegar para URL
- `click_element`: Click em elemento
- `input_text`: Digitar texto
- `extract_content`: Extrair conteúdo da página
- `take_screenshot`: Capturar screenshot

**Exemplo**:
```python
# Navigate
await browser_use.execute(
    action="go_to_url",
    url="https://example.com"
)

# Extract content
content = await browser_use.execute(
    action="extract_content",
    goal="Get main article text"
)
```

---

### 3. FetchURL

**Descrição**: Download de conteúdo de URL

**Parâmetros**:
```python
{
    "url": str,
    "timeout": int,  # Seconds (default: 30)
}
```

**Exemplo**:
```python
html = await fetch_url.execute(
    url="https://api.example.com/data"
)
```

---

## 📁 File Tools

### 1. StrReplaceEditor

**Descrição**: Editor de arquivos com múltiplas operações

**Comandos**:
- `view`: Visualizar arquivo/diretório
- `create`: Criar novo arquivo
- `str_replace`: Substituir texto
- `insert`: Inserir linha
- `undo_edit`: Desfazer última edição

**Exemplo - View**:
```python
await str_replace_editor.execute(
    command="view",
    path="/path/to/file.py"
)
```

**Exemplo - Create**:
```python
await str_replace_editor.execute(
    command="create",
    path="/path/to/new_file.py",
    file_text="def hello():\n    print('Hello')"
)
```

**Exemplo - Replace**:
```python
await str_replace_editor.execute(
    command="str_replace",
    path="/path/to/file.py",
    old_str="def old_name():",
    new_str="def new_name():"
)
```

**Features**:
- ✅ UTF-8 com fallback (ISO-8859-1, replace mode)
- ✅ Validação de old_str vazio
- ✅ History tracking com undo
- ✅ Sandbox support

---

### 2. ReadFile

**Descrição**: Leitura simple de arquivo

**Parâmetros**:
```python
{
    "path": str  # Absolute path
}
```

**Exemplo**:
```python
content = await read_file.execute(
    path="/path/to/file.txt"
)
```

---

### 3. WriteFile

**Descrição**: Escrita simples em arquivo

**Parâmetros**:
```python
{
    "path": str,
    "content": str
}
```

**Exemplo**:
```python
await write_file.execute(
    path="/path/to/output.txt",
    content="Hello, World!"
)
```

---

### 4. ListDirectory

**Descrição**: Listar conteúdo de diretório

**Parâmetros**:
```python
{
    "path": str,
    "recursive": bool  # Default: False
}
```

**Exemplo**:
```python
files = await list_directory.execute(
    path="/path/to/dir",
    recursive=True
)
```

---

## ⚙️ Code Tools

### 1. PythonExecute

**Descrição**: Execução segura de código Python

**Parâmetros**:
```python
{
    "code": str,           # Python code
    "timeout": int,        # Seconds (default: 30)
    "use_sandbox": bool    # Execute in sandbox
}
```

**Exemplo**:
```python
result = await python_execute.execute(
    code="""
def fibonacci(n):
    if n <= 1: return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))
    """,
    timeout=10
)
# Returns: {output: "55", success: True}
```

**Features**:
- ✅ Sandboxed execution (Daytona)
- ✅ Timeout protection
- ✅ stdout/stderr capture
- ✅ Exception handling

---

### 2. Bash

**Descrição**: Executar shell commands

**Parâmetros**:
```python
{
    "command": str,
    "timeout": int,
    "use_sandbox": bool
}
```

**Exemplo**:
```python
result = await bash.execute(
    command="ls -la /tmp",
    timeout=5
)
```

**⚠️ Warning**: Use com cuidado! Prefer sandbox mode.

---

### 3. CodeLinter

**Descrição**: Lint de código Python

**Parâmetros**:
```python
{
    "code": str,          # Code to lint
    "linter": str         # "pylint" | "flake8"
}
```

**Exemplo**:
```python
lint_result = await code_linter.execute(
    code="def bad_function( ):pass",
    linter="pylint"
)
# Returns: {score: 3.5, issues: [...]}
```

---

## 🤖 AI Tools

### 1. AskHuman

**Descrição**: Solicitar input do usuário

**Parâmetros**:
```python
{
    "question": str,       # Question to ask
    "options": list        # Optional choices
}
```

**Exemplo**:
```python
answer = await ask_human.execute(
    question="Which framework?",
    options=["FastAPI", "Flask", "Django"]
)
```

---

### 2. MemoryStore

**Descrição**: Armazenar memória do usuário

**Parâmetros**:
```python
{
    "user_id": str,
    "content": str,
    "metadata": dict  # Optional tags
}
```

**Exemplo**:
```python
await memory_store.execute(
    user_id="user123",
    content="User prefers dark mode",
    metadata={"category": "preferences"}
)
```

---

### 3. MemoryQuery

**Descrição**: Busca semântica em memórias

**Parâmetros**:
```python
{
    "user_id": str,
    "query": str,
    "n_results": int  # Default: 5
}
```

**Exemplo**:
```python
memories = await memory_query.execute(
    user_id="user123",
    query="user preferences",
    n_results=3
)
```

---

### 4. TranscriptAudio

**Descrição**: Transcrição via Whisper

**Parâmetros**:
```python
{
    "audio_path": str,
    "model": str  # "base" | "small" | "medium" | "large"
}
```

**Exemplo**:
```python
text = await transcript_audio.execute(
    audio_path="/path/to/meeting.mp3",
    model="base"
)
```

---

## 🔌 MCP Tools

### MCPTool (Generic)

**Descrição**: Integração Model Context Protocol

**Servers Disponíveis**:
- GitHub
- Database
- Custom protocols

**Exemplo - GitHub**:
```python
mcp = MCPTool(server_name="github")

# Get repository
repo = await mcp.execute(
    action="get_repository",
    owner="user",
    repo="project"
)

# Create issue
issue = await mcp.execute(
    action="create_issue",
    repo="user/project",
    title="Bug found",
    body="Description..."
)
```

**Exemplo - Database**:
```python
mcp = MCPTool(server_name="database")

# Query
results = await mcp.execute(
    action="query",
    sql="SELECT * FROM users WHERE active=1"
)
```

---

## 🔧 System Tools

### 1. Terminate

**Descrição**: Finalizar task atual

**Parâmetros**:
```python
{
    "status": str  # "success" | "failure"
}
```

**Exemplo**:
```python
await terminate.execute(status="success")
```

---

### 2. Sleep

**Descrição**: Aguardar tempo

**Parâmetros**:
```python
{
    "seconds": int
}
```

**Exemplo**:
```python
await sleep.execute(seconds=5)
```

---

## 🎯 Tool Usage Patterns

### Pattern 1: Chaining Tools

```python
# Search → Extract → Summarize
search_results = await web_search.execute(query="...")
content = await fetch_url.execute(url=search_results[0]['url'])
summary = await llm.summarize(content)
```

### Pattern 2: Conditional Execution

```python
# Try sandbox first, fallback to local
try:
    result = await python_execute.execute(
        code=code,
        use_sandbox=True
    )
except SandboxError:
    result = await python execute.execute(
        code=code,
        use_sandbox=False
    )
```

### Pattern 3: File Operations Pipeline

```python
# Read → Edit → Write → Validate
original = await read_file.execute(path="script.py")
edited = await str_replace_editor.execute(
    command="str_replace",
    path="script.py",
    old_str="old",
    new_str="new"
)
lint = await code_linter.execute(code=edited)
```

---

## 📊 Tool Metadata

| Category | Count | Async | Sandbox |
|----------|-------|-------|---------|
| Web | 10+ | ✅ | N/A |
| File | 15+ | ✅ | ✅ |
| Code | 20+ | ✅ | ✅ |
| AI | 10+ | ✅ | N/A |
| MCP | 25+ | ✅ | Varies |
| System | 5+ | ✅ | N/A |

**Total**: 80+ tools

---

## 🔒 Security Considerations

### Sandboxing

```python
# ✅ SAFE: Sandboxed execution
await python_execute.execute(
    code=user_provided_code,
    use_sandbox=True  # Isolated environment
)

# ⚠️ RISKY: Local execution
await bash.execute(
    command=user_provided_command,
    use_sandbox=False  # Direct system access
)
```

### Input Validation

```python
# All tools validate inputs
await str_replace_editor.execute(
    command="str_replace",
    old_str=""  # ❌ Raises ToolError: "old_str cannot be empty"
)
```

### File Path Validation

```python
# Requires absolute paths
await read_file.execute(
    path="relative/path.txt"  # ❌ Raises ToolError
)

await read_file.execute(
    path="/absolute/path.txt"  # ✅ OK
)
```

---

## 🎓 Best Practices

1. **Use Sandbox**: Always prefer `use_sandbox=True` for code execution
2. **Handle Errors**: Check tool results for success
3. **Set Timeouts**: Prevent hanging operations
4. **Validate Inputs**: Check parameters before execution
5. **Chain Wisely**: Consider tool execution order

---

## 🔮 Roadmap

**Planned Tools**:
- [ ] DatabaseTool (SQL)
- [ ] EmailTool (SMTP)
- [ ] APITool (REST client)
- [ ] ImageGenerationTool (DALL-E)
- [ ] PDFTool (parsing/generation)

---

**Status**: ✅ 80+ Tools Available
**Última Atualização**: 2025-12-18
