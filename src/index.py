import sys
import os

# Adiciona a pasta vendor ao path de busca do Python
vendor_path = os.path.join(os.path.dirname(__file__), 'vendor')
sys.path.insert(0, vendor_path)

from js import Response, Object, Headers
from pyodide.ffi import to_js
import json

# Importar handlers
from handlers.upload import handle_upload
from handlers.chunks import handle_add_chunks, handle_process
from handlers.query import handle_query


async def on_fetch(request, env):
    """
    Entry point principal do Worker.
    Roteia requisições para os handlers apropriados.
    """
    
    url = request.url
    method = request.method
    
    # Roteamento simples
    if "/documents/upload" in url and method == "POST":
        return await handle_upload(request, env)
    
    elif "/documents/" in url and "/chunks" in url and method == "POST":
        return await handle_add_chunks(request, env)
    
    elif "/documents/" in url and "/process" in url and method == "POST":
        return await handle_process(request, env)
    
    elif "/chat/query" in url and method == "POST":
        return await handle_query(request, env)
    
    elif method == "GET":
        return Response.new(
            json.dumps({
                "service": "AGEMS IA Regulatória",
                "url": url,
                "status": "online"
            }),
            to_js({"headers": {"Content-Type": "application/json"}})
        )
    
    else:
        from js import JSON
        init = JSON.parse(json.dumps({
            "status": 404,
            "headers": {"Content-Type": "application/json"}
        }))
        return Response.new(json.dumps({"error": "Endpoint not found"}), init)





