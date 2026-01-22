from js import Response
import json

async def handle_upload(request, env):
    """
    Placeholder para o handler de upload.
    Demonstra acesso ao binding R2.
    """
    # env.agems_docs é o binding R2
    r2_bucket = env.agems_docs
    
    return Response.json({
        "message": "Upload handler placeholder. R2 binding (agems_docs) acessado com sucesso.",
        "bucket_name": r2_bucket.name # Acesso a uma propriedade do binding para validação
    }, status=200)