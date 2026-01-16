import os
import json
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from openai import OpenAI
from flask_cors import CORS
import pdfplumber

# Configurações Iniciais
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)
CORS(app)

app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {"txt", "pdf"}

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Histórico em Memória
history = []  


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_pdf(path):
    text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text.replace("\n", " ") + "\n\n"
    except:
        pass
    return text.strip()


def analyze_email(text):
    prompt = (
        "Você é um assistente de atendimento ao cliente. "
        "Classifique o email como 'Produtivo' ou 'Improdutivo'. "
        "Depois, gere uma resposta amigável baseada no conteúdo e categoria.\n"
        "Retorne APENAS um JSON válido com: categoria, resposta, justificativa.\n\n"
        f"Email:\n{text}"
    )

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um assistente profissional de atendimento."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=300
        )

        content = resp.choices[0].message.content.strip()

        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()

        data = json.loads(content)

        return (
            data.get("categoria", "Desconhecido"),
            data.get("resposta", ""),
            data.get("justificativa", "")
        )

    except Exception as e:
        return "Erro", f"Erro ao chamar API: {str(e)}", ""


@app.route("/", methods=["GET"])
def home():
    produtivas = sum(1 for m in history if m["categoria"] == "Produtivo")
    improdutivas = sum(1 for m in history if m["categoria"] == "Improdutivo")

    return render_template("index.html", history=history, stats={
        "produtivas": produtivas,
        "improdutivas": improdutivas,
        "total": len(history)
    })


@app.route("/process", methods=["POST"])
def process():
    text_input = ""
    file = request.files.get("file_input")

    if file and file.filename != "":
        if not allowed_file(file.filename):
            return jsonify({"error": "Arquivo não permitido"}), 400

        filename = secure_filename(file.filename)
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(path)

        if filename.lower().endswith(".txt"):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text_input = f.read()
        else:
            text_input = extract_text_from_pdf(path)

        os.remove(path)

    if not text_input:
        text_input = request.form.get("text_input", "").strip()

    if not text_input:
        return jsonify({"error": "Nenhum texto fornecido"}), 400

    categoria, resposta, justificativa = analyze_email(text_input)

    history.insert(0, {
        "categoria": categoria,
        "resposta": resposta,
        "justificativa": justificativa,
        "content": text_input
    })

    return jsonify({
        "categoria": categoria,
        "resposta": resposta,
        "justificativa": justificativa,
        "content": text_input
    })

