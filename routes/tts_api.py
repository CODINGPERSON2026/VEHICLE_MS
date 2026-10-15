"""
TTS API - Google India Girl Voice (en-IN-NeerjaExpressiveNeural via edge-tts)
Serves pre-rendered MP3 audio for gate announcements directly from the server.
Browser voice independence - always sounds like a natural Indian girl regardless of OS/browser.
"""
import asyncio
import io
import threading
from flask import Blueprint, request, Response, abort
from flask_login import login_required

tts_bp = Blueprint('tts', __name__)

VOICE = 'en-IN-NeerjaExpressiveNeural'  # Google en-in Neerja (Expressive Indian female voice)

_AUDIO_CACHE = {}
_CACHE_LOCK = threading.Lock()

def _run_edge_tts_sync(text: str) -> bytes:
    """Run edge-tts in a fresh event loop (thread-safe for Flask)."""
    try:
        import edge_tts

        buf = io.BytesIO()

        async def _generate():
            communicate = edge_tts.Communicate(text, VOICE, rate='-5%', pitch='+0Hz')
            async for chunk in communicate.stream():
                if chunk['type'] == 'audio':
                    buf.write(chunk['data'])

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(asyncio.wait_for(_generate(), timeout=5.0))
        finally:
            loop.close()

        return buf.getvalue()
    except Exception as e:
        raise RuntimeError(f'edge-tts failed: {e}')


def _run_pyttsx3_fallback(text: str) -> bytes:
    """Offline TTS fallback using Windows SAPI/pyttsx3 (strictly female only)."""
    import tempfile
    import os
    import pyttsx3

    tf = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    tmp_path = tf.name
    tf.close()
    try:
        engine = pyttsx3.init()
        # Strictly select a female voice (Zira, Swara, Heera, etc.). NEVER David or male!
        selected_voice = None
        for v in engine.getProperty('voices'):
            vname = v.name.lower()
            if any(term in vname for term in ['zira', 'female', 'swara', 'kalpana', 'heera', 'hindi', 'india']):
                if not any(m in vname for m in ['david', 'male', 'prabhat', 'madhur', 'ravi', 'mark']):
                    selected_voice = v.id
                    break

        if selected_voice:
            engine.setProperty('voice', selected_voice)
        else:
            raise RuntimeError("No female voice available for pyttsx3 fallback")

        engine.setProperty('rate', 145)
        engine.save_to_file(text, tmp_path)
        engine.runAndWait()
        with open(tmp_path, 'rb') as f:
            return f.read()
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


@tts_bp.route('/api/tts/speak')
@login_required
def speak():
    """
    GET /api/tts/speak?text=...
    Returns audio of the given text spoken in Indian voice (with offline fallback).
    """
    text = request.args.get('text', '').strip()
    if not text:
        abort(400, 'No text provided')
    if len(text) > 400:
        text = text[:400]

    # Check cache first for 0ms latency on repeated announcements
    with _CACHE_LOCK:
        if text in _AUDIO_CACHE:
            cached_bytes, cached_type = _AUDIO_CACHE[text]
            return Response(
                cached_bytes,
                mimetype=cached_type,
                headers={
                    'Cache-Control': 'public, max-age=86400',
                    'Content-Length': str(len(cached_bytes)),
                }
            )

    # Try high-quality Edge TTS first
    try:
        audio_bytes = _run_edge_tts_sync(text)
        content_type = 'audio/mpeg'
    except Exception as e:
        # Fallback to local offline TTS engine so request never 500s
        try:
            audio_bytes = _run_pyttsx3_fallback(text)
            content_type = 'audio/wav'
        except Exception as fb_err:
            abort(500, f"TTS generation failed: {e}; Fallback failed: {fb_err}")

    # Cache response (up to 300 entries)
    with _CACHE_LOCK:
        if len(_AUDIO_CACHE) < 300:
            _AUDIO_CACHE[text] = (audio_bytes, content_type)

    return Response(
        audio_bytes,
        mimetype=content_type,
        headers={
            'Cache-Control': 'public, max-age=86400',
            'Content-Length': str(len(audio_bytes)),
        }
    )

