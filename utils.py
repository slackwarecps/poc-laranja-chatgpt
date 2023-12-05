def filter_assistants(items):
    # Filtrar a lista para incluir apenas os itens com role="assistant"
    assistants = [item for item in items if item.get('role') == "assistant"]
    return assistants