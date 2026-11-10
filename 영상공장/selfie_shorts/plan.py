import json, sys
END = 22.8
subs_raw = [  # (시작, 끝, 자막)  — 원장님 실제 말, 받아쓰기 오류(캐시티→KCT)만 고침
 (0.21, 2.05, '이렇게 <em>KCT학원</em>을'), (2.13, 3.85, '안내해 드리고 싶습니다'),
 (4.07, 6.23, '서대문구 <em>영어 수학</em> 학원'), (6.23, 7.70, '<em>KCT학원</em>'),
 (8.55, 10.60, '너무 아이들이 <em>좋아해요</em>'),
 (10.88, 11.95, '<em>KCT학원</em>은'), (12.19, 13.80, '<em>초등부터 고등까지</em>'),
 (13.87, 16.60, '모든 친구들을 위한 학원입니다'), (17.07, 18.99, '모든 친구들이 <em>함께</em> 만나'),
 (18.99, 21.23, '공부할 수 있는 공간입니다'), (21.23, 22.70, '감사합니다'),
]
subs = []
for i, (a, b, h) in enumerate(subs_raw):
    if i + 1 < len(subs_raw) and subs_raw[i + 1][0] - b < 0.7: b = subs_raw[i + 1][0]
    subs.append({'t0': a, 't1': b, 'html': h})
cards = [
 {'t0': 0.25, 't1': 3.9, 'html': '<em>KCT학원</em>을 소개해요'},
 {'t0': 4.1, 't1': 8.4, 'html': '서대문 <em>수학·영어</em>'},
 {'t0': 8.5, 't1': 10.8, 'img': 'img/wolgan-12.jpg'},
 {'t0': 12.1, 't1': 16.7, 'html': '<em>초·중·고</em> 전 과정'},
 {'t0': 17.0, 't1': 22.75, 'html': '함께 만나 <em>공부하는 공간</em>'},
 {'t0': END, 't1': 99, 'end': True, 'html': '<img src="img/logo-dark.png" alt=""><div class="t">지금, 우리 아이<br><span>현주소</span>부터 확인하세요</div><div class="ph"><small>무료 레벨테스트 · 상담</small><b>02-379-7161</b></div><div class="i">카카오톡 채널 <b>kct7</b><br>서울 서대문구 가좌로 114</div>'},
]
json.dump({'subs': subs, 'cards': cards, 'endStart': END}, open('plan.json', 'w'), ensure_ascii=False, indent=1)
