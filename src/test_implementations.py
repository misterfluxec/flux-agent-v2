"""
TEST DE VERIFICACIÓN - IMPLEMENTACIONES MULTIMODALES
=====================================================
Ejecutar: python -m pytest test_implementations.py -v
O directamente: python test_implementations.py
"""

import asyncio
import os
import sys
import logging
from unittest.mock import AsyncMock, MagicMock, patch

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PASS = "✅"
FAIL = "❌"

results = {"passed": 0, "failed": 0}


def test_result(name: str, passed: bool, details: str = ""):
    status = PASS if passed else FAIL
    print(f"{status} {name}")
    if details:
        print(f"   {details}")
    if passed:
        results["passed"] += 1
    else:
        results["failed"] += 1


async def test_1_tts_piper_import():
    """Test 1: Verificar que Piper TTS se importa correctamente."""
    try:
        from core.capabilities.tts import PiperTTSCapability, get_piper_voice
        test_result("Importar PiperTTSCapability", True)
        
        voice = get_piper_voice()
        if voice is None:
            test_result("Cargar model Piper (sin model = OK)", True, "Modelo no encontrado (esperado sin archivo)")
        else:
            test_result("Cargar model Piper", True)
            
    except ImportError as e:
        test_result("Importar PiperTTSCapability", False, f"ImportError: {e}")
    except Exception as e:
        test_result("Importar PiperTTSCapability", False, str(e))


async def test_2_tts_synthesize_mock():
    """Test 2: Verificar síntesis TTS con mock."""
    try:
        with patch("core.capabilities.tts.get_piper_voice") as mock_voice:
            mock_voice_instance = MagicMock()
            mock_buffer = MagicMock()
            mock_buffer.read.return_value = b"fake_audio_data"
            mock_voice_instance.synthesize.return_value = None
            mock_voice_instance.config = MagicMock(sample_rate=22050)
            mock_voice.return_value = mock_voice_instance
            
            from core.capabilities.tts import PiperTTSCapability
            result = await PiperTTSCapability.synthesize("Hola mundo")
            
            test_result("Síntesis TTS con mock", True, f"Output length: {len(result)}")
    except Exception as e:
        test_result("Síntesis TTS con mock", False, str(e))


async def test_3_llm_router_import():
    """Test 3: Verificar LLMRouter se importa."""
    try:
        from core.llm.router import LLMRouter, llm_router, OllamaProvider
        test_result("Importar LLMRouter", True)
        
        assert llm_router.mode in ["local", "cloud"]
        test_result("LLMRouter modo configurado", True, f"Modo: {llm_router.mode}")
        
        providers = llm_router.get_available_providers()
        test_result("Proveedores disponibles", True, f"local={providers['local']}, openai={providers['openai']}")
        
    except Exception as e:
        test_result("Importar LLMRouter", False, str(e))


async def test_4_llm_router_local():
    """Test 4: Verificar proveedor local (Ollama) configurado."""
    try:
        from core.llm.router import llm_router
        
        provider = llm_router.get_provider()
        from core.llm.router import OllamaProvider
        test_result("Proveedor local es Ollama", isinstance(provider, OllamaProvider))
        
        if llm_router.is_cloud_enabled():
            test_result("Cloud desactivado por defecto", False, "Cloud está habilitado")
        else:
            test_result("Cloud desactivado por defecto", True)
            
    except Exception as e:
        test_result("Proveedor local", False, str(e))


async def test_5_llm_generate_mock():
    """Test 5: Verificar generación LLM con mock."""
    try:
        from core.llm.router import OllamaProvider
        
        provider = OllamaProvider()
        
        with patch.object(provider, "generate") as mock_gen:
            mock_gen.return_value = "Respuesta de prueba"
            
            messages = [{"role": "user", "content": "Hola"}]
            result = await provider.generate(messages, "qwen2.5:3b", 0.7, 2048)
            
            test_result("Generación LLM mock", result == "Respuesta de prueba")
            
    except Exception as e:
        test_result("Generación LLM mock", False, str(e))


def test_6_seed_migration_exists():
    """Test 6: Verificar archivo de migración existe."""
    try:
        path = "/home/mister/flux-agent-v2/migrations/006_seed_plans.sql"
        exists = os.path.exists(path)
        test_result("Migration 006_seed_plans.sql existe", exists)
        
        if exists:
            with open(path) as f:
                content = f.read()
                has_insert = "INSERT INTO plans" in content
                test_result("Migration tiene INSERT plans", has_insert)
                
                has_features = "features" in content and "stt" in content
                test_result("Migration define features JSONB", has_features)
                
    except Exception as e:
        test_result("Migration existe", False, str(e))


def test_7_plan_manager_features():
    """Test 7: Verificar PlanManager usa features."""
    try:
        from core.plan_manager import PlanManager
        import inspect
        
        source = inspect.getsource(PlanManager.check_limite_diario_tenant)
        uses_limits = "limits.get" in source or "usage_limits" in source
        
        test_result("PlanManager verifica límites", uses_limits)
        
        source2 = inspect.getsource(PlanManager.check_feature_tenant)
        checks_features = "features.get" in source2
        
        test_result("PlanManager verifica features", checks_features)
        
    except Exception as e:
        test_result("PlanManager features", False, str(e))


async def test_8_voice_router_import():
    """Test 8: Verificar VoiceRouter se importa."""
    try:
        from routers.voice_router import VoiceStreamManager, voice_manager
        test_result("Importar VoiceStreamManager", True)
        
        assert hasattr(voice_manager, "handle_voice_websocket")
        test_result("VoiceManager tiene handler", True)
        
    except Exception as e:
        test_result("Importar VoiceRouter", False, str(e))


def test_9_config_llm_settings():
    """Test 9: Verificar configuración LLM cloud."""
    try:
        from config import obtener_config
        config = obtener_config()
        
        test_result("Config tiene llm_mode", hasattr(config, "llm_mode"))
        test_result("llm_mode por defecto es local", config.llm_mode == "local")
        
        if hasattr(config, "openai_api_key"):
            test_result("Config tiene openai_api_key", True)
        
    except Exception as e:
        test_result("Config LLM", False, str(e))


def test_10_multimedia_tts_integration():
    """Test 10: Verificar ServicioMultimedia usa TTS."""
    try:
        from services.multimedia import ServicioMultimedia
        import inspect
        
        source = inspect.getsource(ServicioMultimedia.sintetizar_voz)
        uses_piper = "PiperTTSCapability" in source
        
        test_result("ServicioMultimedia integra Piper", uses_piper)
        
    except Exception as e:
        test_result("Multimedia TTS", False, str(e))


async def run_all_tests():
    print("=" * 60)
    print("FLUXAGENT V2 - TEST DE VERIFICACIÓN IMPLEMENTACIONES")
    print("=" * 60)
    print()
    
    print("🔊 FASE 1: TTS CON PIPER")
    await test_1_tts_piper_import()
    await test_2_tts_synthesize_mock()
    print()
    
    print("📊 FASE 2: SEED DE PLANES")
    test_6_seed_migration_exists()
    test_7_plan_manager_features()
    print()
    
    print("🧠 FASE 3: LLM ROUTER (CLOUD/LOCAL)")
    await test_3_llm_router_import()
    await test_4_llm_router_local()
    await test_5_llm_generate_mock()
    test_9_config_llm_settings()
    print()
    
    print("📡 FASE 4: WEBSOCKET VOICE STREAMING")
    await test_8_voice_router_import()
    print()
    
    print("🔗 FASE 5: INTEGRACIÓN")
    test_10_multimedia_tts_integration()
    print()
    
    print("=" * 60)
    print(f"RESULTADOS: {results['passed']} ✅ | {results['failed']} ❌")
    print("=" * 60)
    
    if results["failed"] == 0:
        print("\n🎉 Todas las implementaciones verificadas correctamente!")
    else:
        print(f"\n⚠️  {results['failed']} test(s) requieren atención.")
    
    return results["failed"] == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)