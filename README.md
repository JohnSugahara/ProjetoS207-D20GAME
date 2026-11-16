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
- **mailpit** (http://localhost:8025): uma caixa de entrada de teste  (Mais tarde alterado para acessar emails de verdade, mas ainda funcional se mudar o .env)

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

## Uso

### Jogando pela interface

1. Abra http://localhost:8000 e crie um torneio, ou escolha um que já existe.
2. Digite o nome de cada jogador e clique em **Sortear carta**. A classe é sorteada na hora. São de 2 a 32 jogadores por torneio. Enquanto o torneio não começa, dá para tirar alguém da lista clicando no **×** ao lado do nome.
3. Clique em **Iniciar torneio** para montar o chaveamento.
4. Role os duelos um por vez (**Rolar próximo duelo**), a rodada inteira de uma vez (**Rolar rodada inteira**) ou tudo até sair o campeão (**Rolar torneio inteiro**). Esse último também funciona com o torneio ainda aberto: ele inicia e já resolve todos os duelos.
5. Em cada confronto, **Ver rolagens** mostra o log com as rolagens e as habilidades que entraram em jogo. No final, o campeão aparece no centro da chave.
6. Para jogar de novo com o mesmo grupo, clique em **Reiniciar torneio**. Os jogadores e as classes continuam, mas o chaveamento e o progresso são apagados. Depois disso, dá para inscrever mais gente e iniciar outra vez.

Nos campos de texto, apertar **Enter** tem o mesmo efeito de clicar no botão ao lado.

### Usando a API

| Método | Rota | O que faz |
|---|---|---|
| `GET` | `/api/classes` | Lista as classes e as habilidades |
| `GET` | `/api/tournaments` | Lista os torneios |
| `POST` | `/api/tournaments` | Cria um torneio: `{"name": "...", "unlock_abilities": true}` |
| `GET` | `/api/tournaments/{id}` | Mostra o torneio com os participantes e os confrontos |
| `POST` | `/api/tournaments/{id}/join` | Inscreve um jogador: `{"name": "..."}` |
| `DELETE` | `/api/tournaments/{id}/entries/{entry_id}` | Remove um participante (só antes de iniciar) |
| `POST` | `/api/tournaments/{id}/start` | Inicia o torneio |
| `POST` | `/api/tournaments/{id}/reset` | Reinicia um torneio em andamento ou terminado |
| `POST` | `/api/matches/{id}/roll` | Rola o duelo de um confronto |

Por exemplo:

```bash
curl -X POST http://localhost:8000/api/tournaments -H "Content-Type: application/json" -d '{"name": "Copa D20"}'
```

### Pipeline no Jenkins

Quando o Jenkins sobe, ele já cria o job `d20-arena`, que confere o repositório a cada 5 minutos. O `Jenkinsfile` tem quatro etapas:

1. **Preparar ambiente:** cria o venv e instala as dependências.
2. **Testes:** roda o pytest e reprova o build se a cobertura ficar abaixo de 90%. Os relatórios JUnit e de cobertura ficam arquivados.
3. **Build/Pacote:** gera o `dist/d20-arena-<build>.zip`.
4. **Notificar:** o `scripts/send_email.py` manda um e-mail para `NOTIFY_EMAIL` com o status, a cobertura e o link do build. Se alguma etapa falhar, sai um e-mail de **FAILURE**.

---

## Funcionalidades

### O torneio

- O chaveamento é de eliminatória simples, com a ordem dos jogadores embaralhada. Ele é desenhado no formato de Copa: metade dos confrontos de cada lado, com a final no centro.
- Quando o número de jogadores não é potência de 2, alguns avançam direto por **bye**.
- O vencedor de cada duelo vai sozinho para a próxima rodada.
- Não pode haver dois jogadores com o mesmo nome no mesmo torneio.
- Participantes podem ser removidos antes do início, o que libera o nome e a vaga.
- Dá para resolver o torneio inteiro de uma vez, sem rolar duelo por duelo.
- Dá para criar torneios com o desbloqueio de habilidades desligado.
- Um torneio em andamento ou terminado pode ser reiniciado sem precisar cadastrar todo mundo de novo.
- Tudo fica salvo no banco: SQLite no desenvolvimento e PostgreSQL no Docker.

### Classes

Cada classe tem 4 habilidades, liberadas uma por vitória:

| Classe | Habilidades |
|---|---|
| **Bárbaro** | Fúria Implacável (uma vida extra) → Titã de Ferro (perder por até 5 vira empate) → Sangue do Berserk (+5 depois da Fúria) → Imortal (sobrevive a derrotas, mas acumula penalidade até -20) |
| **Ladino** | Ataque Furtivo (+2) → Assassinato (+1d6) → Premonição de Perigo (perder pela margem exata de um 1d4 vira empate) → Haki da Visão (se o inimigo tirar um múltiplo de 3, a derrota vira empate) |
| **Mago** | Vantagem Arcana (rola 2d20 e fica com o maior) → Elementalista (Pedra, Água, Fogo ou Vento) → Prisão Arcana (anula uma habilidade do inimigo) → Vazio Roxo (1 natural vira 20) |
| **Clérigo** | Bênção Divina (rola de novo um 1 natural) → Mãos Curativas (refaz o duelo se perder por pouco) → Guardião Espiritual (+10 no 20 natural) → Made in Heaven (com um 20 natural, silencia o inimigo) |
| **Guerreiro** | Disciplina de Combate (vence empates) → Mortal (+3) → Herói (1 natural vira 20) → Ex Machina (refaz o duelo se perder tirando de 1 a 9) |

### Qualidade e DevOps

- **Testes automatizados** em `tests/`, cobrindo a API, o chaveamento, os duelos, o banco e o script de e-mail.
- **Testes determinísticos:** o gerador aleatório é injetado como dependência (`app/deps.py`). Nos testes, ele é trocado por um com seed fixa, então os dados sempre dão o mesmo resultado.
- **Cobertura mínima de 90%**, verificada pelo pipeline.
- **Container da aplicação** com `python:3.12-slim`, rodando com um usuário sem privilégios e com health check.
- **Jenkins configurado como código** (JCasC), sem nenhuma configuração manual pela interface.
- **Notificação por e-mail**, com o destinatário vindo do ambiente e não fixo no código.

### Estrutura

```
app/
  main.py, database.py, models.py, schemas.py, deps.py
  routers/api.py          # rotas /api
  services/               # chaveamento, classes, duelos e regras do torneio
  static/                 # frontend (HTML, CSS, JS)
scripts/send_email.py     # e-mail do pipeline
tests/                    # testes automatizados
jenkins/                  # imagem e configuração do Jenkins
Dockerfile, docker-compose.yml, Jenkinsfile
```

---

## Uso de IA

Usamos IA generativa como apoio durante todo o projeto. Tudo o que ela gerou foi revisado, ajustado e testado pelo grupo antes de entrar no repositório, e passa pela mesma suíte de testes e pela cobertura mínima de 90% do pipeline.

### Modelos utilizados

| Ferramenta | Quem usou | Modelo |
|---|---|---|
| Claude (Anthropic) | John | Sonnet 5.5 |
| Claude (Anthropic) | John | Opus 5.5 |
||Tales||
||Vinicius||


### Para que foi usada

- **Brainstorming:** ideias de tema e definição do escopo do torneio.
- **Geração da base do projeto:** API FastAPI, testes com pytest, `Dockerfile` da aplicação, `jenkins/Dockerfile`, `plugins.txt`, `casc.yaml`, `Jenkinsfile`, `docker-compose.yml`, `scripts/send_email.py` e a primeira versão deste README.
- **Debugging:** execução local no Windows (PowerShell) e dúvidas sobre o funcionamento das habilidades.
- **Documentação:** revisão deste README e preparação para a defesa.
- (confirmar) Implementação do motor de duelo com as 4 habilidades por classe.

### Exemplos reais de prompts

| # | Prompt (como foi escrito) | O que a IA respondeu | Decisão |
|---|---|---|---|
| 1 | "Me de mais ideias interessanges, quero algo legal e facil" | Oito ideias, como torneio de e-sports, matchmaking e encurtador de URL | **Descartado.** O grupo propôs o próprio tema (prompt 3). |
| 2 | "...lembrando que Jenkins tem que ser modo container. [...] sei la o que daria para fazer com um Jogo do Unity algo assim." | Desaconselhou rodar um jogo Unity no pipeline (licença e C# fora da cobertura do pytest) e sugeriu um backend em FastAPI | **Descartada a ideia do Unity**, aceita a stack FastAPI + pytest. |
| 3 | "Que tal um sistema de chaveamento aonde gero um personagem aleatorio para um usuario e nele eu crio um sistema de chaves que avança voce para frente com rolagem de d20 baseado a que carta voce tirou." | Escopo: endpoints, modelo de dados, byes e gerador aleatório injetado para testar | **Aceito com ajustes.** |
| 4 | "Certo entao quero que voce crie para mim tendo em mente o seguinte: O projeto deve seguir todos requerimentos necessários pedido pelo projeto. [...]" | Projeto base completo: app, testes, Dockerfiles, Jenkinsfile, JCasC, Compose e script de e-mail | **Aceito como base e ajustado à mão:** `casc.yaml` passou a exigir `REPO_URL` (commit c5a9f07); o e-mail saiu do Mailpit e foi para o Gmail com STARTTLS e variáveis no Compose (9f92403); testes corrigidos (ca00a5b, b64e0ce). |


### Dinâmica de uso

- A IA foi usada principalmente de forma individual em conversa com o Claude, para gerar a base e tirar dúvidas.
- Vinícius e Tales usaram IA nas melhorias de interface.
- As configurações geradas (Jenkinsfile, Compose, casc.yaml) foram revisadas em conjunto antes do commit.
- Os testes automatizados serviram de rede de segurança: código gerado só entrava se a suíte e a cobertura de 90% passassem.
- Nunca compartilhamos senhas, tokens nem o `.env` com a ferramenta.

### O que não foi feito por IA

- **Ideia do jogo:** torneio com carta sorteada e avanço no chaveamento por d20 (prompt 3).
- **Design das 20 habilidades** (5 classes × 4) e da regra "uma habilidade nova por vitória".
- **Arte das 5 cartas** (`app/static/img/`, commit d9583ff) e os ajustes de CSS para exibi-las.
- **Criação do repositório** no Dockerfile Hub e GitHub, organização dos commits.
- **Jenkins funcionando de verdade:** correção do `casc.yaml` para ler `REPO_URL` (c5a9f07) e testes até o pipeline passar.
- **E-mail real:** troca para o Gmail, senha de app e configuração do `.env`.
- **Docker Hub:** build e publicação da imagem `johnsugahara/d20-arena-jenkins:1.0`.
- **Escolha da stack:** FastAPI + pytest e Jenkins em container com configuração como código.

