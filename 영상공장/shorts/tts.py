"""장면 대본을 문장(끊어 읽기) 단위로 읽히고, 사이에 원장님 녹음에서 잰 쉼을 넣어 tts/NN.mp3로 합쳐요."""
import json, subprocess, os, sys, re
VOICE = sys.argv[1]
PAUSE_COMMA, PAUSE_SENT = 0.3, 0.5   # 쉼표로 끝난 조각 뒤 / 문장 끝 뒤
os.makedirs('tts/parts', exist_ok=True)
meta = []
def run(*a): return subprocess.run(a, capture_output=True, text=True, check=True).stdout
for i, sc in enumerate(json.load(open('script.json')), 1):
    files = []
    for k, text in enumerate(sc['parts']):
        raw, trim = f'tts/parts/{i:02d}_{k}.mp3', f'tts/parts/{i:02d}_{k}.wav'
        body = json.dumps({"text": text, "reference_id": VOICE, "format": "mp3"})
        # 글자 수로 예상 길이를 잡고, 너무 길게 늘어진 테이크는 다시 읽혀요 (최대 4번, 가장 짧은 것 사용)
        syl = len(re.findall(r'[가-힣A-Za-z0-9]', text)); expect = syl * 0.17 + text.count(',') * 0.25
        best = None
        for take in range(4):
            tw = f'tts/parts/{i:02d}_{k}_t{take}.wav'
            code = run('curl', '-sS', '--max-time', '120', '-X', 'POST', 'https://api.fish.audio/v1/tts', '-H', 'Authorization: Bearer proxy-injected',
                       '-H', 'Content-Type: application/json', '-H', 'model: s1', '-d', body, '-o', raw, '-w', '%{http_code}')
            assert code == '200', (i, k, code)
            # 앞뒤 무음 정리 (말 앞뒤 0.05초만 남김)
            run('ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-af',
                'silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse',
                '-ar', '48000', '-ac', '1', tw)
            d = float(run('ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', tw))
            print(f'   {i:02d}_{k} take{take}: {d:.2f}s (예상 {expect:.2f}s)')
            if best is None or d < best[0]: best = (d, tw)
            if d <= expect * 1.45: break
        os.replace(best[1], trim)
        files.append(trim)
        if k < len(sc['parts']) - 1:
            p = PAUSE_SENT if text.rstrip()[-1] in '.!?' else PAUSE_COMMA
            sil = f'tts/parts/sil_{p}.wav'
            if not os.path.exists(sil):
                run('ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', f'anullsrc=r=48000:cl=mono', '-t', str(p), sil)
            files.append(sil)
    lst = f'tts/parts/{i:02d}.txt'
    open(lst, 'w').write(''.join(f"file '{os.path.basename(f)}'\n" for f in files))
    run('ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c:a', 'libmp3lame', '-q:a', '2', f'tts/{i:02d}.mp3')
    d = float(run('ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f'tts/{i:02d}.mp3'))
    print(i, len(sc['parts']), 'parts', round(d, 2), 's')
