import json
from pathlib import Path

from app.core.config import settings
from app.rag.pipeline import RAGPipeline


def main() -> None:
    questions_path = Path(__file__).with_name("questions.json")
    questions = json.loads(questions_path.read_text(encoding="utf-8"))

    rag = RAGPipeline()
    if not rag.list_documents().documents:
        for path in sorted(settings.sample_data_dir.iterdir()):
            if path.suffix.lower() in {".pdf", ".txt", ".md", ".markdown", ".html", ".htm"}:
                rag.ingest_file(path, original_filename=path.name)

    hits = 0
    reciprocal_ranks: list[float] = []

    for item in questions:
        sources = rag.retriever.retrieve(item["question"], top_k=4)
        filenames = [source.filename for source in sources]
        expected = set(item["expected_files"])
        hit = any(filename in expected for filename in filenames)
        hits += int(hit)

        rank = next(
            (index for index, filename in enumerate(filenames, start=1) if filename in expected),
            None,
        )
        reciprocal_ranks.append(1 / rank if rank else 0)

        print(f"\nPergunta: {item['question']}")
        print(f"Esperado: {', '.join(item['expected_files'])}")
        print(f"Recuperados: {', '.join(filenames) or 'nenhum'}")
        print(f"Hit@4: {'sim' if hit else 'nao'}")

    total = len(questions)
    hit_at_4 = hits / total if total else 0
    mrr = sum(reciprocal_ranks) / total if total else 0
    print("\nResumo")
    print(f"Hit@4: {hit_at_4:.2%}")
    print(f"MRR: {mrr:.2f}")


if __name__ == "__main__":
    main()

