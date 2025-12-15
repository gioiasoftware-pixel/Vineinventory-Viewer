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
# OBBLIGATORIA: Deve essere configurata su Railway → Settings → Variables
# Deve essere la STESSA chiave del bot!
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"

# Verifica configurazione all'avvio
if not DATABASE_URL:
    logger.error("[VIEWER_DB] ❌ DATABASE_URL non configurata! Il viewer non funzionerà.")
    logger.error("[VIEWER_DB] Configura DATABASE_URL su Railway → Settings → Variables")

if not JWT_SECRET_KEY:
    logger.error("[VIEWER_DB] ❌ JWT_SECRET_KEY non configurata!")
    logger.error("[VIEWER_DB] Configura JWT_SECRET_KEY su Railway → Settings → Variables")
    logger.error("[VIEWER_DB] Deve essere la STESSA chiave del bot!")
    logger.error("[VIEWER_DB] Il viewer non funzionerà senza questa variabile!")
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
        
        # Recupera tutti i vini con tutti i campi disponibili
        wines_query = f"""
            SELECT 
                id,
                name,
                producer,
                supplier,
                vintage,
                quantity,
                selling_price,
                cost_price,
                wine_type,
                grape_variety,
                region,
                country,
                classification,
                alcohol_content,
                description,
                notes,
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
            # Normalizza tipo vino per consistenza (come nei facets)
            wine_type = wine['wine_type'] or "Altro"
            wine_type_normalized = wine_type.strip()
            if wine_type_normalized:
                wine_type_normalized = wine_type_normalized[0].upper() + wine_type_normalized[1:].lower()
            else:
                wine_type_normalized = "Altro"
            
            # Normalizza winery (producer) - escludi valori vuoti/null
            winery_value = wine['producer']
            if winery_value:
                winery_normalized = winery_value.strip()
                if not winery_normalized or winery_normalized.lower() in ("null", "none"):
                    winery_normalized = "-"
            else:
                winery_normalized = "-"
            
            # Normalizza supplier (escludi valori vuoti/null)
            supplier_value = wine['supplier']
            if supplier_value:
                supplier_normalized = supplier_value.strip()
                if not supplier_normalized or supplier_normalized.lower() in ("null", "none"):
                    supplier_normalized = "-"
            else:
                supplier_normalized = "-"
            
            rows.append({
                "id": wine['id'],  # ID necessario per editing
                "name": wine['name'] or "-",
                "winery": winery_normalized,
                "supplier": supplier_normalized,
                "vintage": wine['vintage'],
                "qty": wine['quantity'] or 0,
                "price": float(wine['selling_price']) if wine['selling_price'] else 0.0,
                "cost_price": float(wine['cost_price']) if wine.get('cost_price') else None,
                "type": wine_type_normalized,
                "grape_variety": wine.get('grape_variety'),
                "region": wine.get('region'),
                "country": wine.get('country'),
                "classification": wine.get('classification'),
                "alcohol_content": float(wine['alcohol_content']) if wine.get('alcohol_content') else None,
                "description": wine.get('description'),
                "notes": wine.get('notes'),
                "min_quantity": wine.get('min_quantity'),
                "critical": wine['quantity'] is not None and wine['min_quantity'] is not None and wine['quantity'] <= wine['min_quantity']
            })
        
        # Calcola facets (aggregazioni per filtri)
        facets = {
            "type": {},
            "vintage": {},
            "winery": {},
            "supplier": {}
        }
        
        for wine in wines_rows:
            # Tipo - normalizza per evitare duplicati (trim + capitalize)
            wine_type = wine['wine_type'] or "Altro"
            wine_type_normalized = wine_type.strip()
            # Capitalizza prima lettera per consistenza (es. "spumante" -> "Spumante")
            if wine_type_normalized:
                wine_type_normalized = wine_type_normalized[0].upper() + wine_type_normalized[1:].lower()
            else:
                wine_type_normalized = "Altro"
            facets["type"][wine_type_normalized] = facets["type"].get(wine_type_normalized, 0) + 1
            
            # Annata - normalizza come stringa per matching consistente
            if wine['vintage'] is not None:
                vintage_str = str(wine['vintage']).strip()
                if vintage_str:  # Solo se non vuoto dopo strip
                    facets["vintage"][vintage_str] = facets["vintage"].get(vintage_str, 0) + 1
            
            # Cantina (producer) - normalizza per matching case-insensitive
            if wine['producer']:
                producer_normalized = wine['producer'].strip()
                # Escludi valori vuoti o placeholder
                if producer_normalized and producer_normalized not in ("-", "", "null", "None"):
                    facets["winery"][producer_normalized] = facets["winery"].get(producer_normalized, 0) + 1
            
            # Fornitore (supplier) - normalizza per evitare duplicati
            if wine['supplier']:
                supplier_normalized = wine['supplier'].strip()
                # Escludi valori vuoti o placeholder
                if supplier_normalized and supplier_normalized not in ("-", "", "null", "None"):
                    facets["supplier"][supplier_normalized] = facets["supplier"].get(supplier_normalized, 0) + 1
        
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


async def get_wine_movements(telegram_id: int, business_name: str, wine_name: str) -> List[Dict[str, Any]]:
    """
    Recupera movimenti (consumi e rifornimenti) per un vino specifico.
    
    Args:
        telegram_id: ID Telegram utente
        business_name: Nome business
        wine_name: Nome del vino
        
    Returns:
        Lista di movimenti con date e quantità
    """
    conn = None
    try:
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL non configurata")
        
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Trova user_id
        user_row = await conn.fetchrow(
            "SELECT id FROM users WHERE telegram_id = $1",
            telegram_id
        )
        
        if not user_row:
            logger.warning(f"[VIEWER_DB] Utente {telegram_id} non trovato")
            return []
        
        user_id = user_row['id']
        
        # Nome tabella consumi
        table_consumi = f'"{telegram_id}/{business_name} Consumi e rifornimenti"'
        
        # Query movimenti per questo vino
        movements_rows = await conn.fetch(
            f"""
            SELECT 
                movement_type,
                quantity_change,
                quantity_before,
                quantity_after,
                movement_date
            FROM {table_consumi}
            WHERE user_id = $1
            AND wine_name = $2
            ORDER BY movement_date ASC
            """,
            user_id,
            wine_name
        )
        
        # Formatta movimenti
        movements = []
        for mov in movements_rows:
            movements.append({
                "date": mov['movement_date'].isoformat() if mov['movement_date'] else None,
                "type": mov['movement_type'],  # 'consumo' o 'rifornimento'
                "quantity_change": mov['quantity_change'],
                "quantity_before": mov['quantity_before'],
                "quantity_after": mov['quantity_after']
            })
        
        logger.info(
            f"[VIEWER_DB] Movimenti recuperati per vino '{wine_name}': "
            f"count={len(movements)}, telegram_id={telegram_id}"
        )
        
        return movements
        
    except Exception as e:
        logger.error(f"[VIEWER_DB] Errore recupero movimenti: {e}", exc_info=True)
        raise
    finally:
        if conn:
            await conn.close()


async def update_wine_field(
    telegram_id: int,
    business_name: str,
    wine_id: int,
    field: str,
    value: str
) -> Dict[str, Any]:
    """
    Aggiorna un singolo campo per un vino dell'inventario direttamente nel database.
    
    Args:
        telegram_id: Telegram ID dell'utente
        business_name: Nome del business
        wine_id: ID del vino da aggiornare
        field: Nome del campo da aggiornare
        value: Nuovo valore (come stringa, verrà convertito in base al campo)
        
    Returns:
        Dict con risultato aggiornamento
        
    Raises:
        ValueError: Se campo non supportato o valore non valido
        Exception: Se vino non trovato o errore database
    """
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL non configurata")
    
    # Campi supportati (stesso set del processor)
    allowed_fields = {
        'producer': 'producer',
        'supplier': 'supplier',
        'vintage': 'vintage',
        'grape_variety': 'grape_variety',
        'classification': 'classification',
        'selling_price': 'selling_price',
        'cost_price': 'cost_price',
        'alcohol_content': 'alcohol_content',
        'description': 'description',
        'notes': 'notes',
    }
    
    if field not in allowed_fields:
        raise ValueError(
            f"Campo non consentito: {field}. "
            f"Campi supportati: {', '.join(allowed_fields.keys())}"
        )
    
    # Normalizza tipi per alcuni campi (stessa logica del processor)
    def cast_value(f: str, v: str):
        if f == 'vintage':
            try:
                parsed = int(v)
                if parsed < 1800 or parsed > 2100:
                    raise ValueError(f"Anno non valido: {parsed}")
                return parsed
            except (ValueError, TypeError):
                raise ValueError(f"Anno non valido per {f}: '{v}'")
        if f in ('selling_price', 'cost_price', 'alcohol_content'):
            try:
                parsed = float(str(v).replace(',', '.'))
                if f == 'alcohol_content' and (parsed < 0 or parsed > 100):
                    raise ValueError(f"Gradazione alcolica non valida: {parsed}%")
                if f in ('selling_price', 'cost_price') and parsed < 0:
                    raise ValueError(f"Prezzo non può essere negativo: {parsed}")
                return parsed
            except (ValueError, TypeError):
                raise ValueError(f"Numero non valido per {f}: '{v}'")
        # Per stringhe, rimuovi spazi eccessivi
        return str(v).strip() if v else None
    
    column = allowed_fields[field]
    new_value = cast_value(field, value)
    
    conn = None
    try:
        # Connetti al database
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Verifica che utente esista
        user_query = "SELECT id FROM users WHERE telegram_id = $1"
        user_row = await conn.fetchrow(user_query, telegram_id)
        
        if not user_row:
            raise ValueError(f"Utente con telegram_id {telegram_id} non trovato")
        
        user_id = user_row['id']
        
        # Nome tabella inventario
        table_name = f'"{telegram_id}/{business_name} INVENTARIO"'
        
        # Verifica che il vino esista
        check_query = f"""
            SELECT id FROM {table_name}
            WHERE id = $1 AND user_id = $2
        """
        wine_check = await conn.fetchrow(check_query, wine_id, user_id)
        
        if not wine_check:
            raise ValueError(f"Vino con id {wine_id} non trovato")
        
        # Aggiorna campo
        update_query = f"""
            UPDATE {table_name}
            SET {column} = $1, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2 AND user_id = $3
            RETURNING id, {column}
        """
        
        updated_row = await conn.fetchrow(update_query, new_value, wine_id, user_id)
        
        if not updated_row:
            raise ValueError("Vino non trovato dopo aggiornamento")
        
        logger.info(
            f"[VIEWER_DB] Campo aggiornato: {field} = {new_value} per wine_id={wine_id}, "
            f"telegram_id={telegram_id}, business_name={business_name}"
        )
        
        return {
            "status": "success",
            "wine_id": wine_id,
            "field": field,
            "value": new_value,
            "message": f"Campo {field} aggiornato con successo"
        }
        
    except Exception as e:
        logger.error(
            f"[VIEWER_DB] Errore aggiornamento campo: {e}",
            exc_info=True
        )
        raise
    finally:
        if conn:
            await conn.close()

