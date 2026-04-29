# SistemaDeBol-o

Sistema de Bolão para a Copa do Mundo 2026, desenvolvido com **Python/Flask**, **Bootstrap 5** (com tema Dark) e **MySQL via SQLAlchemy**.

## Funcionalidades

- 🏆 **Ranking** dos apostadores na página inicial
- ⚽ **Apostas** em jogos da Copa do Mundo 2026
- 📊 **Volume de apostas** visível ao fazer a aposta
- 📅 **Últimos 5 resultados** exibidos na tela de aposta
- 🌙 **Tema Dark/Light** com toggle persistente
- 🔐 **Autenticação** (login/cadastro)

### Funcionalidades do Administrador

- Cadastro e gerenciamento de **Jogos** (times, estádio, local, data/hora, fase, grupo)
- Cadastro de **Times** com bandeira
- Cadastro de **Estádios**
- Configuração de **Pontuação** (placar exato, acerto do vencedor, empate)
- Cadastro de **Endpoints de API** para importar jogos automaticamente
- Registro de **Resultados** com cálculo automático de pontos

## Tecnologias

- Python 3.10+
- Flask 3.x
- Flask-SQLAlchemy
- Flask-Login
- Flask-WTF
- Flask-Migrate
- Bootstrap 5.3
- MySQL (produção) / SQLite (testes)

## Instalação

```bash
# 1. Clone e entre no diretório
git clone https://github.com/rodrigoasrodrigues/SistemaDeBol-o.git
cd SistemaDeBol-o

# 2. Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais MySQL

# 5. Crie o usuário admin
#    (as tabelas são criadas automaticamente na primeira execução)
flask create-admin

# 6. (Opcional) Popule com dados iniciais
flask seed-db

# 7. Inicie o servidor
flask run
```

## Variáveis de Ambiente (`.env`)

| Variável | Descrição | Padrão |
|---|---|---|
| `SECRET_KEY` | Chave secreta da aplicação | — |
| `DB_USER` | Usuário do MySQL | `root` |
| `DB_PASSWORD` | Senha do MySQL | — |
| `DB_HOST` | Host do MySQL | `localhost` |
| `DB_PORT` | Porta do MySQL | `3306` |
| `DB_NAME` | Nome do banco | `sistema_bolao` |

## Deploy (AWS Lightsail via GitHub Actions)

O workflow `.github/workflows/deploy.yml` é acionado automaticamente em todo push na branch `main` e realiza:

1. Build da imagem Docker
2. Push para o registry privado do Lightsail (`aws lightsail push-container-image`)
3. Criação de um novo deployment no serviço de container do Lightsail
4. Aguarda o serviço atingir o estado `RUNNING`

### Pré-requisitos

1. Crie um **Lightsail Container Service** na AWS (e.g. `sistema-bolao`).
2. Adicione os seguintes **Secrets** no repositório (`Settings → Secrets and variables → Actions`):

| Secret | Descrição |
|---|---|
| `AWS_ACCESS_KEY_ID` | ID da chave de acesso IAM (ou use OIDC, veja abaixo) |
| `AWS_SECRET_ACCESS_KEY` | Chave secreta IAM (ou use OIDC, veja abaixo) |
| `AWS_REGION` | Região AWS (ex.: `us-east-1`) |
| `SECRET_KEY` | Chave secreta Flask |
| `DB_USER` | Usuário do banco MySQL |
| `DB_PASSWORD` | Senha do banco MySQL |
| `DB_HOST` | Host do banco MySQL |
| `DB_PORT` | Porta do banco (padrão `3306`) |
| `DB_NAME` | Nome do banco |

3. (Opcional) Defina a variável de repositório `LIGHTSAIL_SERVICE_NAME` com o nome do serviço. Se omitido, usa `sistema-bolao`.

> **Recomendação de segurança:** prefira autenticação via OIDC em vez de chaves estáticas.  
> Configure o provedor OIDC do GitHub na AWS (`https://token.actions.githubusercontent.com`),  
> crie uma IAM Role com a política `AmazonLightsailFullAccess` e armazene o ARN da role no  
> secret `LIGHTSAIL_DEPLOY_ROLE`. Depois, substitua o step de credenciais no workflow conforme  
> o bloco comentado "Option A".

### Build local da imagem

```bash
docker build -t sistema-bolao .
docker run --env-file .env -p 8000:8000 sistema-bolao
```

## Testes

```bash
python -m pytest tests/ -v
```

## Estrutura do Projeto

```
app/
├── __init__.py         # App factory
├── models.py           # Modelos: User, Team, Stadium, Game, Bet, PointConfig, ApiEndpoint
├── auth/               # Blueprint de autenticação
├── main/               # Blueprint principal (ranking, jogos, apostas)
├── admin/              # Blueprint admin
├── templates/          # Templates Jinja2 + Bootstrap 5
└── static/             # CSS e JS customizados
config.py               # Configurações (development, testing, production)
run.py                  # Ponto de entrada + CLI commands
requirements.txt
tests/
└── test_app.py         # Testes automatizados
```
