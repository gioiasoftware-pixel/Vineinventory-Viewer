#!/usr/bin/env python3
"""Server HTTP semplice per viewer statico"""
import http.server
import socketserver
import os
import sys

PORT = int(os.getenv("PORT", 8080))
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def do_GET(self):
        """Gestisci richieste GET"""
        # Se richiesta root, serve index.html con configurazione iniettata
        if self.path == '/' or self.path == '':
            self.path = '/index.html'
            self.serve_index_with_config()
            return
        
        # Serve file statici
        return super().do_GET()
    
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
            config_script = f'''
<script>
    // Configurazione iniettata dal server
    window.VIEWER_CONFIG = {{
        apiBase: "{api_base}"
    }};
</script>
'''
            
            # Inserisci lo script prima di </head>
            if '</head>' in content:
                content = content.replace('</head>', config_script + '</head>')
            else:
                # Se non c'è </head>, inserisci prima di <body>
                content = content.replace('<body>', config_script + '<body>')
            
            # Invia risposta
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
            
        except Exception as e:
            sys.stderr.write(f"Errore servendo index.html: {e}\n")
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
        # Log solo su stderr per Railway
        sys.stderr.write(f"{self.address_string()} - {format % args}\n")

if __name__ == "__main__":
    # Log su stderr per Railway
    sys.stderr.write(f"🍷 Vineinventory Viewer server avviato su porta {PORT}\n")
    sys.stderr.write(f"📁 Directory: {DIRECTORY}\n")
    sys.stderr.write(f"📄 Index file: {os.path.join(DIRECTORY, 'index.html')}\n")
    
    # Verifica che index.html esista
    index_path = os.path.join(DIRECTORY, 'index.html')
    if not os.path.exists(index_path):
        sys.stderr.write(f"❌ ERRORE: index.html non trovato in {index_path}\n")
        sys.exit(1)
    
    sys.stderr.write(f"✅ index.html trovato\n")
    
    try:
        # Permetti riuso indirizzo per evitare "Address already in use"
        socketserver.TCPServer.allow_reuse_address = True
        
        with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
            sys.stderr.write(f"✅ Server pronto su http://0.0.0.0:{PORT}\n")
            sys.stderr.write(f"🚀 In ascolto su porta {PORT}...\n")
            httpd.serve_forever()
    except OSError as e:
        sys.stderr.write(f"❌ Errore porta {PORT}: {e}\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"❌ Errore avvio server: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

