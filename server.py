#!/usr/bin/env python3
"""Server HTTP semplice per viewer statico"""
import http.server
import socketserver
import os
import sys
import json
import asyncio
import logging
from urllib.parse import urlparse, parse_qs
from logging_config import setup_colored_logging

# Configurazione logging colorato
setup_colored_logging("viewer")
logger = logging.getLogger(__name__)

PORT = int(os.getenv("PORT", 8080))
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def do_GET(self):
        """Gestisci richieste GET"""
        parsed_path = urlparse(self.path)
        
        # Endpoint API per generazione viewer
        if parsed_path.path == '/api/generate':
            self.handle_generate_endpoint()
            return
        
        # Endpoint per servire HTML dalla cache
        if parsed_path.path.startswith('/') and 'view_id' in parse_qs(parsed_path.query):
            query_params = parse_qs(parsed_path.query)
            view_id = query_params.get('view_id', [None])[0]
            if view_id:
                self.serve_html_from_cache(view_id)
                return
        
        # Se richiesta root, serve index.html con configurazione iniettata
        if self.path == '/' or self.path == '':
            self.path = '/index.html'
            self.serve_index_with_config()
            return
        
        # Serve file statici
        return super().do_GET()
    
    def do_POST(self):
        """Gestisci richieste POST"""
        parsed_path = urlparse(self.path)
        
        # Endpoint API per generazione viewer
        if parsed_path.path == '/api/generate':
            self.handle_generate_endpoint()
            return
        
        self.send_error(404, "Not found")
    
    def serve_index_with_config(self):
        """Serve index.html con configurazione API iniettata"""
        try:
            index_path = os.path.join(DIRECTORY, 'index.html')
            if not os.path.exists(index_path):
                self.send_error(404, "File not found")
                return
            
            # Leggi index.html
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Leggi API_BASE da variabile ambiente (default se non configurata)
            api_base = os.getenv('API_BASE', 'https://gioia-processor-production.up.railway.app')
            
            # Inietta configurazione JavaScript prima della chiusura di </head>
            # IMPORTANTE: Deve essere PRIMA di app.js per essere disponibile
            config_script = f'''
<script>
    // Configurazione iniettata dal server (deve essere PRIMA di app.js)
    window.VIEWER_CONFIG = {{
        apiBase: "{api_base}"
    }};
    console.log("[VIEWER_CONFIG] Configurazione iniettata:", window.VIEWER_CONFIG);
</script>
'''
            
            # Inserisci lo script prima di </head> (deve essere prima di app.js)
            if '</head>' in content:
                # Inserisci prima dell'ultima riga di </head>
                content = content.replace('</head>', config_script + '</head>')
            elif '<script' in content:
                # Se non c'è </head>, inserisci prima del primo script
                first_script_pos = content.find('<script')
                content = content[:first_script_pos] + config_script + content[first_script_pos:]
            else:
                # Ultimo fallback: prima di <body>
                content = content.replace('<body>', config_script + '<body>')
            
            logger.info(f"[SERVER] Configurazione iniettata: apiBase={api_base}")
            
            # Invia risposta
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"[SERVER] Errore servendo index.html: {e}", exc_info=True)
            self.send_error(500, f"Internal server error: {e}")
    
    def handle_generate_endpoint(self):
        """Gestisci endpoint POST /api/generate"""
        try:
            # Leggi body JSON
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, "Body vuoto")
                return
            
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            telegram_id = data.get('telegram_id')
            business_name = data.get('business_name')
            correlation_id = data.get('correlation_id')
            
            if not telegram_id or not business_name:
                self.send_error(400, "telegram_id e business_name richiesti")
                return
            
            # Esegui generazione asincrona
            logger.info(
                f"[VIEWER_API] Richiesta generazione per telegram_id={telegram_id}, "
                f"business_name={business_name}, correlation_id={correlation_id}"
            )
            
            # Importa e esegui generazione
            from api_generate import generate_viewer_html
            
            # Esegui async in modo sincrono (per HTTP server)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    generate_viewer_html(telegram_id, business_name, correlation_id)
                )
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
                
                logger.info(
                    f"[VIEWER_API] Generazione completata: view_id={result.get('view_id')}, "
                    f"telegram_id={telegram_id}, correlation_id={correlation_id}"
                )
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"[VIEWER_API] Errore generazione: {e}", exc_info=True)
            self.send_error(500, f"Internal server error: {e}")
    
    def serve_html_from_cache(self, view_id: str):
        """Serve HTML dalla cache"""
        try:
            from api_generate import get_viewer_html_from_cache
            
            html, found = get_viewer_html_from_cache(view_id)
            
            if not found:
                logger.warning(f"[VIEWER_CACHE] View ID {view_id} non trovato")
                self.send_error(404, "View non trovata o scaduta")
                return
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            
            logger.info(f"[VIEWER_CACHE] HTML servito per view_id={view_id}, length={len(html)}")
            
        except Exception as e:
            logger.error(f"[VIEWER_CACHE] Errore servendo HTML: {e}", exc_info=True)
            self.send_error(500, f"Internal server error: {e}")
    
    def end_headers(self):
        # Headers CORS se necessario (per chiamate API)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        # Cache headers per static files
        self.send_header('Cache-Control', 'public, max-age=3600')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Gestisci preflight requests per CORS"""
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, format, *args):
        """Override per logging più pulito"""
        # Log usando logger invece di sys.stderr
        logger.debug(f"{self.address_string()} - {format % args}")

if __name__ == "__main__":
    logger.info(f"🍷 Vineinventory Viewer server avviato su porta {PORT}")
    logger.info(f"📁 Directory: {DIRECTORY}")
    logger.info(f"📄 Index file: {os.path.join(DIRECTORY, 'index.html')}")
    
    # Verifica che index.html esista
    index_path = os.path.join(DIRECTORY, 'index.html')
    if not os.path.exists(index_path):
        logger.error(f"❌ ERRORE: index.html non trovato in {index_path}")
        sys.exit(1)
    
    logger.info(f"✅ index.html trovato")
    
    try:
        # Permetti riuso indirizzo per evitare "Address already in use"
        socketserver.TCPServer.allow_reuse_address = True
        
        with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
            logger.info(f"✅ Server pronto su http://0.0.0.0:{PORT}")
            logger.info(f"🚀 In ascolto su porta {PORT}...")
            httpd.serve_forever()
    except OSError as e:
        logger.error(f"❌ Errore porta {PORT}: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Errore avvio server: {e}", exc_info=True)
        sys.exit(1)

