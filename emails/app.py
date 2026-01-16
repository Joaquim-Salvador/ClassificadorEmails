import os
import re
import json
import logging
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import openai
from flask_cors import CORS
import pdfplumber

# -----------------------------
# Config & logging
# -----------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.warning("OPENAI_API_KEY não encontrada nas env vars. Configure antes do deploy.")

openai.api_key = OPENAI_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("classificador")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {"txt", "pdf"}

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Histórico em memória (volátil)
history = []  # cada item: {"categoria":..., "resposta":..., "justificativa":..., "content":...}


# -----------------------------
# Helpers
# -----------------------------
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_pdf(path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text.replace("\n", " ") + "\n\n"
    except Exception as e:
        logger.exception("Erro ao extrair PDF: %s", e)
    return text.strip()


def _extract_json_from_text(text: str) -> str | None:
    """
    Tenta extrair um JSON válido a partir de um texto que pode conter crases ou texto adicional.
    Retorna a string JSON ou None.
    """
    # remover blocos de código ```json ... ```
    text = re.sub(r"```json\s*", "", text, flags=re.IGNORECASE)
    text = text.replace("```", "")

    # pegar o primeiro objeto JSON simples (não recursivo)
    match = re.search(r"\{.*?\}", text, flags=re.DOTALL)
    if match:
        return match.group(0).strip()
    return None



def analyze_email(text: str) -> tuple[str, str, str]:
    """
    Chama a OpenAI para classificar e gerar resposta.
    Retorna (categoria, resposta_amigavel, justificativa).
    """
    prompt = (
        "Você é um assistente de atendimento ao cliente. "
        "Classifique o email como 'Produtivo' ou 'Improdutivo'. "
        "Depois, gere uma resposta amigável baseada no conteúdo e na categoria.\n"
        "Retorne APENAS um JSON válido com os campos: categoria, resposta, justificativa.\n\n"
        f"Email:\n{text}"
    )

    try:
        logger.info("Chamando OpenAI para analisar texto (comprimento %d)", len(text))
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # mantenha se você tiver acesso; se der erro, troque por um modelo disponível
            messages=[
                {"role": "system", "content": "Você é um assistente profissional de atendimento ao cliente."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=400
        )

        # extrair texto da resposta
        content = resp["choices"][0]["message"]["content"].strip()
        logger.debug("Resposta bruta do modelo: %s", content[:500])

        # tentar carregar JSON direto
        json_text = _extract_json_from_text(content) or content

        try:
            data = json.loads(json_text)
            categoria = (data.get("categoria") or "Desconhecido").strip()
            resposta = (data.get("resposta") or "").strip()
            justificativa = (data.get("justificativa") or "").strip()
            return categoria, resposta, justificativa
        except Exception:
            # fallback: se não for JSON, coloque tudo em "resposta" e categoria Desconhecido
            logger.warning("Não foi possível parsear JSON da resposta do modelo. Retornando fallback.")
            return "Desconhecido", content, ""

    except Exception as e:
        logger.exception("Erro ao chamar OpenAI: %s", e)
        return "Erro", f"Erro ao chamar API: {str(e)}", ""


# -----------------------------
# Rotas
# -----------------------------
@app.route("/", methods=["GET"])
def home():
    produtivas = sum(1 for m in history if m.get("categoria") == "Produtivo")
    improdutivas = sum(1 for m in history if m.get("categoria") == "Improdutivo")
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

    if file and file.filename:
        if not allowed_file(file.filename):
            return jsonify({"error": "Arquivo não permitido"}), 400

        filename = secure_filename(file.filename)
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(path)

        try:
            if filename.lower().endswith(".txt"):
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text_input = f.read()
            else:
                text_input = extract_text_from_pdf(path)
        finally:
            # sempre tenta remover o arquivo
            try:
                os.remove(path)
            except Exception:
                pass

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
