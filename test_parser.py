"""
Test the parser against sample messages from the channel.
"""
from parser import parse_message

# Sample message 1 - complete match with score 5:1
SAMPLE_1 = """01:35 14-05-2026 #N258 #L4
#ЭрмакКэссиКейдж
#Эрмак #КэссиКейдж
Ermac - Cassie Cage
   P1m|P2m - 2.575|1.53
P1/P2 - 2.168/1.755
FBR - 3.75 | 3.8 | 1.81
#t7v8     atv : 35.83
TimeStat (https://t.me/timestata/465713)(Больше-Меньше:O-U)
28.5 (1.256 - 3.81)   #m28
35.5 (1.93 - 1.975)   #s35
43.5 (4.1 - 1.23)   #b43
FYes -3.75    FNo -1.29
377349 377311

5:1
1. P1--R--20  TMM
2. P1--R--47  TBB
3. P1--B--32  TM
4. P1--B--34  TM
5. P2--B--33  TM
6. P1--R--36  TB
   #T6"""

# Sample message 2 - complete match 5:0
SAMPLE_2 = """01:40 14-05-2026 #N259 #L1
#ТреморДжэкиБриггс
#Тремор #ДжэкиБриггс
Tremor - Jacqueline Briggs
   P1m|P2m - 1.285|3.79
P1/P2 - 1.584/2.44
FBR - 3.29 | 5.26 | 1.696
#t6v6     atv : 32.5
TimeStat (https://t.me/timestata/465714)(Больше-Меньше:O-U)
26.5 (1.245 - 3.94)   #m26
32.5 (2.008 - 1.896)   #s32
38.5 (3.72 - 1.265)   #b38
FYes -3.29    FNo -1.355
371201 371207

5:0
1. P1--R--34  TB
2. P1--B--32  TM
3. P1--F--45  TBB
4. P1--R--26  TMM
5. P1--R--39  TBB
   #T5"""

# Sample message 3 - match with 5:4 score
SAMPLE_3 = """01:25 14-05-2026 #N256 #L2
#КунгЛаоЭрронБлэк
#КунгЛао #ЭрронБлэк
Kung Lao - Erron Black
   P1m|P2m - 1.98|1.92
P1/P2 - 1.96/1.94
FBR - 3.3 | 10.4 | 1.425
#FW - 1.001
#t5v9     atv : 25.83
TimeStat (https://t.me/timestata/465711)(Больше-Меньше:O-U)
19.5 (1.225 - 4.15)   #m19
24.5 (2.06 - 1.85)   #s24
33.5 (3.93 - 1.245)   #b33
FYes -3.3    FNo -1.352
371217 377309

5:4
1. P1--B--31  TB
2. P2--R--32  TB
3. P2--R--22  TM
4. P2--B--34  TBB
5. P2--R--29  TB
6. P1--R--32  TB
7. P1--R--22  TM
8. P1--B--21  TM
9. P1--B--23  TM"""

# Sample message 4 - unfinished match (no rounds) - should be SKIPPED
SAMPLE_4 = """02:00 14-05-2026 #N263 #L1
#КэссиКейджКунгДжин
#КэссиКейдж #КунгДжин
Cassie Cage - Kung Jin
   P1m|P2m - 1.001|100
P1/P2 - 1.045/10.4
FBR - 1.736 | 10.4 | 2.51
#FW - 1.001
#t6v8     atv : 34.17
TimeStat (https://t.me/timestata/465718)(Больше-Меньше:O-U)
27.5 (1.256 - 3.82)   #m27
33.5 (1.975 - 1.925)   #s33
41.5 (4.15 - 1.225)   #b41
FYes -1.736    FNo -2.195
377311 377351
   #T9"""


def test_sample_1():
    result = parse_message(SAMPLE_1, message_id=1001)
    assert result is not None, "Sample 1 should parse successfully"
    
    assert result['time'] == '01:35'
    assert result['date'] == '14-05-2026'
    assert result['match_number'] == 258
    assert result['lobby'] == 4
    assert result['player1_ru'] == 'Эрмак'
    assert result['player2_ru'] == 'КэссиКейдж'
    assert result['player1_en'] == 'Ermac'
    assert result['player2_en'] == 'Cassie Cage'
    assert result['p1m_coeff'] == 2.575
    assert result['p2m_coeff'] == 1.53
    assert result['p1_round_coeff'] == 2.168
    assert result['p2_round_coeff'] == 1.755
    assert result['fatality_coeff'] == 3.75
    assert result['brutality_coeff'] == 3.8
    assert result['no_finish_coeff'] == 1.81
    assert result['total_matches'] == '7v8'
    assert result['avg_time'] == 35.83
    assert result['time_total_small'] == 28.5
    assert result['time_small_over_coeff'] == 1.256
    assert result['time_small_under_coeff'] == 3.81
    assert result['time_small_tag'] == 'm28'
    assert result['time_total_medium'] == 35.5
    assert result['time_medium_over_coeff'] == 1.93
    assert result['time_medium_under_coeff'] == 1.975
    assert result['time_medium_tag'] == 's35'
    assert result['time_total_big'] == 43.5
    assert result['time_big_over_coeff'] == 4.1
    assert result['time_big_under_coeff'] == 1.23
    assert result['time_big_tag'] == 'b43'
    assert result['f_yes_coeff'] == 3.75
    assert result['f_no_coeff'] == 1.29
    assert result['bet_ids'] == '377349 377311'
    assert result['score'] == '5:1'
    assert result['winner'] == 'P1'
    assert result['total_rounds'] == 6
    assert result['has_rounds'] == 1
    
    # Check rounds
    rounds = result['rounds']
    assert len(rounds) == 6
    assert rounds[0] == {'round_number': 1, 'winner': 'P1', 'finish_type': 'NoFinish', 'time_seconds': 20, 'time_category': 'TMM'}
    assert rounds[2] == {'round_number': 3, 'winner': 'P1', 'finish_type': 'Brutality', 'time_seconds': 32, 'time_category': 'TM'}
    assert rounds[4] == {'round_number': 5, 'winner': 'P2', 'finish_type': 'Brutality', 'time_seconds': 33, 'time_category': 'TM'}
    
    print("[PASS] Sample 1 - Ermac vs Cassie Cage (5:1)")


def test_sample_2():
    result = parse_message(SAMPLE_2, message_id=1002)
    assert result is not None, "Sample 2 should parse successfully"
    
    assert result['match_number'] == 259
    assert result['lobby'] == 1
    assert result['player1_en'] == 'Tremor'
    assert result['player2_en'] == 'Jacqueline Briggs'
    assert result['p1m_coeff'] == 1.285
    assert result['p2m_coeff'] == 3.79
    assert result['score'] == '5:0'
    assert result['winner'] == 'P1'
    assert result['total_rounds'] == 5
    
    rounds = result['rounds']
    assert rounds[2] == {'round_number': 3, 'winner': 'P1', 'finish_type': 'Fatality', 'time_seconds': 45, 'time_category': 'TBB'}
    
    print("[PASS] Sample 2 - Tremor vs Jacqueline Briggs (5:0)")


def test_sample_3():
    result = parse_message(SAMPLE_3, message_id=1003)
    assert result is not None, "Sample 3 should parse successfully"
    
    assert result['match_number'] == 256
    assert result['player1_en'] == 'Kung Lao'
    assert result['player2_en'] == 'Erron Black'
    assert result['fw_coeff'] == 1.001
    assert result['score'] == '5:4'
    assert result['winner'] == 'P1'
    assert result['total_rounds'] == 9
    
    rounds = result['rounds']
    assert rounds[0]['finish_type'] == 'Brutality'
    assert rounds[1]['winner'] == 'P2'
    assert rounds[8] == {'round_number': 9, 'winner': 'P1', 'finish_type': 'Brutality', 'time_seconds': 23, 'time_category': 'TM'}
    
    print("[PASS] Sample 3 - Kung Lao vs Erron Black (5:4)")


def test_sample_4_skip():
    """Unfinished matches (no rounds) should be skipped."""
    result = parse_message(SAMPLE_4, message_id=1004)
    assert result is None, "Sample 4 (unfinished match) should return None"
    print("[PASS] Sample 4 - Unfinished match correctly skipped")


def test_non_match_messages():
    """Non-match messages should return None."""
    assert parse_message("", 0) is None
    assert parse_message("Hello world", 0) is None
    assert parse_message("Some random text\nwith lines", 0) is None
    print("[PASS] Non-match messages correctly skipped")


if __name__ == '__main__':
    test_sample_1()
    test_sample_2()
    test_sample_3()
    test_sample_4_skip()
    test_non_match_messages()
    print("\n" + "=" * 50)
    print("  ALL TESTS PASSED!")
    print("=" * 50)
