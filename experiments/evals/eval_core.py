from pathlib import Path
import json


EVAL_FILE = Path("experiments/evals/eval_questions.jsonl") # 评测问题列表，每行一个 JSON 对象，包含 question 和 expected_document_id


def load_eval_cases(path: Path = EVAL_FILE) -> list[dict]:
    '''
    从 JSONL 文件加载评测用例。
    '''
    if not path.exists():
        raise FileNotFoundError(f"Eval file not found: {path}")

    cases: list[dict] = []

    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1): 
            line = line.strip()

            if not line:
                continue

            case = json.loads(line)

            if "question" not in case:  
                raise ValueError(f"Line {line_no}: missing field 'question'")

            if "expected_document_id" not in case:
                raise ValueError(f"Line {line_no}: missing field 'expected_document_id'")

            cases.append(case)

    if not cases:   
        raise ValueError(f"No eval cases found in: {path}")

    return cases