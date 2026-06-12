import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

const require = createRequire(import.meta.url);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const htmlPath = path.join(__dirname, "relay-rules-flowcharts.html");
const outputs = [
  ["#flow-en", "relay-rules-flow-en.png"],
  ["#flow-zh", "relay-rules-flow-zh.png"],
];

const { chromium } = require("/Users/ct/node_modules/playwright");

const browser = await chromium.launch({
  headless: true,
  executablePath: "/Users/ct/Library/Caches/ms-playwright/chromium_headless_shell-1187/chrome-mac/headless_shell",
});
try {
  const page = await browser.newPage({
    viewport: { width: 1900, height: 1400 },
    deviceScaleFactor: 2,
  });
  await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  for (const [selector, filename] of outputs) {
    const element = page.locator(selector);
    await element.screenshot({
      path: path.join(__dirname, filename),
      animations: "disabled",
    });
    console.log(path.join(__dirname, filename));
  }
} finally {
  await browser.close();
}
