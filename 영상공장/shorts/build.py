"""KCT학원 홍보 쇼츠 빌드: 타임라인 → 프레임 → 오디오 → mp4 + srt.
사용: python3 build.py <버전> [--test]"""
import json, re, subprocess, sys, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', '완성영상')
VER = sys.argv[1] if len(sys.argv) > 1 else 'v1'
TEST = '--test' in sys.argv
FPS = 30
GAP = 0.1        # 장면 사이 쉼
TAIL = 0.2      # 말 끝난 뒤 머무는 시간
END_HOLD = 0.6   # 마지막 장면 머무는 시간
KEYS = ['KCT학원', '지금 실력', '무료 레벨테스트', '다 맞을 때까지', '쿠킹클래스', '할 때는 끝까지', '현주소', '기초']

def dur(p):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p],
                                capture_output=True, text=True).stdout)

def chunks_of(say, maxlen=16):
    parts = []
    for p in (p.strip() for p in re.split(r'(?<=[,.!?])\s+', say) if p.strip()):
        words, line = p.split(), ''
        for w in words:   # 긴 문장은 단어 단위로 나눠요
            if line and len(line) + 1 + len(w) > maxlen:
                parts.append(line); line = w
            else:
                line = (line + ' ' + w).strip()
        parts.append(line)
    out, cur = [], ''
    for p in parts:
        if cur and len(cur) + 1 + len(p) > maxlen:
            out.append(cur); cur = p
        else:
            cur = (cur + ' ' + p).strip()
    if cur: out.append(cur)
    return out

def hl(text):
    for k in KEYS:
        text = text.replace(k, f'<em>{k}</em>')
    return text

script = json.load(open(os.path.join(HERE, 'script.json')))
t = 0.1
timeline = []
for i, sc in enumerate(script, 1):
    a = os.path.join(HERE, 'tts', f'{i:02d}.mp3')
    d = dur(a)
    start = t
    end = start + d + TAIL + (END_HOLD if i == len(script) else 0)
    pieces = chunks_of(sc['say'])
    total = sum(len(p) for p in pieces)
    cs, c0 = [], start
    for p in pieces:
        c1 = c0 + d * len(p) / total
        cs.append({'t0': round(c0, 3), 't1': round(c1 + (0.15 if p is pieces[-1] else 0), 3), 'html': hl(p), 'text': p})
        c0 = c1
    timeline.append({'start': round(start, 3), 'end': round(end, 3), 'audio': a, 'say': sc['say'], 'chunks': cs})
    t = end + GAP
TOTAL = timeline[-1]['end']
print(f'total {TOTAL:.2f}s')
json.dump(timeline, open(os.path.join(HERE, 'timeline.json'), 'w'), ensure_ascii=False, indent=1)

# ---- frames
frames = os.path.join(HERE, 'frames')
shutil.rmtree(frames, ignore_errors=True); os.makedirs(frames)
times = [1.5, 7.0, 15.0, 21.5, 30.5, TOTAL - 0.3] if TEST else [f / FPS for f in range(int(TOTAL * FPS))]
js = f"""
const {{ chromium }} = require('playwright');
(async () => {{
  const b = await chromium.launch();
  const p = await b.newPage({{ viewport: {{ width: 1080, height: 1920 }} }});
  await p.addInitScript(tl => {{ window.TIMELINE = tl; }}, {json.dumps(timeline, ensure_ascii=False)});
  await p.goto('file://{HERE}/shorts.html');
  await p.evaluate(() => window.ready);
  const times = {json.dumps(times)};
  for (let i = 0; i < times.length; i++) {{
    await p.evaluate(t => window.seek(t), times[i]);
    await p.screenshot({{ path: `{frames}/f${{String(i).padStart(5,'0')}}.jpg`, type: 'jpeg', quality: 92 }});
  }}
  await b.close();
}})();
"""
open(os.path.join(HERE, 'render.js'), 'w').write(js)
subprocess.run(['node', os.path.join(HERE, 'render.js')], check=True, cwd=HERE)
if TEST:
    print('test frames in', frames); sys.exit()

# ---- audio: 장면마다 시작 시각에 놓고 합치기
inputs, filt = [], []
for i, sc in enumerate(timeline):
    inputs += ['-i', sc['audio']]
    ms = int(sc['start'] * 1000)
    filt.append(f'[{i}:a]aresample=48000,adelay={ms}|{ms}[a{i}]')
mix = ''.join(f'[a{i}]' for i in range(len(timeline)))
filt.append(f'{mix}amix=inputs={len(timeline)}:normalize=0,apad,atrim=0:{TOTAL:.3f},loudnorm=I=-16:TP=-1.5:LRA=11[out]')
audio = os.path.join(HERE, 'mix.wav')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *inputs, '-filter_complex', ';'.join(filt), '-map', '[out]', '-ac', '2', '-ar', '48000', audio], check=True)

# ---- encode
os.makedirs(OUT, exist_ok=True)
name = f'KCT학원_홍보쇼츠_{VER}'
mp4 = os.path.join(OUT, name + '.mp4')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(frames, 'f%05d.jpg'), '-i', audio,
                '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                '-shortest', '-movflags', '+faststart', mp4], check=True)

# ---- srt
def ts(x):
    ms = int(round(x * 1000)); return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}'
cues = [c for sc in timeline for c in sc['chunks']]
with open(os.path.join(OUT, name + '.srt'), 'w') as f:
    for i, c in enumerate(cues, 1):
        f.write(f"{i}\n{ts(c['t0'])} --> {ts(c['t1'])}\n{c['text']}\n\n")
print('done', mp4)
