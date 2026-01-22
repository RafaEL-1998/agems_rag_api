def validate_upload(form_data):
    """Valida dados de upload"""
    required_fields = ['file', 'title', 'type', 'sector']
    
    for field in required_fields:
        if not form_data.get(field):
            return False, f"Missing required field: {field}"
    
    # Validar tipo de arquivo
    file = form_data.get('file')
    if not file.name.endswith('.pdf'):
        return False, "Only PDF files are supported"
    
    return True, None

def validate_query(body):
    """Valida dados de consulta"""
    if not body.get('query'):
        return False, "Query is required"
    
    query = body.get('query')
    if len(query) < 3:
        return False, "Query too short (minimum 3 characters)"
    
    if len(query) > 1000:
        return False, "Query too long (maximum 1000 characters)"
    
    return True, None