"""
psychology/manual_question_test.py
=====================================
국민대 게이트웨이(OpenAI 호환 포맷)로 온보딩 질문 3개를 생성하고,
답변이 불충분하면 추가 질문을 판단한다.
"""

import json

import requests

API_KEY = "sk-kzXv9BDfT7FIrYnspnWR3b4oUM86IjCLK6rjuVqO5YSvEeG0"  # 여기 채우세요 (sk-... 키)
BASE_URL = "https://ai.cs.kookmin.ac.kr/v1"
MODEL = "claude-haiku-4-5"


def _call(prompt: str, schema: dict, system: str, temp: float = 0.0) -> dict:
    """게이트웨이에 구조화 출력(tools 방식)으로 1회 호출한다."""
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
        print("args",args)
        if args:
            return args
    raise RuntimeError(f"구조화 응답을 받지 못했습니다: {data}")


def generate_base_questions():
    """Big Five 관련 개방형 질문 3개를 생성해 문자열 리스트로 반환한다."""
    schema = {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 3,
                "maxItems": 3,
            }
        },
        "required": ["questions"],
    }
    system = (
        "너는 대학생 대상 성격 온보딩 설문의 질문 설계자다. "
        "Big Five(OCEAN) 성격 특성을 자유서술형 답변에서 읽어낼 수 있도록 "
        "개방형 질문 3개를 만든다. 객관식/예-아니오 질문 금지, 최근 있었던 "
        "구체적 경험을 묻는다, 3개는 서로 다른 성격 축을 겨냥한다."
    )
    result = _call("대학생 온보딩 설문용 개방형 질문 3개를 만들어라.", schema, system, temp=0.7)
    data = json.loads(result)
    questions = data.get("questions", [])
    return questions


def judge_followup_question(questions, answers):
    """답변 3개가 불충분하면 추가 질문 1개를, 충분하면 None을 반환한다."""
    schema = {
        "type": "object",
        "properties": {
            "insufficient": {"type": "boolean"},
            "followup_question": {"type": "string"},
        },
        "required": ["insufficient", "followup_question"],
    }
    system = (
        "너는 심리측정 보조 도구다. 대학생이 방금 답한 자유서술 답변 3개를 보고 "
        "Big Five 성격을 채점하기에 충분한 정보인지 판단한다. 답변이 너무 짧거나"
        "(\"네\", \"그냥요\" 등) 구체적 행동/경험이 없으면 불충분하다고 판단한다. "
        "충분하면 insufficient를 false로, followup_question은 빈 문자열로 둔다. "
        "불충분하면 insufficient를 true로 하고, 부족한 부분을 채울 추가 질문 1개를 "
        "followup_question에 담는다(이미 물은 3개와 안 겹치게)."
    )
    qa_text = "\n\n".join(
        f"[Q{i+1}] {q}\n{(a or '').strip() or '(무응답)'}"
        for i, (q, a) in enumerate(zip(questions, answers))
    )
    result = _call(qa_text, schema, system, temp=0.0)
    if result.get("insufficient") and (result.get("followup_question") or "").strip():
        return result["followup_question"].strip()
    return None


def main():
    print("=== 기본 질문 3개 생성 ===")
    questions = generate_base_questions()

    answers = []
    for i, q in enumerate(questions, start=1):
        print(f"\n[Q{i}] {q}")
        answers.append(input("답변 입력: "))

    print("\n=== 추가 질문 판단 ===")
    followup = judge_followup_question(questions, answers)

    if followup:
        print(f"\n[추가 질문] {followup}")
        followup_answer = input("답변 입력: ")
        print(f"\n최종 답변 4개: {answers + [followup_answer]}")
    else:
        print("\n추가 질문 없음 - 답변 3개로 충분하다고 판단됨.")
        print(f"최종 답변 3개: {answers}")


if __name__ == "__main__":
    main()
