"""
Teste de integração completo do OpenManus
Verifica:
- Inicialização
- Estrutura refatorada
- Sistema de memória
- Sistema de áudio
- Tarefas assíncronas
"""

import os
import sys

# Adicionar path do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_imports():
    """Testar imports após refatoração"""
    print("\n🧪 Testando imports...")

    try:
        # Core tools (nova estrutura)
        from app.tools.core.bash import Bash
        from app.tools.core.python_execute import PythonExecute
        from app.tools.core.str_replace_editor import StrReplaceEditor

        print("✅ Core tools importados")

        # Web tools
        from app.tools.web.browser_use import BrowserUseTool
        from app.tools.web.web_search import WebSearch

        print("✅ Web tools importados")

        # AI tools
        from app.tools.ai.audio_transcription import AudioTool
        from app.tools.ai.memory import MemoryTool

        print("✅ AI tools importados")

        # Interaction tools
        from app.tools.interaction.ask_human import AskHuman
        from app.tools.interaction.terminate import Terminate

        print("✅ Interaction tools importados")

        # Async tasks
        from app.utils.async_tasks import AsyncTaskManager

        print("✅ Async tasks importado")

        # Memory system
        from app.memory.context_manager import ContextManager
        from app.memory.user_manager import UserManager
        from app.memory.vector_store import SimpleVectorStore

        print("✅ Memory system importado")

        # Audio system
        from app.audio.audio_processor import AudioProcessor
        from app.audio.whisper_service import WhisperService

        print("✅ Audio system importado")

        return True

    except Exception as e:
        print(f"❌ Erro nos imports: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_tool_initialization():
    """Testar inicialização de ferramentas"""
    print("\n🧪 Testando inicialização de ferramentas...")

    try:
        from app.tools.ai.memory import MemoryTool
        from app.tools.core.python_execute import PythonExecute

        # Testar criação
        python_tool = PythonExecute()
        print(f"✅ PythonExecute: {python_tool.name}")

        memory_tool = MemoryTool()
        print(f"✅ MemoryTool: {memory_tool.name}")

        return True

    except Exception as e:
        print(f"❌ Erro na inicialização: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_async_system():
    """Testar sistema de tarefas assíncronas"""
    print("\n🧪 Testando sistema async...")

    try:
        import asyncio

        from app.utils.async_tasks import AsyncTaskManager, run_parallel_tasks

        async def dummy_task(n):
            await asyncio.sleep(0.1)
            return f"Task {n} done"

        async def run_test():
            # Teste 1: AsyncTaskManager
            manager = AsyncTaskManager(max_concurrent=3)

            for i in range(5):
                manager.add_task(dummy_task(i), name=f"Test-{i}")

            results = await manager.run_parallel()
            print(f"✅ Manager executou {len(results)} tarefas")

            # Teste 2: Helper function
            results2 = await run_parallel_tasks(
                dummy_task(10), dummy_task(11), dummy_task(12)
            )
            print(f"✅ Helper executou {len(results2)} tarefas")

            return True

        success = asyncio.run(run_test())
        return success

    except Exception as e:
        print(f"❌ Erro no sistema async: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_backward_compatibility():
    """Testar compatibilidade reversa"""
    print("\n🧪 Testando backward compatibility...")

    try:
        import warnings

        # Capturar warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Importar do caminho antigo (deve funcionar com warning)
            from app.tool import BaseTool, ToolCollection

            if len(w) > 0:
                print(f"⚠️  Deprecation warning detectado (esperado): {w[0].message}")

            print("✅ Backward compatibility funcionando")
            return True

    except Exception as e:
        print(f"❌ Erro na compatibilidade: {e}")
        return False


def test_memory_system():
    """Testar sistema de memória"""
    print("\n🧪 Testando sistema de memória...")

    try:
        from app.memory.user_manager import UserManager
        from app.memory.vector_store import SimpleVectorStore

        # Testar UserManager
        user_mgr = UserManager()
        user_id = user_mgr.get_current_user_id()
        print(f"✅ UserManager inicializado (user: {user_id})")

        # Testar VectorStore
        store = SimpleVectorStore()
        print("✅ VectorStore inicializado")

        return True

    except Exception as e:
        print(f"❌ Erro no memory system: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_audio_system():
    """Testar sistema de áudio"""
    print("\n🧪 Testando sistema de áudio...")

    try:
        from app.audio.audio_processor import AudioProcessor
        from app.audio.whisper_service import WhisperService

        # Testar AudioProcessor
        processor = AudioProcessor()
        print(
            f"✅ AudioProcessor inicializado (formatos: {len(processor.SUPPORTED_FORMATS)})"
        )

        # Testar WhisperService
        whisper = WhisperService()
        print("✅ WhisperService inicializado")

        return True

    except Exception as e:
        print(f"❌ Erro no audio system: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Executar todos os testes"""
    print("=" * 60)
    print("🚀 OpenManus - Teste de Integração Completo")
    print("=" * 60)

    results = {
        "Imports": test_imports(),
        "Tool Initialization": test_tool_initialization(),
        "Async System": test_async_system(),
        "Backward Compatibility": test_backward_compatibility(),
        "Memory System": test_memory_system(),
        "Audio System": test_audio_system(),
    }

    print("\n" + "=" * 60)
    print("📊 Resultados dos Testes")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, success in results.items():
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{test_name:.<30} {status}")
        if success:
            passed += 1

    print("=" * 60)
    print(f"Total: {passed}/{total} testes passaram ({passed/total*100:.0f}%)")
    print("=" * 60)

    if passed == total:
        print("\n🎉 Todos os testes passaram! Sistema OK!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} teste(s) falharam")
        return 1


if __name__ == "__main__":
    sys.exit(main())
