import sys
import os

# Adiciona a pasta vendor ao path de busca do Python
vendor_path = os.path.join(os.path.dirname(__file__), 'vendor')
sys.path.insert(0, vendor_path)

from js import Response
import json

# Importar handlers
from handlers.upload import handle_upload
from handlers.process import handle_process
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
    
    elif "/documents/" in url and "/process" in url and method == "POST":
        return await handle_process(request, env)
    
    elif "/chat/query" in url and method == "POST":
        return await handle_query(request, env)
    
    elif method == "GET" and url.endswith("/"):
        return Response.json({
            "service": "AGEMS IA Regulatória",
            "version": "1.0.0",
            "status": "online"
        })
    
    else:
        return Response.json(
            {"error": "Endpoint not found"},
            status=404
        )