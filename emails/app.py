import os
import json
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from openai import OpenAI
import PyPDF2

# -----------------------------
# Configurações
# -----------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {"txt", "pdf"}

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# -----------------------------
# Histórico em memória
# -----------------------------
history = []  # Cada item: {"categoria":..., "resposta":..., "justificativa":..., "content":...}

# -----------------------------
# Funções auxiliares
# -----------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

import pdfplumber

def extract_text_from_pdf(path):
    text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    # Substitui quebras de linha simples por espaço
                    # Mantém parágrafos duplos
                    page_text = page_text.replace("\n", " ")
                    text += page_text + "\n\n"
    except Exception as e:
        print("Erro ao extrair PDF:", e)
        text = ""
    return text.strip()


def analyze_email(text):
    """
    Chama a OpenAI para classificar o email e gerar resposta amigável.
    Retorna (categoria, resposta_amigavel, justificativa)
    """
    prompt = (
        "Você é um assistente de atendimento ao cliente. "
        "Classifique o email como 'Produtivo' ou 'Improdutivo'. "
        "Depois, gere uma resposta amigável para o cliente baseada no conteúdo e na categoria.\n"
        "Retorne APENAS um JSON válido, sem crases ou texto adicional, "
        "com os campos: categoria, resposta, justificativa.\n\n"
        f"Email:\n{text}"
    )

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":"Você é um assistente profissional de atendimento ao cliente."},
                {"role":"user","content":prompt}
            ],
            temperature=0.5,
            max_tokens=300
        )
        content = resp.choices[0].message.content.strip()

        # Remover possíveis crases ou ```json
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()

        # Parse JSON
        try:
            data = json.loads(content)
            categoria = data.get("categoria","Desconhecido").strip()
            resposta = data.get("resposta","").strip()
            justificativa = data.get("justificativa","").strip()
            return categoria, resposta, justificativa
        except json.JSONDecodeError:
            return "Desconhecido", content, ""

    except Exception as e:
        return "Erro", f"Erro ao chamar API: {str(e)}", ""

# -----------------------------
# Rotas
# -----------------------------
@app.route("/", methods=["GET"])
def home():
    # Calcular estatísticas
    produtivas = sum(1 for m in history if m["categoria"] == "Produtivo")
    improdutivas = sum(1 for m in history if m["categoria"] == "Improdutivo")
    total = len(history)
    return render_template("index.html", history=history, stats={
        "produtivas": produtivas,
        "improdutivas": improdutivas,
        "total": total
    })

@app.route("/process", methods=["POST"])
def process():
    text_input = ""
    file = request.files.get("file_input")

    # -------------------------
    # Arquivo enviado
    # -------------------------
    if file and file.filename != "":
        if not allowed_file(file.filename):
            return jsonify({"error": "Arquivo não permitido"}), 400
        filename = secure_filename(file.filename)
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(path)

        if filename.lower().endswith(".txt"):
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text_input = f.read()
            except Exception:
                text_input = ""
        elif filename.lower().endswith(".pdf"):
            text_input = extract_text_from_pdf(path)

        os.remove(path)

    # -------------------------
    # Texto manual
    # -------------------------
    if not text_input:
        text_input = request.form.get("text_input", "").strip()

    if not text_input:
        return jsonify({"error": "Nenhum texto fornecido"}), 400

    # -------------------------
    # Análise com OpenAI
    # -------------------------
    categoria, resposta, justificativa = analyze_email(text_input)

    # Salvar no histórico
    history.insert(0, {
        "categoria": categoria,
        "resposta": resposta,
        "justificativa": justificativa,
        "content": text_input
    })

    # -------------------------
    # Retornar JSON para o front-end
    # -------------------------
    return jsonify({
        "categoria": categoria,
        "resposta": resposta,
        "justificativa": justificativa,
        "content": text_input
    })

# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
