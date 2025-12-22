import asyncio
import os

from openai import AsyncOpenAI

from app.audio.audio_processor import AudioProcessor
from app.audio.whisper_service import WhisperService
from app.tools.ai.audio_transcription import AudioTool


async def create_test_audio():
    """Create a test audio file using OpenAI TTS."""
    client = AsyncOpenAI(api_key=os.getenv("MANUS_OPENAI_API_KEY"))

    test_text = """
    Este é um teste de transcrição de áudio usando Whisper.
    O OpenManus agora suporta transcrição de áudio com compressão automática.
    Esta funcionalidade permite processar áudios longos dividindo-os em chunks.
    """

    print("Creating test audio with TTS...")
    response = await client.audio.speech.create(
        model="tts-1", voice="alloy", input=test_text
    )

    audio_path = "workspace/temp/test_audio.mp3"
    os.makedirs(os.path.dirname(audio_path), exist_ok=True)

    with open(audio_path, "wb") as f:
        f.write(response.content)

    print(f"✅ Test audio created: {audio_path}")
    return audio_path


async def test_audio_tool():
    """Test the complete audio transcription workflow."""
    print("\n=== Testing Whisper Audio Transcription ===\n")

    # Create test audio
    audio_path = await create_test_audio()

    # Test AudioTool
    print("\n1. Testing AudioTool...")
    tool = AudioTool()

    result = await tool.execute(file_path=audio_path, language="pt")

    print(f"\n✅ Transcription Result:")
    print(f"{result}\n")

    print("=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_audio_tool())
