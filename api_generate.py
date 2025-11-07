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
from db_utils import fetch_inventory_data_from_db

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
BOT_URL = os.getenv("BOT_URL", "https://gioia-bot-production.up.railway.app")  # URL del bot per callback
VIEWER_URL = os.getenv("VIEWER_URL", "https://vineinventory-viewer-production.up.railway.app")  # URL del viewer stesso

# Assicura che gli URL abbiano il protocollo
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
        
        # 1. Estrai i dati direttamente dal database
        processor_data = await asyncio.to_thread(
            fetch_inventory_data_from_db,
            telegram_id,
            business_name,
            correlation_id,
        )
        
        if not processor_data:
            raise Exception("Dati inventario non disponibili")
        
        logger.info(
            f"[VIEWER_GENERATE] Dati estratti dal database: rows={len(processor_data.get('rows', []))}, "
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
        
        # 5. Invia link al bot (attende completamento per evitare chiusura loop)
        try:
            await _send_link_to_bot(telegram_id, viewer_url, correlation_id)
        except Exception as cb_error:
            logger.error(
                f"[VIEWER_CALLBACK] Errore nell'invio del link al bot: {cb_error}",
                exc_info=True
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
                logger.info(
                    f"[VIEWER_CALLBACK] Inizio richiesta POST a {url}, "
                    f"payload keys: {list(payload.keys())}, telegram_id={telegram_id}, correlation_id={correlation_id}"
                )
                async with session.post(url, json=payload) as response:
                    response_text = await response.text()
                    logger.info(
                        f"[VIEWER_CALLBACK] Risposta dal bot: HTTP {response.status}, "
                        f"response={response_text[:200]}, telegram_id={telegram_id}, correlation_id={correlation_id}"
                    )
                    if response.status == 200:
                        logger.info(
                            f"[VIEWER_CALLBACK] ✅ Link inviato con successo al bot, "
                            f"telegram_id={telegram_id}, correlation_id={correlation_id}"
                        )
                    else:
                        logger.error(
                            f"[VIEWER_CALLBACK] ❌ Errore invio link al bot: HTTP {response.status}, "
                            f"telegram_id={telegram_id}, error={response_text[:200]}, correlation_id={correlation_id}"
                        )
            except asyncio.TimeoutError as timeout_error:
                logger.error(
                    f"[VIEWER_CALLBACK] ⏱️ Timeout richiesta HTTP al bot dopo 10s: {timeout_error}, "
                    f"url={url}, telegram_id={telegram_id}, correlation_id={correlation_id}",
                    exc_info=True
                )
            except aiohttp.ClientError as client_error:
                logger.error(
                    f"[VIEWER_CALLBACK] 🔴 Errore client HTTP al bot: {client_error}, "
                    f"url={url}, telegram_id={telegram_id}, correlation_id={correlation_id}",
                    exc_info=True
                )
            except Exception as req_error:
                logger.error(
                    f"[VIEWER_CALLBACK] ❌ Errore generico richiesta HTTP al bot: {req_error}, "
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
