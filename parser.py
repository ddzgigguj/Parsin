"""
Parser for MK match messages from Telegram channel.
Extracts match data, coefficients, time totals, and round results.
"""

import re
from typing import Optional


def parse_message(text: str, message_id: int = 0) -> Optional[dict]:
    """
    Parse a single message from the channel.
    Returns dict with match data or None if message doesn't match format.
    Skips matches without round results (unfinished matches).
    """
    if not text or not text.strip():
        return None

    lines = text.strip().split('\n')
    lines = [l.strip() for l in lines]

    # Check if this is a match message - must start with time pattern
    time_date_match = re.match(r'^(\d{1,2}:\d{2})\s+(\d{1,2}-\d{2}-\d{4})\s+#N(\d+)\s+#L(\d+)', lines[0])
    if not time_date_match:
        return None

    match_data = {
        'message_id': message_id,
        'time': time_date_match.group(1),
        'date': time_date_match.group(2),
        'match_number': int(time_date_match.group(3)),
        'lobby': int(time_date_match.group(4)),
    }

    # Parse the rest of the message
    full_text = '\n'.join(lines)

    # --- Players (Russian names from hashtags) ---
    # Pattern: #Player1 #Player2
    ru_names_match = re.search(r'^#([А-Яа-яЁё]+)\s+#([А-Яа-яЁё]+)\s*$', full_text, re.MULTILINE)
    if ru_names_match:
        match_data['player1_ru'] = ru_names_match.group(1)
        match_data['player2_ru'] = ru_names_match.group(2)
    else:
        match_data['player1_ru'] = None
        match_data['player2_ru'] = None

    # --- Players (English names) ---
    # Pattern: Name1 - Name2
    en_names_match = re.search(r'^([A-Za-z][A-Za-z ]+?)\s*-\s*([A-Za-z][A-Za-z ]+?)\s*$', full_text, re.MULTILINE)
    if en_names_match:
        match_data['player1_en'] = en_names_match.group(1).strip()
        match_data['player2_en'] = en_names_match.group(2).strip()
    else:
        match_data['player1_en'] = None
        match_data['player2_en'] = None

    # --- Match coefficients P1m|P2m ---
    p_match = re.search(r'P1m\|P2m\s*-\s*([\d.]+)\|([\d.]+)', full_text)
    if p_match:
        match_data['p1m_coeff'] = float(p_match.group(1))
        match_data['p2m_coeff'] = float(p_match.group(2))
    else:
        match_data['p1m_coeff'] = None
        match_data['p2m_coeff'] = None

    # --- Round coefficients P1/P2 ---
    p_round = re.search(r'P1/P2\s*-\s*([\d.]+)/([\d.]+)', full_text)
    if p_round:
        match_data['p1_round_coeff'] = float(p_round.group(1))
        match_data['p2_round_coeff'] = float(p_round.group(2))
    else:
        match_data['p1_round_coeff'] = None
        match_data['p2_round_coeff'] = None

    # --- FBR coefficients (Fatality | Brutality | No finish) ---
    fbr_match = re.search(r'FBR\s*-\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)', full_text)
    if fbr_match:
        match_data['fatality_coeff'] = float(fbr_match.group(1))
        match_data['brutality_coeff'] = float(fbr_match.group(2))
        match_data['no_finish_coeff'] = float(fbr_match.group(3))
    else:
        match_data['fatality_coeff'] = None
        match_data['brutality_coeff'] = None
        match_data['no_finish_coeff'] = None

    # --- FW coefficient ---
    fw_match = re.search(r'#FW\s*-\s*([\d.]+)', full_text)
    if fw_match:
        match_data['fw_coeff'] = float(fw_match.group(1))
    else:
        match_data['fw_coeff'] = None

    # --- Total matches and avg time ---
    # Pattern: #t7v8  atv : 35.83
    tv_match = re.search(r'#t(\d+)v(\d+)\s+atv\s*:\s*([\d.]+)', full_text)
    if tv_match:
        match_data['total_matches'] = f"{tv_match.group(1)}v{tv_match.group(2)}"
        match_data['avg_time'] = float(tv_match.group(3))
    else:
        match_data['total_matches'] = None
        match_data['avg_time'] = None

    # --- Time totals (small, medium, big) ---
    # Pattern: 28.5 (1.256 - 3.81)   #m28
    time_small = re.search(r'([\d.]+)\s*\(\s*([\d.]+)\s*-\s*([\d.]+)\s*\)\s*#m(\d+)', full_text)
    if time_small:
        match_data['time_total_small'] = float(time_small.group(1))
        match_data['time_small_over_coeff'] = float(time_small.group(2))
        match_data['time_small_under_coeff'] = float(time_small.group(3))
        match_data['time_small_tag'] = f"m{time_small.group(4)}"
    else:
        match_data['time_total_small'] = None
        match_data['time_small_over_coeff'] = None
        match_data['time_small_under_coeff'] = None
        match_data['time_small_tag'] = None

    # Pattern: 35.5 (1.93 - 1.975)   #s35
    time_medium = re.search(r'([\d.]+)\s*\(\s*([\d.]+)\s*-\s*([\d.]+)\s*\)\s*#s(\d+)', full_text)
    if time_medium:
        match_data['time_total_medium'] = float(time_medium.group(1))
        match_data['time_medium_over_coeff'] = float(time_medium.group(2))
        match_data['time_medium_under_coeff'] = float(time_medium.group(3))
        match_data['time_medium_tag'] = f"s{time_medium.group(4)}"
    else:
        match_data['time_total_medium'] = None
        match_data['time_medium_over_coeff'] = None
        match_data['time_medium_under_coeff'] = None
        match_data['time_medium_tag'] = None

    # Pattern: 43.5 (4.1 - 1.23)   #b43
    time_big = re.search(r'([\d.]+)\s*\(\s*([\d.]+)\s*-\s*([\d.]+)\s*\)\s*#b(\d+)', full_text)
    if time_big:
        match_data['time_total_big'] = float(time_big.group(1))
        match_data['time_big_over_coeff'] = float(time_big.group(2))
        match_data['time_big_under_coeff'] = float(time_big.group(3))
        match_data['time_big_tag'] = f"b{time_big.group(4)}"
    else:
        match_data['time_total_big'] = None
        match_data['time_big_over_coeff'] = None
        match_data['time_big_under_coeff'] = None
        match_data['time_big_tag'] = None

    # --- FYes / FNo ---
    fyes_match = re.search(r'FYes\s*-([\d.]+)', full_text)
    fno_match = re.search(r'FNo\s*-([\d.]+)', full_text)
    match_data['f_yes_coeff'] = float(fyes_match.group(1)) if fyes_match else None
    match_data['f_no_coeff'] = float(fno_match.group(1)) if fno_match else None

    # --- Bet IDs ---
    bet_ids_match = re.search(r'^(\d{5,})\s+(\d{5,})\s*$', full_text, re.MULTILINE)
    if bet_ids_match:
        match_data['bet_ids'] = f"{bet_ids_match.group(1)} {bet_ids_match.group(2)}"
    else:
        match_data['bet_ids'] = None

    # --- Score ---
    score_match = re.search(r'^(\d+):(\d+)\s*$', full_text, re.MULTILINE)
    if score_match:
        match_data['score'] = f"{score_match.group(1)}:{score_match.group(2)}"
        p1_score = int(score_match.group(1))
        p2_score = int(score_match.group(2))
        if p1_score > p2_score:
            match_data['winner'] = 'P1'
        else:
            match_data['winner'] = 'P2'
    else:
        match_data['score'] = None
        match_data['winner'] = None

    # --- Rounds ---
    rounds = parse_rounds(full_text)

    # Skip matches without rounds (unfinished matches)
    if not rounds:
        return None

    match_data['has_rounds'] = 1
    match_data['total_rounds'] = len(rounds)
    match_data['rounds'] = rounds

    return match_data


def parse_rounds(text: str) -> list:
    """
    Parse round results from message.
    Pattern: 1. P1--R--20  TMM
    Returns list of round dicts.
    """
    rounds = []

    # Pattern: number. P1/P2--F/B/R--time  T...
    round_pattern = re.compile(
        r'(\d+)\.\s*(P[12])--([FBR])--(\d+)\s+(T[A-Z]*)',
        re.MULTILINE
    )

    for m in round_pattern.finditer(text):
        round_num = int(m.group(1))
        winner = m.group(2)
        finish_type_code = m.group(3)
        time_seconds = int(m.group(4))
        time_category = m.group(5)

        # Map finish type
        finish_map = {'F': 'Fatality', 'B': 'Brutality', 'R': 'NoFinish'}
        finish_type = finish_map.get(finish_type_code, finish_type_code)

        rounds.append({
            'round_number': round_num,
            'winner': winner,
            'finish_type': finish_type,
            'time_seconds': time_seconds,
            'time_category': time_category,
        })

    return rounds


def is_valid_match_message(text: str) -> bool:
    """Quick check if text looks like a match message."""
    if not text:
        return False
    return bool(re.match(r'\s*\d{1,2}:\d{2}\s+\d{1,2}-\d{2}-\d{4}\s+#N\d+', text.strip()))
