"""
Arquivo WSGI para deploy no PythonAnywhere
"""

import sys
import os

# Adicionar o diretório do projeto ao path
path = 'c:/Users/genez/ceitec_hub'  # Ajustado para o caminho local atual
if path not in sys.path:
    sys.path.insert(0, path)

# Configurar variáveis de ambiente
os.environ['SECRET_KEY'] = 'ceitec-hub-secret-key-2024-prod'

from app import app as application

# Inicializar banco de dados na primeira execução
from models import Database
db = Database(os.path.join(path, 'database.db'))

# Garantir que as tabelas existam
try:
    db.init_db()
except:
    pass
