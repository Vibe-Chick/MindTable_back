"""
psychology/manual_analyze_test.py
=====================================
followUps(질문/답변 목록)를 받아 AI 성향 분석 결과를 반환한다.
국민대 게이트웨이(OpenAI 호환 포맷)를 직접 호출한다.
"""
try:
    from .manual_question_test import generate_base_questions
except ImportError:
    from manual_question_test import generate_base_questions

import json

import requests

API_KEY = "sk-kzXv9BDfT7FIrYnspnWR3b4oUM86IjCLK6rjuVqO5YSvEeG0" 
BASE_URL = "https://ai.cs.kookmin.ac.kr/v1"
MODEL = "claude-haiku-4-5"

_BIG_FIVE_TRAITS = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]


def _call(prompt: str, schema: dict, system: str, temp: float = 0.0) -> dict:
    """게이트웨이에 구조화 출력(tools 방식)으로 1회 호출하고, 파싱된 dict를 반환한다."""
    body = {
        "model": MODEL,
        "messages": (
            [{"role": "system", "content": system}] if system else []
        ) + [{"role": "user", "content": prompt}],
        "temperature": temp,
        "tools": [{
            "type": "function",
            "function": {
                "name": "emit",
                "description": "결과 출력",
                "parameters": schema,
            },
        }],
        "tool_choice": {"type": "function", "function": {"name": "emit"}},
    }
    resp = requests.post(
        f"{BASE_URL}/chat/completions",
        json=body,
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    msg = data["choices"][0]["message"]
    for tc in msg.get("tool_calls") or []:
        args = tc.get("function", {}).get("arguments")
        if args:
            return json.loads(args)  # 문자열로 온 JSON을 실제 dict/list로 변환
    raise RuntimeError(f"구조화 응답을 받지 못했습니다: {data}")


_ANALYZE_SCHEMA = {
    "type": "object",
    "properties": {
        "openness": {"type": "integer", "minimum": 1, "maximum": 5},
        "conscientiousness": {"type": "integer", "minimum": 1, "maximum": 5},
        "extraversion": {"type": "integer", "minimum": 1, "maximum": 5},
        "agreeableness": {"type": "integer", "minimum": 1, "maximum": 5},
        "neuroticism": {"type": "integer", "minimum": 1, "maximum": 5},
        "interests": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
        "valid": {"type": "boolean"},
        "insufficient": {
            "type": "array",
            "items": {"type": "string", "enum": _BIG_FIVE_TRAITS},
        },
    },
    "required": [
        "openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism",
        "interests", "summary", "valid", "insufficient",
    ],
}

_ANALYZE_SYSTEM_PROMPT = (
    "너는 심리측정 보조 도구다. 대학생의 질문-답변 목록을 보고 Big Five(OCEAN) "
    "성격을 1~5점으로 채점하고, 관심사 키워드를 뽑고, 한 문장 요약을 쓴다.\n\n"
    "- 답변에 실제로 드러난 근거로만 채점한다. 근거 없으면 3점(중립).\n"
    "- interests는 답변에 실제로 언급된 것만 뽑는다(지어내지 않는다).\n"
    "- summary는 대비되는 특징을 짚는 한 문장으로 쓴다"
    "(예: '낯가림은 있지만 얘기 시작하면 잘 안 멈추는 타입').\n"
    "- 답변이 너무 적거나 짧아서 판단 근거가 부족한 축이 있으면, 그 축 이름을 "
    "insufficient 목록에 넣고 valid를 false로 한다. 판단할 근거가 충분하면 "
    "insufficient는 빈 배열, valid는 true로 한다."
)


def analyze_personality(user_id: str, follow_ups: list) -> dict:
    """
    무엇을: followUps(질문/답변 목록)를 받아 AI 성향 분석 결과를 반환한다.

    Args:
        user_id: 사용자 식별자(이메일 등). 프롬프트에는 안 쓰지만 로그/디버깅용으로 받는다.
        follow_ups: [{"questionId": "...", "question": "...", "answer": "..."}, ...]

    Returns:
        명세서와 동일한 형태의 dict:
        {"bigFive": {...5축...}, "interests": [...], "summary": "...",
         "valid": bool, "insufficient": [...]}
        전부 파이썬 기본 타입(dict/list/str/bool/int)이다.
    """
    qa_text = "\n\n".join(
        f"[{fu.get('questionId', '?')}] {fu.get('question', '')}\n{(fu.get('answer') or '').strip() or '(무응답)'}"
        for fu in follow_ups
    )

    result = _call(qa_text, _ANALYZE_SCHEMA, _ANALYZE_SYSTEM_PROMPT, temp=0.0)

    return {
        "bigFive": {trait: result[trait] for trait in _BIG_FIVE_TRAITS},
        "interests": list(result.get("interests") or []),
        "summary": str(result.get("summary") or ""),
        "valid": bool(result.get("valid", False)),
        "insufficient": list(result.get("insufficient") or []),
    }





def main():
    print("=== 질문 3개 생성 ===")
    questions = generate_base_questions()

    follow_ups = []
    for i, q in enumerate(questions, start=1):
        print(f"\n[Q{i}] {q}")
        answer = input("답변 입력: ")
        follow_ups.append({"questionId": f"q{i}", "question": q, "answer": answer})

    print("\n=== AI 성향 분석 ===")
    user_id = input("\nuser_id 입력: ")
    result = analyze_personality(user_id, follow_ups)

    print("\n=== 최종 결과 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

