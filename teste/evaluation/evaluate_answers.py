import json
from pathlib import Path

import requests


API_URL = "http://localhost:8000"


def main() -> None:
    questions_path = Path(__file__).with_name("questions.json")
    questions = json.loads(questions_path.read_text(encoding="utf-8"))

    print("Avaliacao manual de respostas")
    print("Criterios sugeridos: fidelidade ao contexto, completude, citacao de fonte e ausencia de alucinacao.")

    for item in questions:
        response = requests.post(
            f"{API_URL}/chat",
            json={"question": item["question"], "top_k": 4},
            timeout=180,
        )
        response.raise_for_status()
        payload = response.json()
        print("\n" + "=" * 80)
        print(f"Pergunta: {item['question']}")
        print(f"Resposta esperada: {item['reference_answer']}")
        print(f"Resposta gerada: {payload['answer']}")
        print("Fontes:")
        for source in payload["sources"]:
            print(f"- {source['filename']} | pagina={source['page']} | score={source['score']}")


if __name__ == "__main__":
    main()
