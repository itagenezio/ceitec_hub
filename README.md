# CEITEC HUB - Plataforma Educacional Integrada

## Descrição
Este é o CEITEC HUB, uma plataforma desenvolvida para o Centro de Inovação em Tecnologia e Educação do Ceará. A plataforma inclui módulos de:
- Competição Matemática
- Avaliação de Texto com IA (Motor Interno)
- Clube de Robótica (Galeria de Projetos)
- Relatórios de Desempenho

## Estrutura do Projeto
- `app.py`: Ponto de entrada da aplicação Flask.
- `models.py`: Lógica do banco de dados SQLite.
- `static/`: Arquivos estáticos (CSS, JS, Imagens).
- `templates/`: Templates HTML (Jinja2).

## Como Executar Localmente
1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Inicie a aplicação:
   ```bash
   python app.py
   ```
3. Acesse `http://localhost:5000` no seu navegador.

## Deploy no PythonAnywhere
Consulte o arquivo `wsgi.py` para configurações de deploy.
