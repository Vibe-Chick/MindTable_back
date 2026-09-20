"""
matching/services.py
=======================
MatchRecommendAPIView가 쓰는 ai(user, tables) 함수.

공식: score = 1.0×관심사유사도 + β×배경다양성 + 0.5×성격보완도 − 0.8×재매칭
(ai_engine/matching.py의 score_group()과 동일한 가중치)

- 관심사유사도: PsychologyProfile.interests(자유 텍스트)를 고정 12개 태그로
  투영해 코사인 유사도 계산. 태그/가중치를 DB에 저장 안 해서, 요청마다 LLM로
  즉석 분류한다(모의시연이라 속도보다 정확도 우선. 한 요청 안에서는 같은
  사용자를 두 번 분류하지 않도록 캐시함).
- β(diversity_beta): PsychologyProfile에 저장된 값이 없어 ai_engine 기본값
  0.5로 고정.
- 성격보완도: ai_engine.matching.personality_complement()과 동일한 로직
  (외향성은 적당한 분산, 개방성·우호성은 유사도를 선호).
- 재매칭 페널티: 이 유저와 테이블 멤버가 과거에(지금 테이블 제외) 같은
  MatchTable에 있었던 적 있으면 쌍마다 0.8 감점.
"""

import json
import math
import statistics

import requests

from .models import MatchTable

API_KEY = ""  # 여기 채우세요 (sk-... 키)
BASE_URL = "https://ai.cs.kookmin.ac.kr/v1"
MODEL = "claude-haiku-4-5"

TAGS = ["운동", "여행", "요리", "음악", "영상", "독서", "게임", "기술", "학술", "창작", "봉사", "재테크"]

_BIG_FIVE_FIELDS = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]

DIVERSITY_BETA_DEFAULT = 0.5  # ai_engine 기본값. PsychologyProfile에 개인화 β가 없어 고정값 사용
GAMMA = 0.5      # 성격보완도 가중
DELTA_REPEAT = 0.8  # 재매칭 페널티


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
            "function": {"name": "emit", "description": "결과 출력", "parameters": schema},
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
            return json.loads(args)
    raise RuntimeError(f"구조화 응답을 받지 못했습니다: {data}")


def get_user_major(user):
    return getattr(user, "major", "")


def get_user_school(user):
    return getattr(user, "school", "")


def _get_profile(user):
    """PsychologyProfile이 없으면 중립값(3점, 관심사 없음)으로 대체한다."""
    try:
        profile = user.psychology_profile
    except Exception:
        return {f: 3.0 for f in _BIG_FIVE_FIELDS}, []
    big_five = {f: getattr(profile, f, 3.0) for f in _BIG_FIVE_FIELDS}
    interests = list(profile.interests or [])
    return big_five, interests


_TAGS_SCHEMA = {
    "type": "object",
    "properties": {
        "weights": {
            "type": "object",
            "properties": {t: {"type": "number", "minimum": 0, "maximum": 2} for t in TAGS},
            "required": TAGS,
        }
    },
    "required": ["weights"],
}

_TAGS_SYSTEM_PROMPT = (
    "너는 관심사 키워드를 고정된 12개 카테고리로 투영하는 도구다. "
    "입력된 관심사 키워드 목록을 보고, 12개 카테고리 각각에 대한 관련도를 "
    "0~2 사이 숫자로 매겨라. 직접 관련 있으면 1.0 이상, 전혀 관련 없으면 0. "
    "예: '클라이밍'->운동 1.5, '홈서버'->기술 1.5. "
    "카테고리: 운동, 여행, 요리, 음악, 영상, 독서, 게임, 기술, 학술, 창작, 봉사, 재테크"
)


def _classify_tags(interests):
    if not interests:
        return {t: 0.0 for t in TAGS}
    prompt = "관심사: " + ", ".join(interests)
    result = _call(prompt, _TAGS_SCHEMA, _TAGS_SYSTEM_PROMPT, temp=0.0)
    weights = result.get("weights", {})
    return {t: float(weights.get(t, 0.0)) for t in TAGS}


def _get_tag_weights(user, cache):
    """같은 ai() 호출 안에서는 같은 유저를 두 번 LLM에 안 보내도록 캐시한다."""
    if user.id in cache:
        return cache[user.id]
    _, interests = _get_profile(user)
    weights = _classify_tags(interests)
    cache[user.id] = weights
    return weights


def _cosine_similarity(a, b):
    dot = sum(a.get(t, 0.0) * b.get(t, 0.0) for t in TAGS)
    na = math.sqrt(sum(a.get(t, 0.0) ** 2 for t in TAGS))
    nb = math.sqrt(sum(b.get(t, 0.0) ** 2 for t in TAGS))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def _diversity(majors, schools):
    """ai_engine.matching.diversity()와 동일: 전공(0.5)+학교(0.5)."""
    n = len(majors)
    if n == 0:
        return 0.0
    major_div = len(set(majors)) / n
    school_div = len(set(schools)) / n
    return 0.5 * major_div + 0.5 * school_div


def _personality_complement(big_five_list):
    """ai_engine.matching.personality_complement()와 동일."""
    if len(big_five_list) < 2:
        return 0.0
    e_std = statistics.pstdev([b["extraversion"] for b in big_five_list])
    e_term = 1.0 - abs(e_std - 1.0) / 2.0
    oa = (
        statistics.pstdev([b["openness"] for b in big_five_list])
        + statistics.pstdev([b["agreeableness"] for b in big_five_list])
    ) / 2.0
    return e_term - oa / 2.0


def _repeat_count(user, members, current_table_id):
    """user와 members 각각이 과거(지금 테이블 제외) 같은 테이블에 있었던 적 있는 쌍의 수."""
    count = 0
    for member in members:
        if member.id == user.id:
            continue
        past = (
            MatchTable.objects.filter(members=user)
            .filter(members=member)
            .exclude(id=current_table_id)
        )
        if past.exists():
            count += 1
    return count


def _fit_reason(shared_interests):
    if len(shared_interests) >= 2:
        return f"{shared_interests[0]}·{shared_interests[1]} 얘기가 잘 통할 조합이에요"
    if len(shared_interests) == 1:
        return f"{shared_interests[0]} 관심사가 통하는 조합이에요"
    return "성격이 잘 어울리는 조합이에요"


def ai(user, tables):
    """
    무엇을: 사용자 한 명 + '열린 테이블' 목록을 받아, 각 테이블에 대한
    fit(0~1) / fitReason / sharedInterests를 계산한다.
    score = 1.0*관심사유사도 + β*배경다양성 + 0.5*성격보완도 - 0.8*재매칭

    Returns:
        [{"table": <MatchTable>, "fit": float, "fitReason": str,
          "sharedInterests": [str, ...]}, ...]  fit 내림차순 정렬.
    """
    user_big_five, user_interests = _get_profile(user)
    tag_cache = {}
    user_tags = _get_tag_weights(user, tag_cache)

    recommendations = []
    for table in tables:
        members = list(table.members.all())

        member_big_fives, member_majors, member_schools = [], [], []
        member_interests_list, interest_sims = [], []

        for member in members:
            big_five, interests = _get_profile(member)
            member_big_fives.append(big_five)
            member_interests_list.append(interests)
            member_majors.append(get_user_major(member))
            member_schools.append(get_user_school(member))
            interest_sims.append(_cosine_similarity(user_tags, _get_tag_weights(member, tag_cache)))

        interest_similarity = sum(interest_sims) / len(interest_sims) if interest_sims else 0.0

        diversity_score = _diversity(
            member_majors + [get_user_major(user)],
            member_schools + [get_user_school(user)],
        )
        complement_score = _personality_complement(member_big_fives + [user_big_five])
        repeat = _repeat_count(user, members, table.id)

        raw_score = (
            1.0 * interest_similarity
            + DIVERSITY_BETA_DEFAULT * diversity_score
            + GAMMA * complement_score
            - DELTA_REPEAT * repeat
        )
        fit = round(max(0.0, min(1.0, raw_score)), 2)

        combined_member_interests = set()
        for interests in member_interests_list:
            combined_member_interests |= set(interests)
        shared = sorted(set(user_interests) & combined_member_interests)

        recommendations.append({
            "table": table,
            "fit": fit,
            "fitReason": _fit_reason(shared),
            "sharedInterests": shared,
        })

    recommendations.sort(key=lambda r: r["fit"], reverse=True)
    return recommendations
