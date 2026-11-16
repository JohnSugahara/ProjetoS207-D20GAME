# D20 Arena

O D20 Arena é um torneio de duelos de dados. Cada jogador entra no torneio, recebe uma classe sorteada e enfrenta os outros no chaveamento rolando um d20. Quem vence avança de rodada e desbloqueia uma nova habilidade.

Fizemos o projeto para a disciplina de Qualidade de Software. Por isso, além do jogo, ele tem testes automatizados com cobertura mínima de 90%, roda em containers com Docker Compose e tem um pipeline no Jenkins que testa, empacota e manda o resultado por e-mail.

**Stack:** Python 3.12, FastAPI, SQLAlchemy, PostgreSQL/SQLite, Pytest, Docker, Jenkins e Mailpit.

**Docker hub - Imagem link:** https://hub.docker.com/repository/docker/johnsugahara/d20-arena-jenkins/general

---

## Instalação

Você vai precisar de **Python 3.12+**, **Git** e, se quiser rodar com containers, **Docker** com **Docker Compose**.

Clone o repositório:

```bash
git clone https://github.com/JohnSugahara/ProjetoS207-D20GAME.git
cd ProjetoS207-D20GAME
```

Para rodar localmente, crie um ambiente virtual e instale as dependências:

```bash
python -m venv .venv
```

```bash
# Linux/macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

```bash
pip install -r requirements-dev.txt
```

O `requirements-dev.txt` já inclui o `requirements.txt` da aplicação e acrescenta as ferramentas de teste (`pytest`, `pytest-cov` e `httpx`).

Para rodar com Docker, copie o arquivo de exemplo e preencha os valores:

```bash
cp .env.example .env
```

O `.env` guarda as credenciais do Postgres, o usuário e a senha de admin do Jenkins, a URL do repositório que o Jenkins vai clonar, o e-mail que recebe as notificações e os dados do servidor SMTP (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`). Se usar o Gmail, gere uma *senha de app* em vez de usar a senha da conta. O `.env` não deve ser versionado.

---

## Execução

### Localmente

```bash
uvicorn app.main:app --reload
```

Sem a variável `DATABASE_URL`, a aplicação cria sozinha um banco SQLite (`d20_arena.db`). Depois disso, é só abrir:

- http://localhost:8000: interface do jogo
- http://localhost:8000/docs: documentação da API (Swagger)
- http://localhost:8000/health: health check

### Com Docker Compose

```bash
docker compose up -d --build
```

Esse comando sobe quatro containers:

- **app** (http://localhost:8000): a aplicação, construída a partir do `Dockerfile` local
- **postgres**: o banco de dados
- **jenkins** (http://localhost:8080): o pipeline de CI/CD
- **mailpit** (http://localhost:8025): uma caixa de entrada de teste

A aplicação só sobe depois que o Postgres passa no health check. Para derrubar tudo, use `docker compose down`. Os dados do banco e do Jenkins ficam em volumes; se quiser apagá-los também, use `docker compose down -v`.

### Testes

```bash
pytest
```

Para ver a cobertura do mesmo jeito que o pipeline:

```bash
pytest --cov=app --cov=scripts --cov-report=term-missing --cov-report=html:htmlcov --cov-fail-under=90
```

O relatório em HTML fica em `htmlcov/index.html`.

### Imagem do Jenkins

O Compose baixa a imagem do Jenkins do Docker Hub. Ela é gerada a partir de `jenkins/Dockerfile` e já vem com Python, zip, git, os plugins de `plugins.txt` e toda a configuração em `casc.yaml`. Para gerar e publicar uma nova versão:

```bash
docker build -t <DOCKERHUB_USER>/d20-arena-jenkins:1.0 jenkins/
```

```bash
docker push <DOCKERHUB_USER>/d20-arena-jenkins:1.0
```

---