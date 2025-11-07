"""Utility per accesso al database PostgreSQL.

Il viewer utilizza una connessione sincrona (psycopg2) perché il server HTTP
è sincrono. Tutte le query vengono eseguite in modo bloccante, quindi eventuali
chiamate da coroutine devono essere delegate a `asyncio.to_thread`.
"""

from __future__ import annotations

import os
import logging
from datetime import datetime
from typing import Dict, Any

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


def _get_database_url() -> str:
    """Recupera e normalizza l'URL del database."""
    database_url = os.getenv("DATABASE_URL", "").strip()

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL non configurata per il viewer."
        )

    # Compatibilità Railway: postgres:// -> postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    return database_url


def get_connection():
    """Restituisce una nuova connessione al database."""
    database_url = _get_database_url()
    logger.debug("[DB] Apertura nuova connessione al database viewer")
    return psycopg2.connect(database_url)


def get_inventory_table_name(telegram_id: int, business_name: str | None) -> sql.Identifier:
    """Restituisce l'identificatore della tabella inventario per l'utente."""
    if not business_name:
        business_name = "Upload Manuale"

    table_name = f"{telegram_id}/{business_name} INVENTARIO"
    return sql.Identifier(table_name)


def fetch_inventory_data_from_db(
    telegram_id: int,
    business_name: str | None,
    correlation_id: str | None = None
) -> Dict[str, Any]:
    """
    Estrae i dati dell'inventario dal database e li formatta per il viewer.

    Returns:
        Dict con chiavi `rows`, `facets`, `meta`.
    """

    connection = None
    try:
        connection = get_connection()
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            logger.info(
                "[DB] Estrazione inventario: telegram_id=%s, business_name=%s, correlation_id=%s",
                telegram_id,
                business_name,
                correlation_id,
            )

            cursor.execute(
                "SELECT id FROM users WHERE telegram_id = %s",
                (telegram_id,),
            )
            user_row = cursor.fetchone()
            if not user_row:
                logger.warning(
                    "[DB] Utente non trovato per telegram_id=%s, correlation_id=%s",
                    telegram_id,
                    correlation_id,
                )
                return _empty_inventory()

            user_id = user_row["id"]
            table_identifier = get_inventory_table_name(telegram_id, business_name)

            query = sql.SQL(
                """
                SELECT
                    name,
                    producer,
                    vintage,
                    quantity,
                    selling_price,
                    wine_type,
                    min_quantity,
                    region,
                    country,
                    grape_variety,
                    classification,
                    supplier,
                    cost_price,
                    alcohol_content,
                    description,
                    notes,
                    updated_at
                FROM {table}
                WHERE user_id = %s
                ORDER BY name NULLS LAST, vintage NULLS LAST
                """
            ).format(table=table_identifier)

            try:
                cursor.execute(query, (user_id,))
                wines_rows = cursor.fetchall()
            except psycopg2.errors.UndefinedTable:
                logger.warning(
                    "[DB] Tabella inventario non trovata per telegram_id=%s, business_name=%s",
                    telegram_id,
                    business_name,
                )
                return _empty_inventory()

        rows = []
        facets_type: Dict[str, int] = {}
        facets_vintage: Dict[str, int] = {}
        facets_winery: Dict[str, int] = {}

        last_update = datetime.utcnow()

        for wine in wines_rows:
            name = wine.get("name") or "-"
            winery = wine.get("producer") or "-"
            vintage = wine.get("vintage")
            quantity = wine.get("quantity") or 0
            price = float(wine.get("selling_price")) if wine.get("selling_price") else 0.0
            wine_type = wine.get("wine_type") or "Altro"
            min_quantity = wine.get("min_quantity")
            updated_at = wine.get("updated_at") or last_update
            region = wine.get("region")
            country = wine.get("country")
            grape_variety = wine.get("grape_variety")
            classification = wine.get("classification")
            supplier = wine.get("supplier")
            cost_price_raw = wine.get("cost_price")
            cost_price = float(cost_price_raw) if cost_price_raw is not None else None
            alcohol_raw = wine.get("alcohol_content")
            alcohol = float(alcohol_raw) if alcohol_raw is not None else None
            description = wine.get("description")
            notes = wine.get("notes")

            row = {
                "name": name,
                "winery": winery,
                "vintage": vintage,
                "qty": quantity,
                "price": price,
                "type": wine_type,
                "critical": (
                    min_quantity is not None
                    and quantity is not None
                    and quantity <= min_quantity
                ),
                "min_qty": min_quantity,
                "region": region,
                "country": country,
                "grape_variety": grape_variety,
                "classification": classification,
                "supplier": supplier,
                "cost_price": cost_price,
                "alcohol_content": alcohol,
                "description": description,
                "notes": notes,
                "updated_at": updated_at.isoformat() if updated_at else None,
            }
            rows.append(row)

            facets_type[wine_type] = facets_type.get(wine_type, 0) + 1

            if vintage:
                vintage_key = str(vintage)
                facets_vintage[vintage_key] = facets_vintage.get(vintage_key, 0) + 1

            if winery and winery != "-":
                facets_winery[winery] = facets_winery.get(winery, 0) + 1

            if updated_at and updated_at > last_update:
                last_update = updated_at

        data = {
            "rows": rows,
            "facets": {
                "type": facets_type,
                "vintage": facets_vintage,
                "winery": facets_winery,
            },
            "meta": {
                "total_rows": len(rows),
                "last_update": (last_update or datetime.utcnow()).isoformat(),
            },
        }

        logger.info(
            "[DB] Inventario estratto: rows=%s, telegram_id=%s, correlation_id=%s",
            len(rows),
            telegram_id,
            correlation_id,
        )

        return data

    except Exception as exc:
        logger.error(
            "[DB] Errore durante l'estrazione inventario: %s", exc, exc_info=True
        )
        raise
    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                logger.warning("[DB] Errore chiusura connessione", exc_info=True)


def _empty_inventory() -> Dict[str, Any]:
    """Restituisce struttura vuota compatibile con il viewer."""
    now = datetime.utcnow().isoformat()
    return {
        "rows": [],
        "facets": {
            "type": {},
            "vintage": {},
            "winery": {},
        },
        "meta": {
            "total_rows": 0,
            "last_update": now,
        },
    }


