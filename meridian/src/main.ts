import './ui/styles.css';
import { boot } from './game/boot';

boot().catch((e: unknown) => {
  // Last-resort error surface: never leave a black screen.
  const el = document.getElementById('screen-error');
  const t = document.getElementById('error-text');
  if (el && t) {
    t.textContent = `Startup failed: ${e instanceof Error ? e.message : String(e)}`;
    el.classList.remove('hidden');
    document.getElementById('screen-title')?.classList.add('hidden');
  }
  console.error(e);
});
