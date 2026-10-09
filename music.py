"""Музыка к ролику, два варианта:
  1 — спокойный: мягкий фон и колокольчики на события анимации  → assets/music.m4a
  2 — динамичный: тот же материал с ритмом 120 ударов в минуту, который нарастает к финалу → assets/music2.m4a
Запуск: python3 music.py [1|2]  (без аргумента — оба). Нужен afconvert из macOS.
Времена событий взяты из index.html; если тайминги сцен меняются, их нужно поправить и здесь."""
import math, os, random, struct, subprocess, sys, wave
from array import array

SR, DUR = 32000, 98.5
N = int(SR * DUR)
NOTE = {n: 440 * 2 ** ((i - 57) / 12) for i, n in enumerate(
    f'{name}{octv}' for octv in range(0, 8) for name in ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])}
buf = lambda: array('d', bytes(8 * N))
_env = {}


def osc(out, start, env, freq, amp):
    """Синус по рекуррентной формуле (без вызова sin на каждый отсчёт), умноженный на готовую огибающую."""
    w = 2 * math.pi * freq / SR
    c, y1, y2 = 2 * math.cos(w), 0.0, -math.sin(w)
    n0 = int(start * SR)
    for i in range(min(len(env), N - n0)):
        y = c * y1 - y2
        y2, y1 = y1, y
        out[n0 + i] += y * env[i] * amp


def decay(tau, length=5.0, attack=.004):
    key = (tau, length, attack)
    if key not in _env:
        n, d, att = int(tau * length * SR), math.exp(-1 / (tau * SR)), max(1, int(attack * SR))
        env, e = [0.0] * n, 1.0
        for i in range(n):
            env[i] = e * min(1.0, i / att)
            e *= d
        _env[key] = env
    return _env[key]


def chord(out, start, end, notes, amp=1.0, fade=3.0):
    """Аккорд фона: медленное появление и уход, у каждого голоса чуть расстроенная пара."""
    t0, t1 = max(0, start - fade / 2), min(DUR, end + fade / 2)
    n, f = int((t1 - t0) * SR), int(fade * SR)
    env = [1.0] * n
    for i in range(min(f, n)):
        k = math.sin(math.pi / 2 * i / f) ** 2
        env[i] *= k
        env[n - 1 - i] *= k
    for j, name in enumerate(notes):
        fr = NOTE[name]
        a = amp * (.055 if j else .075) * min(1.0, 220 / fr) ** .35
        osc(out, t0, env, fr, a)
        osc(out, t0, env, fr * 1.004, a * .8)
    osc(out, t0, env, NOTE[notes[-1]] * 2, amp * .012)


def bell(out, t, name, amp=.16, tau=.9):
    """Колокольчик: основной тон и два быстро гаснущих обертона."""
    fr = NOTE[name] if isinstance(name, str) else name
    for k, a, tk in ((1, 1.0, 1.0), (2.01, .3, .55), (3.02, .1, .3)):
        osc(out, t, decay(round(tau * tk, 3), 4.5), fr * k, amp * a)


def events(out, q=lambda t: t, k=1.0):
    """Колокольчики на события анимации. q — привязка времени к ритмической сетке, k — общая громкость."""
    b = lambda t, nm, amp=.16, tau=.9: bell(out, q(t), nm, amp * k, tau)

    def run(t, names, step=.09, amp=.09, tau=.5):
        for i, nm in enumerate(names):
            b(t + i * step, nm, amp, tau)

    b(1.0, 'A5', .2, 1.6)                                  # первая звезда
    b(3.6, 'E5', .07, 1.2)
    b(7.25, 'D3', .2, .5)                                  # журнал лёг на небо
    run(12.3, ['B5', 'A5', 'F#5', 'D5', 'B4', 'A4'], .16, .06, .5)        # клетки рассыпаются
    for nm in ('D5', 'A5', 'D6'):                          # точки собрались в звезду
        b(15.95, nm, .16, 1.8)
    b(23.4, 'F#5', .18, 1.2)                               # звёзды из телефона встают на небо
    b(25.6, 'A5', .18, 1.2); b(25.72, 'D6', .1, 1.0)
    for i, nm in enumerate(['D5', 'F#5', 'B4']):           # отметки: звезда, яркая, спящая
        b(26.0 + i * .5, nm, .12, .8)
    b(27.5, 'A2', .22, .45); b(27.5, 'A#3', .05, .3)       # астероид
    b(30.5, 'E5', .1, .8)                                  # × 2 академических часа
    run(31.4, ['A5', 'B5', 'D6', 'A5'], .16, .07, .4)
    b(33.4, 'E5', .16, 1.2)
    b(37.3, 'A4', .08, .8)                                 # диплом
    b(39.8, 'D5', .18, 1.4)                                # Меркурий
    for i, nm in enumerate(['E5', 'F#5', 'A5', 'B5', 'D6', 'E6', 'F#6']):  # остальные планеты
        b(40.9 + (i + 1) * .52, nm, .13, 1.0)
    b(45.7, 'A4', .12, 1.2); b(45.7, 'D5', .1, 1.2)        # Земля: за помощь
    # созвездие: восемь главных звёзд складываются в мелодию, ракета — пауза
    for t, nm in zip([50.5, 51.05, 51.6, 52.15, 52.7, 55.0, 55.55, 56.1], ['D5', 'E5', 'F#5', 'A5', 'B5', 'D6', 'B5', 'A5']):
        b(t, nm, .19, 1.3)
    b(53.2, 'G4', .09, 1.0); b(53.35, 'E4', .07, 1.2)      # путешественник
    run(56.5, ['A6', 'B6', 'A6', 'F#6', 'A6', 'B6', 'D7'], .08, .04, .3)   # вспомогательные звёзды
    for nm, a in (('D3', .16), ('D5', .16), ('F#5', .14), ('A5', .14), ('D6', .12)):   # награда
        b(58.0, nm, a, 2.2)
    run(60.5, ['B5', 'A5', 'F#5', 'E5', 'D5', 'B4'], .14, .07, .6)        # список созвездий
    # звёзды слетаются в книжки, книжки — в цветок
    for t, nm in zip([67.4 + i * .2 for i in range(12)], ['A5', 'B5', 'D6', 'F#5', 'A5', 'B5', 'E5', 'F#5', 'A5', 'D5', 'E5', 'F#5']):
        b(t, nm, .05, .5)
    for t, nm in zip([68.55, 68.95, 69.35, 69.75], ['G4', 'B4', 'D5', 'F#5']):
        b(t, nm, .15, 1.2)
    for nm, a in (('D3', .16), ('D4', .12), ('A4', .13), ('D5', .15), ('F#5', .13), ('A5', .11)):   # цветок собран
        b(73.1, nm, a, 2.4)
    run(73.5, ['D5', 'E5', 'F#5', 'A5', 'B5', 'D6', 'E6', 'F#6', 'A6'], .18, .06, .7)   # рамка обегает цветок
    run(75.1, ['A5'] * 12, .15, .03, .15)                  # счётчик
    b(77.0, 'D6', .16, 1.6)
    for i, nm in enumerate(['A4', 'B4', 'D5']):            # шаги к подарку
        b(80.95 + i * 1.3, nm, .13, 1.1)
    b(84.7, 'E5', .15, 1.2)
    run(85.5, ['F#5', 'A5', 'B5', 'D6', 'F#6', 'A6', 'D7'], .07, .09, .8)  # коробка открылась
    run(89.6, ['A5', 'B5', 'D6', 'F#5', 'A5', 'E6'], .25, .06, .8)        # созвездия расходятся по небу
    for nm, a in (('D2', .16), ('D4', .12), ('D5', .16), ('F#5', .14), ('A5', .13), ('D6', .11)):   # цветок встал в небо
        b(91.0, nm, a, 3.0)
    b(92.6, 'A5', .1, 2.0); b(94.0, 'D5', .08, 2.5)


def mix(name, pad, wet, dry=None, fade_from=96.2, squash=0.0):
    """Сведение: эхо на «мокрой» шине, лёгкое покачивание фона, уход в конце, запись в m4a."""
    dl, dr, fb = int(.375 * SR), int(.5 * SR), .34          # эхо в долях такта при 120 ударах в минуту
    el, er, L, R = buf(), buf(), buf(), buf()
    peak, fade0 = 0.0, int(fade_from * SR)
    for i in range(N):
        b = wet[i]
        el[i] = (b + fb * er[i - dl]) if i >= dl else b     # эхо перекидывается между каналами
        er[i] = (b + fb * el[i - dr]) if i >= dr else b
        lfo = .12 * math.sin(2 * math.pi * .07 * i / SR)
        g = 1.0 if i < fade0 else max(0.0, 1 - (i - fade0) / (N - fade0)) ** 2
        d = dry[i] if dry else 0.0
        L[i] = (pad[i] * (1 + lfo) + .75 * b + .5 * (el[i] - b) + d) * g
        R[i] = (pad[i] * (1 - lfo) + .75 * b + .5 * (er[i] - b) + d) * g
        peak = max(peak, abs(L[i]), abs(R[i]))
    if squash:                                              # мягкое сжатие: тихие места громче, пики не перегружаются
        sq, top = squash / peak, math.tanh(squash)
        for i in range(N):
            L[i] = math.tanh(L[i] * sq) / top
            R[i] = math.tanh(R[i] * sq) / top
        peak = 1.0
    k = .88 / peak * 32767
    here = os.path.dirname(os.path.abspath(__file__))
    wav = os.path.join(here, 'assets', name + '.wav')
    with wave.open(wav, 'wb') as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes(b''.join(struct.pack('<hh', int(L[i] * k), int(R[i] * k)) for i in range(N)))
    subprocess.run(['afconvert', '-f', 'm4af', '-d', 'aac', '-b', '160000', wav, os.path.join(here, 'assets', name + '.m4a')], check=True)
    os.remove(wav)
    print(f'готово: assets/{name}.m4a, пик {peak:.3f}')


def calm():
    pad, wet = buf(), buf()
    c = lambda *a, **k: chord(pad, *a, **k)
    c(0, 7, ['D3', 'A3', 'E4'], .75)                       # 1. хук: пустое небо
    c(7, 15, ['B2', 'F#3', 'D4'], .55)                     # 2. проблема: темнее и тише
    c(15, 20, ['D3', 'A3', 'D4', 'F#4', 'A4'], 1.0)        # 3. название
    c(20, 28.5, ['G2', 'D3', 'B3', 'A4'], .85)             # 4. звёзды
    c(28.5, 37, ['A2', 'E3', 'B3', 'E4'], .85)
    c(37, 43, ['B2', 'F#3', 'A3', 'D4'], .9)               # 5. планеты
    c(43, 49, ['G2', 'D3', 'F#3', 'B3'], .9)
    c(49, 57.5, ['D3', 'A3', 'F#4'], .8)                   # 6. созвездие: место для мелодии
    c(57.5, 64, ['A2', 'E3', 'C#4', 'E4'], .95)
    c(64, 72.5, ['G2', 'D3', 'B3', 'D4'], .9)              # 7. один счёт
    c(72.5, 80, ['D3', 'A3', 'D4', 'F#4', 'A4'], 1.0)
    c(80, 88, ['A2', 'E3', 'G3', 'B3', 'D4'], .9)          # 8. подарки
    c(88, 97.2, ['D2', 'A2', 'D3', 'F#3', 'A3', 'E4', 'F#4'], 1.05)   # 9. финал
    events(wet)
    mix('music', pad, wet)


def drive():
    """Динамичный вариант: сетка 120 ударов в минуту (доля — 0,5 с), слои добавляются от сцены к сцене."""
    pad, wet, dry = buf(), buf(), buf()
    rnd = random.Random(7)
    CH = {   # аккорд: голоса фона, бас, ход арпеджио
        'Dsus': (['D3', 'A3', 'E4'], 'D2', ['D4', 'A4', 'E5', 'A4']),
        'D': (['D3', 'A3', 'D4', 'F#4'], 'D2', ['D4', 'A4', 'D5', 'F#5', 'A5', 'F#5', 'D5', 'A4']),
        'A': (['A2', 'E3', 'A3', 'C#4'], 'A2', ['A3', 'E4', 'A4', 'C#5', 'E5', 'C#5', 'A4', 'E4']),
        'Bm': (['B2', 'F#3', 'B3', 'D4'], 'B2', ['B3', 'F#4', 'B4', 'D5', 'F#5', 'D5', 'B4', 'F#4']),
        'G': (['G2', 'D3', 'G3', 'B3'], 'G2', ['G3', 'D4', 'G4', 'B4', 'D5', 'B4', 'G4', 'D4']),
        'Em': (['E3', 'B3', 'E4', 'G4'], 'E2', ['E4', 'B4', 'E5', 'G5', 'B5', 'G5', 'E5', 'B4']),
    }
    PLAN = [(0, 7, 'Dsus'), (7, 11, 'Bm'), (11, 15, 'G'), (15, 20, 'D'),
            (20, 24, 'D'), (24, 28, 'Bm'), (28, 32, 'G'), (32, 37, 'A'),
            (37, 41, 'Bm'), (41, 45, 'G'), (45, 47, 'D'), (47, 49, 'A'),
            (49, 53, 'D'), (53, 57, 'G'), (57, 61, 'D'), (61, 64, 'A'),
            (64, 66, 'D'), (66, 68, 'A'), (68, 70, 'Bm'), (70, 72, 'G'), (72, 73, 'A'),
            (73, 75, 'D'), (75, 77, 'A'), (77, 79, 'Bm'), (79, 80, 'G'),
            (80, 82, 'G'), (82, 84, 'D'), (84, 86, 'Em'), (86, 88, 'A'),
            (88, 90, 'Bm'), (90, 92, 'D'), (92, 94, 'G'), (94, 96, 'A'), (96, 98.5, 'D')]
    at = lambda t: next(nm for a, b, nm in PLAN if a <= t < b)
    grid = lambda a, b, step, off=0.0: [a + off + i * step for i in range(int(round((b - a - off) / step - 1e-9)) + 1) if a + off + i * step < b - 1e-9]
    lerp = lambda t, a, b, va, vb: va + (vb - va) * min(1, max(0, (t - a) / (b - a)))

    for a, b, nm in PLAN:                                   # фон тише, чем в спокойном варианте: место занимает ритм
        chord(pad, a, b, CH[nm][0], .75, 2.5 if b - a >= 4 else 1.0)

    def pluck(t, name, amp, tau=.14):
        fr = NOTE[name]
        osc(wet, t, decay(tau, 5), fr, amp)
        osc(wet, t, decay(tau * .5, 5), fr * 2, amp * .35)
        osc(wet, t, decay(tau * .3, 5), fr * 3, amp * .12)

    def bass(t, name, amp, tau=.22):
        fr = NOTE[name]
        osc(dry, t, decay(tau, 4, .006), fr, amp)
        osc(dry, t, decay(tau * .7, 4, .006), fr * 2, amp * .45)
        osc(dry, t, decay(tau * .4, 4, .006), fr * 3, amp * .15)

    def kick(t, amp):
        n0, ph = int(t * SR), 0.0
        for i in range(int(.26 * SR)):
            x = i / SR
            ph += 2 * math.pi * (46 + 95 * math.exp(-x / .028)) / SR
            dry[n0 + i] += math.sin(ph) * math.exp(-x / .11) * amp * .34

    def noise(t, length, tau, amp, hp=2):
        n0, p1, p2 = int(t * SR), 0.0, 0.0
        for i in range(min(int(length * SR), N - n0)):
            x = rnd.uniform(-1, 1)
            y = x - p1 if hp == 1 else x - 2 * p1 + p2       # грубый фильтр высоких частот
            p2, p1 = p1, x
            dry[n0 + i] += y * math.exp(-i / (tau * SR)) * amp

    hat = lambda t, amp: noise(t, .05, .011, amp * .028)
    def snare(t, amp):
        noise(t, .16, .045, amp * .07, 1)
        osc(dry, t, decay(.05, 4, .002), 196, amp * .09)
    def riser(a, b, amp):
        n0, n, p1 = int(a * SR), int((b - a) * SR), 0.0
        for i in range(n):
            x = rnd.uniform(-1, 1)
            dry[n0 + i] += (x - p1) * (i / n) ** 2.2 * amp * .09
            p1 = x

    # --- арпеджио: задаёт темп с первой секунды, к финалу чаще и громче
    for t in grid(1, 7, .5):
        pluck(t, CH['Dsus'][2][int(t * 2) % 4], .05, .2)
    for t in grid(7, 15, 1.0):                              # сцена 2: только редкий глухой пульс
        pluck(t, 'B3' if t < 11 else 'G3', .06, .25)
    for a, b, step in ((15, 53, .25), (55, 64, .25), (64, 72, .125), (73, 88, .125), (88, 96, .125)):
        for t in grid(a, b, step):
            pat = CH[at(t)][2]
            amp = lerp(t, 15, 20, .03, .06) if t < 20 else lerp(t, 20, 96, .06, .09)
            if step == .125: amp *= .8 if int(round(t * 8)) % 2 else 1.0
            pluck(t, pat[int(round(t / step)) % len(pat)], amp)
            if t >= 88 and int(round(t * 8)) % 4 == 0:      # финал: верхняя октава на сильные доли
                fr = pat[0][:-1] + str(int(pat[0][-1]) + 2)
                pluck(t, fr, amp * .6, .2)
    # --- бас
    for a, b, step, amp in ((20, 37, .5, .15), (37, 53, .5, .19), (55, 64, .5, .2), (64, 72, .25, .2), (73, 88, .25, .22), (88, 96, .25, .25)):
        for t in grid(a, b, step):
            root = CH[at(t)][1]
            up = step == .25 and int(round(t * 4)) % 2 == 1  # на слабую долю — октавой выше
            bass(t, root[:-1] + str(int(root[-1]) + 1) if up else root, amp * (.7 if up else 1))
    # --- ударные
    for t in grid(20, 37, 1.0): kick(t, .45)
    for a, b, amp in ((37, 53, .6), (55, 64, .7), (64, 72, .85), (73, 87.5, .92), (88, 96, 1.0)):
        for t in grid(a, b, .5): kick(t, amp)
    for t in grid(28, 53, .5, .25) + grid(55, 64, .5, .25): hat(t, .7)
    for t in grid(64, 72, .25) + grid(73, 88, .25): hat(t, 1.0 if int(round(t * 4)) % 2 else .6)
    for t in grid(88, 96, .125): hat(t, 1.0 if int(round(t * 8)) % 4 == 2 else .5)
    for t in grid(55, 64, 2.0, 1.5): snare(t, .6)
    for t in grid(64, 72, 1.0, .5) + grid(73, 87.5, 1.0, .5) + grid(88, 96, 1.0, .5): snare(t, .85 if t < 88 else 1.0)
    for t in (87.625, 87.75, 87.875, 95.5, 95.625, 95.75, 95.875): snare(t, .7)   # сбивки перед финалом и перед последним аккордом
    riser(71, 73.1, 1.0); riser(86.5, 88, 1.1); riser(94.5, 96, 1.0)
    for t in (64, 73.125, 88, 96):                          # акценты: тарелка
        noise(t, 1.6, .45, .05)
    # --- последний аккорд: ритм обрывается, звучит один ре мажор
    kick(96, 1.1)
    for nm, a in (('D2', .2), ('D3', .16), ('A3', .12), ('D4', .13), ('F#4', .12), ('A4', .12), ('D5', .14), ('F#5', .11), ('A5', .09), ('D6', .08)):
        bell(wet, 96, nm, a, 2.2)
    events(wet, q=lambda t: round(t * 8) / 8, k=.9)         # колокольчики привязаны к сетке шестнадцатых
    mix('music2', pad, wet, dry, fade_from=97.2, squash=2.4)


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'both'
    if which in ('1', 'both'): calm()
    if which in ('2', 'both'): drive()
