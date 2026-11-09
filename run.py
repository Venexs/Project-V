from modules.memory import rebuild_memory_index, rebuild_semantic_index, rebuild_memory_graph
from modules.knowledge import rebuild_knowledge_index, rebuild_knowledge_embeddings
print('Building indices...')
rebuild_memory_index()
rebuild_semantic_index()
rebuild_memory_graph()
rebuild_knowledge_index()
rebuild_knowledge_embeddings()
print('Done.')