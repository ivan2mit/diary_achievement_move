"""Музыка к ролику: мягкий «космический» фон и колокольчики на события анимации.
Запуск: python3 music.py  →  assets/music.m4a (нужен afconvert из macOS).
Времена событий взяты из index.html; если тайминги сцен меняются, их нужно поправить и здесь."""
import math, struct, subprocess, wave, os
from array import array

SR, DUR = 32000, 98.5
N = int(SR * DUR)
pad, bells = array('d', bytes(8 * N)), array('d', bytes(8 * N))

NOTE = {n: 440 * 2 ** ((i - 57) / 12) for i, n in enumerate(
    f'{name}{octv}' for octv in range(0, 8) for name in ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])}


def osc(buf, start, env, freq, amp):
    """Синус по рекуррентной формуле (без вызова sin на каждый отсчёт), умноженный на готовую огибающую."""
    w = 2 * math.pi * freq / SR
    c, y1, y2 = 2 * math.cos(w), 0.0, -math.sin(w)
    n0 = int(start * SR)
    for i in range(min(len(env), N - n0)):
        y = c * y1 - y2
        y2, y1 = y1, y
        buf[n0 + i] += y * env[i] * amp


def chord(start, end, notes, amp=1.0, fade=3.0):
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
        osc(pad, t0, env, fr, a)
        osc(pad, t0, env, fr * 1.004, a * .8)
    osc(pad, t0, env, NOTE[notes[-1]] * 2, amp * .012)


def bell(t, name, amp=.16, tau=.9):
    """Колокольчик: основной тон и две быстро гаснущие обертоны."""
    fr = NOTE[name] if isinstance(name, str) else name
    for k, a, tk in ((1, 1.0, 1.0), (2.01, .3, .55), (3.02, .1, .3)):
        n, d = int(tau * tk * 5 * SR), math.exp(-1 / (tau * tk * SR))
        env, e, att = [0.0] * n, 1.0, int(.004 * SR)
        for i in range(n):
            env[i] = e * min(1.0, i / att)
            e *= d
        osc(bells, t, env, fr * k, amp * a)


def run(t, names, step=.09, amp=.09, tau=.5):
    for i, nm in enumerate(names):
        bell(t + i * step, nm, amp, tau)


# ---------- фон по сценам ----------
chord(0, 7, ['D3', 'A3', 'E4'], .75)                      # 1. хук: пустое небо
chord(7, 15, ['B2', 'F#3', 'D4'], .55)                    # 2. проблема: темнее и тише
chord(15, 20, ['D3', 'A3', 'D4', 'F#4', 'A4'], 1.0)       # 3. название
chord(20, 28.5, ['G2', 'D3', 'B3', 'A4'], .85)            # 4. звёзды
chord(28.5, 37, ['A2', 'E3', 'B3', 'E4'], .85)
chord(37, 43, ['B2', 'F#3', 'A3', 'D4'], .9)              # 5. планеты
chord(43, 49, ['G2', 'D3', 'F#3', 'B3'], .9)
chord(49, 57.5, ['D3', 'A3', 'F#4'], .8)                  # 6. созвездие: место для мелодии
chord(57.5, 64, ['A2', 'E3', 'C#4', 'E4'], .95)
chord(64, 72.5, ['G2', 'D3', 'B3', 'D4'], .9)             # 7. один счёт
chord(72.5, 80, ['D3', 'A3', 'D4', 'F#4', 'A4'], 1.0)
chord(80, 88, ['A2', 'E3', 'G3', 'B3', 'D4'], .9)         # 8. подарки
chord(88, 97.2, ['D2', 'A2', 'D3', 'F#3', 'A3', 'E4', 'F#4'], 1.05)   # 9. финал

# ---------- колокольчики на события ----------
bell(1.0, 'A5', .2, 1.6)                                  # первая звезда
bell(3.6, 'E5', .07, 1.2)
bell(7.25, 'D3', .2, .5)                                  # журнал лёг на небо
run(12.3, ['B5', 'A5', 'F#5', 'D5', 'B4', 'A4'], .16, .06, .5)        # клетки рассыпаются
for nm in ('D5', 'A5', 'D6'):                             # точки собрались в звезду
    bell(15.95, nm, .16, 1.8)
bell(23.4, 'F#5', .18, 1.2)                               # звёзды из телефона встают на небо
bell(25.6, 'A5', .18, 1.2); bell(25.72, 'D6', .1, 1.0)
for i, nm in enumerate(['D5', 'F#5', 'B4']):              # отметки: звезда, яркая, спящая
    bell(26.0 + i * .5, nm, .12, .8)
bell(27.5, 'A2', .22, .45); bell(27.5, 'A#3', .05, .3)    # астероид
bell(30.5, 'E5', .1, .8)                                  # × 2 академических часа
run(31.4, ['A5', 'B5', 'D6', 'A5'], .16, .07, .4)
bell(33.4, 'E5', .16, 1.2)
bell(37.3, 'A4', .08, .8)                                 # диплом
bell(39.8, 'D5', .18, 1.4)                                # Меркурий
for i, nm in enumerate(['E5', 'F#5', 'A5', 'B5', 'D6', 'E6', 'F#6']):  # остальные планеты
    bell(40.9 + (i + 1) * .52, nm, .13, 1.0)
bell(45.7, 'A4', .12, 1.2); bell(45.7, 'D5', .1, 1.2)     # Земля: за помощь
# созвездие: восемь главных звёзд складываются в мелодию, ракета — пауза
for t, nm in zip([50.5, 51.05, 51.6, 52.15, 52.7, 55.0, 55.55, 56.1], ['D5', 'E5', 'F#5', 'A5', 'B5', 'D6', 'B5', 'A5']):
    bell(t, nm, .19, 1.3)
bell(53.2, 'G4', .09, 1.0); bell(53.35, 'E4', .07, 1.2)   # путешественник
run(56.5, ['A6', 'B6', 'A6', 'F#6', 'A6', 'B6', 'D7'], .08, .04, .3)   # вспомогательные звёзды
for nm, a in (('D3', .16), ('D5', .16), ('F#5', .14), ('A5', .14), ('D6', .12)):   # награда
    bell(58.0, nm, a, 2.2)
run(60.5, ['B5', 'A5', 'F#5', 'E5', 'D5', 'B4'], .14, .07, .6)        # список созвездий
# звёзды слетаются в книжки, книжки — в цветок
for t, nm in zip([67.4, 67.6, 67.8, 68.0, 68.2, 68.4, 68.6, 68.8, 69.0, 69.2, 69.4, 69.6], ['A5', 'B5', 'D6', 'F#5', 'A5', 'B5', 'E5', 'F#5', 'A5', 'D5', 'E5', 'F#5']):
    bell(t, nm, .05, .5)
for t, nm in zip([68.55, 68.95, 69.35, 69.75], ['G4', 'B4', 'D5', 'F#5']):
    bell(t, nm, .15, 1.2)
for nm, a in (('D3', .16), ('D4', .12), ('A4', .13), ('D5', .15), ('F#5', .13), ('A5', .11)):   # цветок собран
    bell(73.1, nm, a, 2.4)
run(73.5, ['D5', 'E5', 'F#5', 'A5', 'B5', 'D6', 'E6', 'F#6', 'A6'], .18, .06, .7)   # рамка обегает цветок
run(75.1, ['A5'] * 12, .15, .03, .15)                     # счётчик
bell(77.0, 'D6', .16, 1.6)
for i, nm in enumerate(['A4', 'B4', 'D5']):               # шаги к подарку
    bell(80.95 + i * 1.3, nm, .13, 1.1)
bell(84.7, 'E5', .15, 1.2)
run(85.5, ['F#5', 'A5', 'B5', 'D6', 'F#6', 'A6', 'D7'], .07, .09, .8)  # коробка открылась
for nm, a in (('D2', .16), ('D4', .12), ('D5', .16), ('F#5', .14), ('A5', .13), ('D6', .11)):   # финал: цветок встал в небо
    bell(91.0, nm, a, 3.0)
run(89.6, ['A5', 'B5', 'D6', 'F#5', 'A5', 'E6'], .25, .06, .8)        # созвездия расходятся по небу
bell(92.6, 'A5', .1, 2.0); bell(94.0, 'D5', .08, 2.5)

# ---------- сведение: эхо на колокольчиках, лёгкое покачивание фона, общий уход в конце ----------
dl, dr, fb = int(.33 * SR), int(.47 * SR), .36
el, er = array('d', bytes(8 * N)), array('d', bytes(8 * N))
L, R = array('d', bytes(8 * N)), array('d', bytes(8 * N))
peak, fade0 = 0.0, int(96.2 * SR)
for i in range(N):
    b = bells[i]
    el[i] = (b + fb * er[i - dl]) if i >= dl else b       # эхо перекидывается между каналами
    er[i] = (b + fb * el[i - dr]) if i >= dr else b
    lfo = .12 * math.sin(2 * math.pi * .07 * i / SR)
    g = 1.0 if i < fade0 else max(0.0, 1 - (i - fade0) / (N - fade0)) ** 2
    L[i] = (pad[i] * (1 + lfo) + .75 * b + .5 * (el[i] - b)) * g
    R[i] = (pad[i] * (1 - lfo) + .75 * b + .5 * (er[i] - b)) * g
    peak = max(peak, abs(L[i]), abs(R[i]))
k = .88 / peak * 32767
here = os.path.dirname(os.path.abspath(__file__))
wav = os.path.join(here, 'assets', 'music.wav')
with wave.open(wav, 'wb') as f:
    f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
    f.writeframes(b''.join(struct.pack('<hh', int(L[i] * k), int(R[i] * k)) for i in range(N)))
subprocess.run(['afconvert', '-f', 'm4af', '-d', 'aac', '-b', '160000', wav, os.path.join(here, 'assets', 'music.m4a')], check=True)
os.remove(wav)
print('готово: assets/music.m4a, пик', round(peak, 3))
