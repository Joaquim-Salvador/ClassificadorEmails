# Classificador de Emails com Resposta Automática

Uma aplicação web simples que utiliza inteligência artificial (OpenAI GPT-4O Mini) para **classificar emails** como **Produtivo** ou **Improdutivo** e gerar **respostas amigáveis automáticas**.  

Ideal para empresas que recebem muitos emails e querem automatizar parte do atendimento.

---

## 🖥 Funcionalidades

- Enviar emails **digitando o texto** ou **fazendo upload** de arquivos `.txt` ou `.pdf`.  
- Classificação automática do email:  
  - **Produtivo** → precisa de ação ou resposta  
  - **Improdutivo** → não precisa de ação imediata  
- Resposta amigável automática baseada na categoria.  
- Histórico de emails enviados com detalhes de classificação e justificativa.  
- Dashboard visual mostrando quantidade de emails produtivos e improdutivos.  
- Interface moderna **dark mode** com abas separadas: Enviar, Dashboard, Histórico.  
- Indicador de “O bot está pensando…” enquanto processa a resposta.

---

## ⚙️ Pré-requisitos

Antes de rodar o sistema, você precisa ter:

1. **Python 3.10+** instalado  
   - Baixar: [Python.org](https://www.python.org/downloads/)

2. **Pip** (gerenciador de pacotes do Python)  
   - Normalmente já vem junto com o Python.

3. **Conta na OpenAI** e chave de API  
   - Criar: [OpenAI](https://platform.openai.com/)  
   - Copiar sua chave (`OPENAI_API_KEY`).

---

## 💻 Instalação e execução local

### 1️⃣ Clonar o repositório

git clone https://github.com/Joaquim-Salvador/ClassificadorEmails.git
cd email-classifier-gpt/emails

2️⃣ Criar ambiente virtual (recomendado)
python -m venv venv

Ativar ambiente virtual:

Windows (PowerShell):
venv\Scripts\activate

Linux / Mac:
source venv/bin/activate

3️⃣ Instalar dependências
pip install -r requirements.txt
Isso vai instalar todas as bibliotecas necessárias:

Flask → backend web

openai → integração com GPT-4O Mini

PyPDF2 → leitura de PDFs

pdfplumber → leitura avançada de PDFs

python-dotenv → carregar variáveis de ambiente

4️⃣ Configurar a chave da OpenAI
Crie um arquivo .env na pasta emails/ e cole a chave:


Como obter a chave?

1. Acesse: https://platform.openai.com/
2. Crie uma conta ou faça login
3. Vá em API Keys
4. Clique em Create new secret key
5. Copie a chave gerada
6. Cole isso no arquivo .env: OPENAI_API_KEY=coloque_sua_chave_aqui


5️⃣ Rodar o sistema
bash
Copiar código
python app.py
Abra o navegador em:

http://127.0.0.1:5000/
🖱 Uso da aplicação

1. Vá para a aba Enviar Mensagem
2. Digite um email ou envie um arquivo .txt ou .pdf
3. Clique em Enviar
4. Aguarde o indicador “O bot está pensando…”
5. Veja a resposta automática e histórico atualizado
6. Confira o Dashboard para ver a contagem de mensagens produtivas e improdutivas

🌟 Sugestões de testes
Você pode usar estes exemplos para testar o sistema:

Produtivo:

Gostaria de solicitar a segunda via da fatura.
Pode verificar o status do meu pedido?
Preciso de ajuda para acessar o sistema.

Improdutivo:

Obrigado pela atenção.
Feliz natal!
Mensagem recebida, obrigado.

💡 Notas importantes

Arquivos enviados são armazenados temporariamente e podem ser removidos manualmente da pasta uploads/.
O sistema depende da OpenAI API para classificação e resposta. Sem a chave, não funcionará.

📦 Bibliotecas principais
Flask
openai
PyPDF2 / pdfplumber
python-dotenv
Chart.js (via CDN no frontend)


