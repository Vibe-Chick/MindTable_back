"""
psychology/manual_question_test.py
=====================================
ai_engine의 질문 생성 API를 수동으로 확인하기 위한 스크립트.
"""

import os

import requests

AI_ENGINE_BASE_URL = os.getenv("AI_ENGINE_BASE_URL", "http://localhost:8000")


def main():
    print("=== ai_engine /questions/generate 호출 ===")
    gen_resp = requests.post(f"{AI_ENGINE_BASE_URL}/questions/generate", timeout=30)
    gen_resp.raise_for_status()
    questions = gen_resp.json()["questions"]

    answers = []
    for i, q in enumerate(questions, start=1):
        print(f"\n[Q{i}] {q}")
        answers.append(input("답변 입력: "))

    print("\n=== ai_engine /questions/followup 호출 ===")
    fu_resp = requests.post(
        f"{AI_ENGINE_BASE_URL}/questions/followup",
        json={"questions": questions, "answers": answers},
        timeout=30,
    )
    fu_resp.raise_for_status()
    followup = fu_resp.json()["followup_question"]

    if followup:
        print(f"\n[추가 질문] {followup}")
        followup_answer = input("답변 입력: ")
        print(f"\n최종 답변 4개: {answers + [followup_answer]}")
    else:
        print("\n추가 질문 없음 - 답변 3개로 충분하다고 판단됨.")
        print(f"최종 답변 3개: {answers}")


if __name__ == "__main__":
    main()
