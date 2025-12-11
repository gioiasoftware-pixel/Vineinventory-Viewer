"""
Database utilities per viewer - chiamata diretta al database senza processor
"""
import os
import jwt
import logging
import asyncpg
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Configurazione database
DATABASE_URL = os.getenv("DATABASE_URL")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production-secret-key-2025")
JWT_ALGORITHM = "HS256"

# Verifica configurazione all'avvio
if not DATABASE_URL:
    logger.error("[VIEWER_DB] ❌ DATABASE_URL non configurata! Il viewer non funzionerà.")
    logger.error("[VIEWER_DB] Configura DATABASE_URL su Railway → Settings → Variables")

if not JWT_SECRET_KEY or JWT_SECRET_KEY == "change-me-in-production-secret-key-2025":
    logger.warning("[VIEWER_DB] ⚠️ JWT_SECRET_KEY non configurata o default!")
    logger.warning("[VIEWER_DB] ⚠️ Configura JWT_SECRET_KEY su Railway → Settings → Variables")
    logger.warning("[VIEWER_DB] ⚠️ Deve essere la STESSA chiave del bot!")
else:
    logger.info("[VIEWER_DB] ✅ JWT_SECRET_KEY configurata correttamente")


def validate_viewer_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Valida token JWT per viewer.
    
    Args:
        token: Token JWT da validare
        
    Returns:
        Dict con telegram_id e business_name se valido, None se non valido o scaduto
    """
    try:
        if not token:
            logger.warning("[JWT_VALIDATE] Token vuoto")
            return None
        
        # Log dettagliato per debug
        logger.info(f"[JWT_VALIDATE] Inizio validazione token, length={len(token)}")
        logger.debug(f"[JWT_VALIDATE] Token (primi 50 char): {token[:50]}...")
        logger.debug(f"[JWT_VALIDATE] JWT_SECRET_KEY configurata: {bool(JWT_SECRET_KEY)}")
        logger.debug(f"[JWT_VALIDATE] JWT_SECRET_KEY length: {len(JWT_SECRET_KEY) if JWT_SECRET_KEY else 0}")
        logger.debug(f"[JWT_VALIDATE] JWT_SECRET_KEY (primi 20 char): {JWT_SECRET_KEY[:20] if JWT_SECRET_KEY else 'None'}...")
        logger.debug(f"[JWT_VALIDATE] JWT_ALGORITHM: {JWT_ALGORITHM}")
        
        # Decodifica e valida token
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        
        # Estrai dati necessari
        telegram_id = payload.get("telegram_id")
        business_name = payload.get("business_name")
        
        if not telegram_id or not business_name:
            logger.warning(
                f"[JWT_VALIDATE] Token valido ma payload incompleto: "
                f"telegram_id={telegram_id}, business_name={business_name}"
            )
            return None
        
        logger.info(
            f"[JWT_VALIDATE] ✅ Token JWT validato con successo: "
            f"telegram_id={telegram_id}, business_name={business_name}"
        )
        
        return {
            "telegram_id": telegram_id,
            "business_name": business_name
        }
        
    except jwt.ExpiredSignatureError as e:
        logger.warning(f"[JWT_VALIDATE] ❌ Token JWT scaduto: {e}")
        return None
    except jwt.InvalidSignatureError as e:
        logger.error(
            f"[JWT_VALIDATE] ❌ Firma token non valida (chiave JWT_SECRET_KEY non corrisponde): {e}"
        )
        logger.error(
            f"[JWT_VALIDATE] ⚠️ Verifica che JWT_SECRET_KEY sia identica nel bot e nel viewer!"
        )
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"[JWT_VALIDATE] ❌ Token JWT non valido: {e}")
        logger.debug(f"[JWT_VALIDATE] Tipo errore: {type(e).__name__}")
        return None
    except Exception as e:
        logger.error(
            f"[JWT_VALIDATE] ❌ Errore durante validazione token JWT: {e}",
            exc_info=True
        )
        return None


async def get_inventory_snapshot(telegram_id: int, business_name: str) -> Dict[str, Any]:
    """
    Recupera snapshot inventario direttamente dal database.
    
    Args:
        telegram_id: Telegram ID dell'utente
        business_name: Nome del business
        
    Returns:
        Dict con rows, facets e meta
    """
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL non configurata")
    
    conn = None
    try:
        # Connetti al database
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Nome tabella inventario
        table_name = f'"{telegram_id}/{business_name} INVENTARIO"'
        
        # Verifica che utente esista
        user_query = "SELECT id FROM users WHERE telegram_id = $1"
        user_row = await conn.fetchrow(user_query, telegram_id)
        
        if not user_row:
            raise ValueError(f"Utente con telegram_id {telegram_id} non trovato")
        
        user_id = user_row['id']
        
        # Recupera tutti i vini
        wines_query = f"""
            SELECT 
                name,
                producer,
                vintage,
                quantity,
                selling_price,
                wine_type,
                min_quantity,
                updated_at
            FROM {table_name}
            WHERE user_id = $1
            ORDER BY name, vintage
        """
        
        wines_rows = await conn.fetch(wines_query, user_id)
        
        # Formatta vini per risposta
        rows = []
        for wine in wines_rows:
            rows.append({
                "name": wine['name'] or "-",
                "winery": wine['producer'] or "-",
                "vintage": wine['vintage'],
                "qty": wine['quantity'] or 0,
                "price": float(wine['selling_price']) if wine['selling_price'] else 0.0,
                "type": wine['wine_type'] or "Altro",
                "critical": wine['quantity'] is not None and wine['min_quantity'] is not None and wine['quantity'] <= wine['min_quantity']
            })
        
        # Calcola facets (aggregazioni per filtri)
        facets = {
            "type": {},
            "vintage": {},
            "winery": {}
        }
        
        for wine in wines_rows:
            # Tipo
            wine_type = wine['wine_type'] or "Altro"
            facets["type"][wine_type] = facets["type"].get(wine_type, 0) + 1
            
            # Annata
            if wine['vintage']:
                vintage_str = str(wine['vintage'])
                facets["vintage"][vintage_str] = facets["vintage"].get(vintage_str, 0) + 1
            
            # Cantina (producer)
            if wine['producer']:
                facets["winery"][wine['producer']] = facets["winery"].get(wine['producer'], 0) + 1
        
        # Meta info
        last_update = None
        if wines_rows:
            # Trova ultimo updated_at
            last_update_row = max(wines_rows, key=lambda w: w['updated_at'] if w['updated_at'] else datetime.min)
            last_update = last_update_row['updated_at'].isoformat() if last_update_row['updated_at'] else datetime.utcnow().isoformat()
        else:
            last_update = datetime.utcnow().isoformat()
        
        response = {
            "rows": rows,
            "facets": facets,
            "meta": {
                "total_rows": len(rows),
                "last_update": last_update
            }
        }
        
        logger.info(
            f"[VIEWER_DB] Snapshot recuperato: rows={len(rows)}, "
            f"telegram_id={telegram_id}, business_name={business_name}, "
            f"facets_type_count={len(facets.get('type', {}))}, "
            f"facets_vintage_count={len(facets.get('vintage', {}))}, "
            f"facets_winery_count={len(facets.get('winery', {}))}"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"[VIEWER_DB] Errore recupero snapshot: {e}", exc_info=True)
        raise
    finally:
        if conn:
            await conn.close()

