import type { Settings } from '../game/settings';
import type { QualityPreset } from '../game/config';

export interface MenuHandlers {
  onNew(): void;
  onContinue(): void;
  onContinuePrevious(): void;
  onResume(): void;
  onSave(): void;
  onLoad(): void;
  onRecover(): void;
  onExport(): void;
  onImport(file: File): void;
  onQuitToTitle(): void;
  onSettingsChanged(s: Settings): void;
  onRetry(): void;
}

type Screen = 'title' | 'pause' | 'settings' | 'controls' | 'error' | 'loading' | 'none';

const $ = <T extends HTMLElement = HTMLElement>(id: string): T => {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Missing element #${id}`);
  return el as T;
};

export class Menus {
  private screen: Screen = 'title';
  private returnTo: Screen = 'title';
  private settings: Settings;
  private readonly screens: Record<Exclude<Screen, 'none'>, HTMLElement>;

  constructor(private readonly h: MenuHandlers, initial: Settings) {
    this.settings = { ...initial };
    this.screens = {
      title: $('screen-title'),
      pause: $('screen-pause'),
      settings: $('screen-settings'),
      controls: $('screen-controls'),
      error: $('screen-error'),
      loading: $('screen-loading'),
    };
    const click = (id: string, fn: () => void) => $(id).addEventListener('click', (e) => { e.preventDefault(); fn(); });
    click('btn-new', () => h.onNew());
    click('btn-continue', () => h.onContinue());
    click('btn-continue-prev', () => h.onContinuePrevious());
    click('btn-resume', () => h.onResume());
    click('btn-save', () => h.onSave());
    click('btn-load', () => h.onLoad());
    click('btn-recover', () => h.onRecover());
    click('btn-export', () => h.onExport());
    click('btn-title', () => h.onQuitToTitle());
    click('btn-retry', () => h.onRetry());
    click('btn-settings', () => this.openSub('settings'));
    click('btn-settings-title', () => this.openSub('settings'));
    click('btn-controls', () => this.openSub('controls'));
    click('btn-controls-title', () => this.openSub('controls'));
    click('btn-settings-back', () => this.closeSub());
    click('btn-controls-back', () => this.closeSub());
    const file = $<HTMLInputElement>('file-import');
    click('btn-import', () => file.click());
    click('btn-import-title', () => file.click());
    file.addEventListener('change', () => {
      const f = file.files?.[0];
      if (f) h.onImport(f);
      file.value = '';
    });
    this.bindSettings();
  }

  get current(): Screen {
    return this.screen;
  }

  show(screen: Screen): void {
    this.screen = screen;
    for (const [k, el] of Object.entries(this.screens)) el.classList.toggle('hidden', k !== screen);
    const focusId = screen === 'pause' ? 'btn-resume' : screen === 'error' ? 'btn-retry' : null;
    if (focusId) ($(focusId) as HTMLButtonElement).focus({ preventScroll: true });
  }

  private openSub(s: 'settings' | 'controls'): void {
    this.returnTo = this.screen === 'settings' || this.screen === 'controls' ? this.returnTo : this.screen;
    this.renderSettings();
    this.show(s);
  }

  /** Close settings/controls back to the screen that opened them. Returns false if not in a sub-screen. */
  closeSub(): boolean {
    if (this.screen !== 'settings' && this.screen !== 'controls') return false;
    this.show(this.returnTo);
    return true;
  }

  setTitleStatus(text: string, ready: boolean): void {
    $('title-status').textContent = text;
    ($('btn-new') as HTMLButtonElement).disabled = !ready;
  }

  setContinueAvailable(available: boolean, note = '', isError = false): void {
    $('btn-continue').classList.toggle('hidden', !available);
    this.setTitleNote(note, isError);
  }

  setPreviousAvailable(available: boolean): void {
    $('btn-continue-prev').classList.toggle('hidden', !available);
  }

  setTitleNote(text: string, isError = false): void {
    const el = $('title-save-note');
    el.textContent = text;
    el.classList.toggle('error', isError);
  }

  /** Read-only history line for a save from an earlier version (null hides it). */
  setLegacy(text: string | null): void {
    const el = $('title-legacy');
    el.textContent = text ?? '';
    el.classList.toggle('hidden', !text);
  }

  setPauseStatus(text: string, isError = false): void {
    const el = $('pause-status');
    el.textContent = text;
    el.classList.toggle('error', isError);
  }

  showError(title: string, text: string, canRetry = true): void {
    $('error-title').textContent = title;
    $('error-text').textContent = text;
    $('btn-retry').classList.toggle('hidden', !canRetry);
    this.show('error');
  }

  setLoading(text: string): void {
    $('loading-text').textContent = text;
  }

  private bindSettings(): void {
    const preset = $<HTMLSelectElement>('set-preset');
    const auto = $<HTMLInputElement>('set-auto');
    const sens = $<HTMLInputElement>('set-sens');
    const inv = $<HTMLInputElement>('set-invert');
    const vol = $<HTMLInputElement>('set-volume');
    const red = $<HTMLInputElement>('set-reduced');
    const emit = () => {
      this.settings = {
        preset: preset.value as QualityPreset,
        adaptive: auto.checked,
        sensitivity: parseFloat(sens.value),
        invertY: inv.checked,
        volume: parseFloat(vol.value),
        reducedMotion: red.checked,
      };
      this.renderSettings();
      this.h.onSettingsChanged({ ...this.settings });
    };
    for (const el of [preset, auto, inv, red]) el.addEventListener('change', emit);
    for (const el of [sens, vol]) el.addEventListener('input', emit);
  }

  setSettings(s: Settings): void {
    this.settings = { ...s };
    this.renderSettings();
  }

  setSettingsNote(text: string): void {
    $('settings-note').textContent = text;
  }

  private renderSettings(): void {
    const s = this.settings;
    $<HTMLSelectElement>('set-preset').value = s.preset;
    $<HTMLInputElement>('set-auto').checked = s.adaptive;
    $<HTMLInputElement>('set-sens').value = String(s.sensitivity);
    $('set-sens-v').textContent = s.sensitivity.toFixed(2);
    $<HTMLInputElement>('set-invert').checked = s.invertY;
    $<HTMLInputElement>('set-volume').value = String(s.volume);
    $('set-volume-v').textContent = `${Math.round(s.volume * 100)}%`;
    $<HTMLInputElement>('set-reduced').checked = s.reducedMotion;
  }
}
