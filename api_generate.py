#!/usr/bin/env python3
"""
Endpoint API per generazione viewer HTML
"""
import json
import os
import sys
import logging
import uuid
import time
from datetime import datetime
from typing import Dict, Any, Optional
import aiohttp
import asyncio
from logging_config import setup_colored_logging

# Configurazione logging colorato (se non già configurato)
try:
    setup_colored_logging("viewer")
except:
    pass  # Già configurato in server.py

logger = logging.getLogger(__name__)

# Cache in-memory per HTML generati (view_id -> (html, timestamp))
_viewer_html_cache = {}
_cache_expiry_seconds = 3600  # 1 ora

# URL servizi
PROCESSOR_URL = os.getenv("PROCESSOR_URL", "https://gioia-processor-production.up.railway.app")
BOT_URL = os.getenv("BOT_URL", "https://gioia-bot-production.up.railway.app")  # URL del bot per callback
VIEWER_URL = os.getenv("VIEWER_URL", "https://vineinventory-viewer-production.up.railway.app")  # URL del viewer stesso

# Assicura che gli URL abbiano il protocollo
if PROCESSOR_URL and not PROCESSOR_URL.startswith(("http://", "https://")):
    PROCESSOR_URL = f"https://{PROCESSOR_URL}"
if BOT_URL and not BOT_URL.startswith(("http://", "https://")):
    BOT_URL = f"https://{BOT_URL}"
if VIEWER_URL and not VIEWER_URL.startswith(("http://", "https://")):
    VIEWER_URL = f"https://{VIEWER_URL}"


async def generate_viewer_html(
    telegram_id: int,
    business_name: str,
    correlation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Genera HTML viewer completo:
    1. Chiede dati al processor
    2. Genera HTML con dati embedded
    3. Salva in cache
    4. Invia link al bot
    """
    try:
        logger.info(
            f"[VIEWER_GENERATE] Inizio generazione per telegram_id={telegram_id}, "
            f"business_name={business_name}, correlation_id={correlation_id}"
        )
        
        # 1. Chiedi dati al processor
        processor_data = await _fetch_data_from_processor(telegram_id, correlation_id)
        
        if not processor_data:
            raise Exception("Dati non disponibili dal processor")
        
        logger.info(
            f"[VIEWER_GENERATE] Dati ricevuti dal processor: rows={len(processor_data.get('rows', []))}, "
            f"telegram_id={telegram_id}, correlation_id={correlation_id}"
        )
        
        # 2. Genera HTML con dati embedded
        view_id = str(uuid.uuid4())
        html = _generate_html_with_data(processor_data, view_id)
        
        # 3. Salva in cache
        _viewer_html_cache[view_id] = (html, time.time())
        
        logger.info(
            f"[VIEWER_GENERATE] HTML generato e salvato: view_id={view_id}, "
            f"html_length={len(html)}, telegram_id={telegram_id}, correlation_id={correlation_id}"
        )
        
        # 4. Genera URL viewer
        viewer_url = f"{VIEWER_URL}/?view_id={view_id}"
        
        # 5. Invia link al bot (async, non blocca)
        asyncio.create_task(
            _send_link_to_bot(telegram_id, viewer_url, correlation_id)
        )
        
        return {
            "status": "completed",
            "view_id": view_id,
            "viewer_url": viewer_url,
            "telegram_id": telegram_id
        }
        
    except Exception as e:
        logger.error(
            f"[VIEWER_GENERATE] Errore generazione viewer: {e}, "
            f"telegram_id={telegram_id}, correlation_id={correlation_id}",
            exc_info=True
        )
        raise


async def _fetch_data_from_processor(
    telegram_id: int,
    correlation_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Chiede dati inventario al processor.
    Riprova più volte se i dati non sono ancora pronti.
    """
    max_retries = 5
    retry_delay = 2  # secondi
    
    for attempt in range(max_retries):
        try:
            url = f"{PROCESSOR_URL}/api/viewer/data?telegram_id={telegram_id}"
            
            logger.info(
                f"[VIEWER_FETCH] Tentativo {attempt + 1}/{max_retries}: richiesta dati a processor, "
                f"url={url}, telegram_id={telegram_id}, correlation_id={correlation_id}"
            )
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(
                            f"[VIEWER_FETCH] Dati ricevuti dal processor: rows={len(data.get('rows', []))}, "
                            f"telegram_id={telegram_id}, correlation_id={correlation_id}"
                        )
                        return data
                    elif response.status == 404:
                        # Dati non ancora pronti
                        if attempt < max_retries - 1:
                            logger.warning(
                                f"[VIEWER_FETCH] Dati non ancora pronti, riprovo tra {retry_delay} secondi "
                                f"(tentativo {attempt + 1}/{max_retries}), "
                                f"telegram_id={telegram_id}, correlation_id={correlation_id}"
                            )
                            await asyncio.sleep(retry_delay)
                            continue
                        else:
                            logger.error(
                                f"[VIEWER_FETCH] Dati non disponibili dopo {max_retries} tentativi, "
                                f"telegram_id={telegram_id}, correlation_id={correlation_id}"
                            )
                            return None
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"[VIEWER_FETCH] Errore richiesta processor: HTTP {response.status}, "
                            f"telegram_id={telegram_id}, error={error_text[:200]}, "
                            f"correlation_id={correlation_id}"
                        )
                        return None
                        
        except Exception as e:
            logger.error(
                f"[VIEWER_FETCH] Errore chiamata processor (tentativo {attempt + 1}/{max_retries}): {e}, "
                f"telegram_id={telegram_id}, correlation_id={correlation_id}",
                exc_info=True
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                return None
    
    return None


def _generate_html_with_data(data: Dict[str, Any], view_id: str) -> str:
    """
    Genera HTML completo con dati embedded.
    """
    # Leggi template base
    template_path = os.path.join(os.path.dirname(__file__), 'index.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        html_template = f.read()
    
    # Inietta dati embedded
    embedded_data_script = f'''
<script>
    window.EMBEDDED_INVENTORY_DATA = {json.dumps(data, ensure_ascii=False)};
    console.log("[VIEWER] Dati embedded caricati:", window.EMBEDDED_INVENTORY_DATA);
</script>
'''
    
    # Inserisci script prima di </head>
    if '</head>' in html_template:
        html = html_template.replace('</head>', embedded_data_script + '</head>')
    else:
        html = html_template.replace('<body>', embedded_data_script + '<body>')
    
    return html


async def _send_link_to_bot(
    telegram_id: int,
    viewer_url: str,
    correlation_id: Optional[str] = None
):
    """
    Invia link pronto al bot.
    """
    try:
        url = f"{BOT_URL}/api/viewer/link-ready"
        
        payload = {
            "telegram_id": telegram_id,
            "viewer_url": viewer_url,
            "correlation_id": correlation_id
        }
        
        logger.info(
            f"[VIEWER_CALLBACK] Invio link al bot: url={url}, "
            f"telegram_id={telegram_id}, correlation_id={correlation_id}"
        )
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            try:
                async with session.post(url, json=payload) as response:
                    response_text = await response.text()
                    logger.info(
                        f"[VIEWER_CALLBACK] Risposta dal bot: HTTP {response.status}, "
                        f"response={response_text[:200]}, telegram_id={telegram_id}, correlation_id={correlation_id}"
                    )
                    if response.status == 200:
                        logger.info(
                            f"[VIEWER_CALLBACK] Link inviato con successo al bot, "
                            f"telegram_id={telegram_id}, correlation_id={correlation_id}"
                        )
                    else:
                        logger.error(
                            f"[VIEWER_CALLBACK] Errore invio link al bot: HTTP {response.status}, "
                            f"telegram_id={telegram_id}, error={response_text[:200]}"
                        )
            except Exception as req_error:
                logger.error(
                    f"[VIEWER_CALLBACK] Errore richiesta HTTP al bot: {req_error}, "
                    f"url={url}, telegram_id={telegram_id}, correlation_id={correlation_id}",
                    exc_info=True
                )
                    
    except Exception as e:
        logger.error(
            f"[VIEWER_CALLBACK] Errore callback bot: {e}, "
            f"telegram_id={telegram_id}, correlation_id={correlation_id}",
            exc_info=True
        )


def get_viewer_html_from_cache(view_id: str) -> tuple[Optional[str], bool]:
    """
    Recupera HTML dalla cache.
    """
    if view_id not in _viewer_html_cache:
        return None, False
    
    html, timestamp = _viewer_html_cache[view_id]
    
    # Verifica scadenza
    if time.time() - timestamp > _cache_expiry_seconds:
        logger.warning(f"[VIEWER_CACHE] View ID {view_id} scaduto, rimuovo dalla cache")
        del _viewer_html_cache[view_id]
        return None, False
    
    return html, True

Endpoint API per generazione viewer HTML
"""
import json
import os
import sys
import logging
import uuid
import time
from datetime import datetime
from typing import Dict, Any, Optional
import aiohttp
import asyncio
from logging_config import setup_colored_logging

# Configurazione logging colorato (se non già configurato)
try:
    setup_colored_logging("viewer")
except:
    pass  # Già configurato in server.py

logger = logging.getLogger(__name__)

# Cache in-memory per HTML generati (view_id -> (html, timestamp))
_viewer_html_cache = {}
_cache_expiry_seconds = 3600  # 1 ora

# URL servizi
PROCESSOR_URL = os.getenv("PROCESSOR_URL", "https://gioia-processor-production.up.railway.app")
BOT_URL = os.getenv("BOT_URL", "https://gioia-bot-production.up.railway.app")  # URL del bot per callback
VIEWER_URL = os.getenv("VIEWER_URL", "https://vineinventory-viewer-production.up.railway.app")  # URL del viewer stesso

# Assicura che gli URL abbiano il protocollo
if PROCESSOR_URL and not PROCESSOR_URL.startswith(("http://", "https://")):
    PROCESSOR_URL = f"https://{PROCESSOR_URL}"
if BOT_URL and not BOT_URL.startswith(("http://", "https://")):
    BOT_URL = f"https://{BOT_URL}"
if VIEWER_URL and not VIEWER_URL.startswith(("http://", "https://")):
    VIEWER_URL = f"https://{VIEWER_URL}"


async def generate_viewer_html(
    telegram_id: int,
    business_name: str,
    correlation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Genera HTML viewer completo:
    1. Chiede dati al processor
    2. Genera HTML con dati embedded
    3. Salva in cache
    4. Invia link al bot
    """
    try:
        logger.info(
            f"[VIEWER_GENERATE] Inizio generazione per telegram_id={telegram_id}, "
            f"business_name={business_name}, correlation_id={correlation_id}"
        )
        
        # 1. Chiedi dati al processor
        processor_data = await _fetch_data_from_processor(telegram_id, correlation_id)
        
        if not processor_data:
            raise Exception("Dati non disponibili dal processor")
        
        logger.info(
            f"[VIEWER_GENERATE] Dati ricevuti dal processor: rows={len(processor_data.get('rows', []))}, "
            f"telegram_id={telegram_id}, correlation_id={correlation_id}"
        )
        
        # 2. Genera HTML con dati embedded
        view_id = str(uuid.uuid4())
        html = _generate_html_with_data(processor_data, view_id)
        
        # 3. Salva in cache
        _viewer_html_cache[view_id] = (html, time.time())
        
        logger.info(
            f"[VIEWER_GENERATE] HTML generato e salvato: view_id={view_id}, "
            f"html_length={len(html)}, telegram_id={telegram_id}, correlation_id={correlation_id}"
        )
        
        # 4. Genera URL viewer
        viewer_url = f"{VIEWER_URL}/?view_id={view_id}"
        
        # 5. Invia link al bot (async, non blocca)
        asyncio.create_task(
            _send_link_to_bot(telegram_id, viewer_url, correlation_id)
        )
        
        return {
            "status": "completed",
            "view_id": view_id,
            "viewer_url": viewer_url,
            "telegram_id": telegram_id
        }
        
    except Exception as e:
        logger.error(
            f"[VIEWER_GENERATE] Errore generazione viewer: {e}, "
            f"telegram_id={telegram_id}, correlation_id={correlation_id}",
            exc_info=True
        )
        raise


async def _fetch_data_from_processor(
    telegram_id: int,
    correlation_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Chiede dati inventario al processor.
    Riprova più volte se i dati non sono ancora pronti.
    """
    max_retries = 5
    retry_delay = 2  # secondi
    
    for attempt in range(max_retries):
        try:
            url = f"{PROCESSOR_URL}/api/viewer/data?telegram_id={telegram_id}"
            
            logger.info(
                f"[VIEWER_FETCH] Tentativo {attempt + 1}/{max_retries}: richiesta dati a processor, "
                f"url={url}, telegram_id={telegram_id}, correlation_id={correlation_id}"
            )
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(
                            f"[VIEWER_FETCH] Dati ricevuti dal processor: rows={len(data.get('rows', []))}, "
                            f"telegram_id={telegram_id}, correlation_id={correlation_id}"
                        )
                        return data
                    elif response.status == 404:
                        # Dati non ancora pronti
                        if attempt < max_retries - 1:
                            logger.warning(
                                f"[VIEWER_FETCH] Dati non ancora pronti, riprovo tra {retry_delay} secondi "
                                f"(tentativo {attempt + 1}/{max_retries}), "
                                f"telegram_id={telegram_id}, correlation_id={correlation_id}"
                            )
                            await asyncio.sleep(retry_delay)
                            continue
                        else:
                            logger.error(
                                f"[VIEWER_FETCH] Dati non disponibili dopo {max_retries} tentativi, "
                                f"telegram_id={telegram_id}, correlation_id={correlation_id}"
                            )
                            return None
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"[VIEWER_FETCH] Errore richiesta processor: HTTP {response.status}, "
                            f"telegram_id={telegram_id}, error={error_text[:200]}, "
                            f"correlation_id={correlation_id}"
                        )
                        return None
                        
        except Exception as e:
            logger.error(
                f"[VIEWER_FETCH] Errore chiamata processor (tentativo {attempt + 1}/{max_retries}): {e}, "
                f"telegram_id={telegram_id}, correlation_id={correlation_id}",
                exc_info=True
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                return None
    
    return None


def _generate_html_with_data(data: Dict[str, Any], view_id: str) -> str:
    """
    Genera HTML completo con dati embedded.
    """
    # Leggi template base
    template_path = os.path.join(os.path.dirname(__file__), 'index.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        html_template = f.read()
    
    # Inietta dati embedded
    embedded_data_script = f'''
<script>
    window.EMBEDDED_INVENTORY_DATA = {json.dumps(data, ensure_ascii=False)};
    console.log("[VIEWER] Dati embedded caricati:", window.EMBEDDED_INVENTORY_DATA);
</script>
'''
    
    # Inserisci script prima di </head>
    if '</head>' in html_template:
        html = html_template.replace('</head>', embedded_data_script + '</head>')
    else:
        html = html_template.replace('<body>', embedded_data_script + '<body>')
    
    return html


async def _send_link_to_bot(
    telegram_id: int,
    viewer_url: str,
    correlation_id: Optional[str] = None
):
    """
    Invia link pronto al bot.
    """
    try:
        url = f"{BOT_URL}/api/viewer/link-ready"
        
        payload = {
            "telegram_id": telegram_id,
            "viewer_url": viewer_url,
            "correlation_id": correlation_id
        }
        
        logger.info(
            f"[VIEWER_CALLBACK] Invio link al bot: url={url}, "
            f"telegram_id={telegram_id}, correlation_id={correlation_id}"
        )
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            try:
                async with session.post(url, json=payload) as response:
                    response_text = await response.text()
                    logger.info(
                        f"[VIEWER_CALLBACK] Risposta dal bot: HTTP {response.status}, "
                        f"response={response_text[:200]}, telegram_id={telegram_id}, correlation_id={correlation_id}"
                    )
                    if response.status == 200:
                        logger.info(
                            f"[VIEWER_CALLBACK] Link inviato con successo al bot, "
                            f"telegram_id={telegram_id}, correlation_id={correlation_id}"
                        )
                    else:
                        logger.error(
                            f"[VIEWER_CALLBACK] Errore invio link al bot: HTTP {response.status}, "
                            f"telegram_id={telegram_id}, error={response_text[:200]}"
                        )
            except Exception as req_error:
                logger.error(
                    f"[VIEWER_CALLBACK] Errore richiesta HTTP al bot: {req_error}, "
                    f"url={url}, telegram_id={telegram_id}, correlation_id={correlation_id}",
                    exc_info=True
                )
                    
    except Exception as e:
        logger.error(
            f"[VIEWER_CALLBACK] Errore callback bot: {e}, "
            f"telegram_id={telegram_id}, correlation_id={correlation_id}",
            exc_info=True
        )


def get_viewer_html_from_cache(view_id: str) -> tuple[Optional[str], bool]:
    """
    Recupera HTML dalla cache.
    """
    if view_id not in _viewer_html_cache:
        return None, False
    
    html, timestamp = _viewer_html_cache[view_id]
    
    # Verifica scadenza
    if time.time() - timestamp > _cache_expiry_seconds:
        logger.warning(f"[VIEWER_CACHE] View ID {view_id} scaduto, rimuovo dalla cache")
        del _viewer_html_cache[view_id]
        return None, False
    
    return html, True
