// Покадровая выгрузка ролика в WebM: node render.js [fps] [файл]
// Нужны Playwright и его Chromium с ffmpeg (ставятся командой `npx playwright install chromium ffmpeg`).
// Пути ниже — к тому, что уже лежит в кэше на этой машине; при обновлении Playwright их нужно поправить.
const os = require('os'), path = require('path'), { spawn } = require('child_process');
const CACHE = path.join(os.homedir(), 'Library/Caches/ms-playwright');
const { chromium } = require(path.join(os.homedir(), '.npm/_npx/9833c18b2d85bc59/node_modules/playwright'));
const CHROME = path.join(CACHE, 'chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell');
const FFMPEG = path.join(CACHE, 'ffmpeg-1011/ffmpeg-mac');
const FPS = +process.argv[2] || 30, OUT = process.argv[3] || path.join(__dirname, 'ролик-v3.webm'), DUR = 98;

(async () => {
    const browser = await chromium.launch({ executablePath: CHROME });
    const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
    await page.goto('file://' + path.join(__dirname, 'index.html') + '?clean&t=0');
    await page.waitForFunction('window.ready === true');
    const ff = spawn(FFMPEG, ['-y', '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', String(FPS), '-i', 'pipe:0',
        '-c:v', 'vp8', '-b:v', '8M', '-qmin', '4', '-qmax', '24', '-deadline', 'good', '-cpu-used', '2', '-threads', '8', OUT],
        { stdio: ['pipe', 'ignore', 'ignore'] });
    ff.on('exit', (code) => { if (code) { console.error('ffmpeg завершился с кодом', code); process.exit(1); } });
    const total = Math.round(DUR * FPS);
    for (let i = 0; i <= total; i++) {
        await page.evaluate((t) => window.seek(t), i / FPS);
        const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
        if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
        if (i % 300 === 0) console.log(`кадр ${i} из ${total}`);
    }
    ff.stdin.end();
    await new Promise((r) => ff.on('close', r));
    await browser.close();
    console.log('готово:', OUT);
})().catch((e) => { console.error(e); process.exit(1); });
