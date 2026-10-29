import { RenderSystem, WebGL2UnavailableError } from '../render/RenderSystem';
import { initPhysics } from '../physics/Physics';
import { Menus } from '../ui/Menus';
import { DEFAULT_SETTINGS, sanitizeSettings, type Settings } from './settings';
import { KvStore } from '../save/db';
import { SaveStore, exportJson, importJson, type SaveData } from '../save/SaveSystem';
import { Game } from './Game';
import { Panel } from '../ui/Panel';
import { renderJournal, renderSurvey } from '../ui/Journal';
import { BODIES, BODY_IDS, CORE_BODY_IDS, EXTENDED_BODY_IDS } from '../world/bodies';

function when(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? 'unknown time' : d.toLocaleString();
}

function summary(d: SaveData): string {
  const e = d.expedition;
  if (e.extendedTransmitted) return 'both surveys transmitted';
  const ext = e.relays.filter((b) => BODIES[b].survey === 'extended').length;
  if (e.transmitted) return `survey transmitted · extended ${ext}/${EXTENDED_BODY_IDS.length} relays`;
  return `${e.relays.length - ext}/${CORE_BODY_IDS.length} relays · ${e.species.length} species logged`;
}

/** Application entry: compatibility checks, async init, and wiring of menus to the game. */
export async function boot(): Promise<void> {
  const canvas = document.getElementById('view') as HTMLCanvasElement;
  let settings: Settings = { ...DEFAULT_SETTINGS };
  let kv: KvStore | null = null;
  let game: Game | null = null;
  let saves = new SaveStore(null);

  /** Start (or continue) play from a user gesture: audio and pointer lock need one. */
  const startPlay = (g: Game) => {
    g.audio.start(settings.volume);
    g.audio.setMix(settings.music, settings.effects);
    g.input.requestLock();
  };

  const restore = (g: Game, data: SaveData) => {
    g.restore(data);
    startPlay(g);
  };

  // Writes are serialized; a request during a write is coalesced into one more write.
  let writing = false;
  let again = false;
  const writeSave = async (manual: boolean): Promise<void> => {
    const g = game;
    if (!g) return;
    if (!saves.available) {
      g.hud.saveStatus('Saving unavailable — use Export Backup', true);
      if (manual) menus.setPauseStatus('Browser storage is unavailable: progress is not saved. Export Backup still works.', true);
      return;
    }
    if (writing) {
      again = true;
      return;
    }
    writing = true;
    const data = g.snapshot();
    const ok = await saves.write(data);
    writing = false;
    if (ok) {
      g.markSaved(data);
      g.hud.saveStatus('Saved');
      if (manual) menus.setPauseStatus(`Saved ${when(data.savedAt)}.`);
    } else {
      g.hud.saveStatus(`Save failed — ${saves.failure ?? 'unknown error'}`, true);
      menus.setPauseStatus(`${saves.failure ?? 'Saving failed.'} Your previous save is unchanged. Use Export Backup to keep progress.`, true);
    }
    if (again) {
      again = false;
      void writeSave(false);
    }
  };

  const download = (name: string, text: string) => {
    const blob = new Blob([text], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  const menus = new Menus(
    {
      onNew: () => {
        if (!game) return;
        game.newExpedition();
        game.beginPlay();
        startPlay(game);
      },
      onContinue: () => {
        if (game && saves.latest.data) restore(game, saves.latest.data);
      },
      onContinuePrevious: () => {
        if (game && saves.previous.data) restore(game, saves.previous.data);
      },
      onResume: () => {
        if (!game) return;
        game.setState('playing');
        startPlay(game);
      },
      onSave: () => void writeSave(true),
      onLoad: () => {
        if (!game) return;
        const d = saves.latest.data;
        if (!d) {
          menus.setPauseStatus('There is no save to load yet.', true);
          return;
        }
        restore(game, d);
      },
      onRecover: () => game?.recover(),
      onExport: () => {
        if (!game) return;
        const data = game.snapshot();
        download(`meridian-backup-${data.savedAt.slice(0, 19).replace(/[:T]/g, '-')}.json`, exportJson(data));
        menus.setPauseStatus('Backup exported.');
      },
      onImport: (file) => {
        void file.text().then((text) => {
          const r = importJson(text);
          if (!r.ok) {
            const msg = `Import failed: ${r.error}`;
            menus.setPauseStatus(msg, true);
            menus.setTitleNote(msg, true);
            return;
          }
          if (!game) return;
          restore(game, r.data);
          game.hud.notice('Backup imported', `Restored a save from ${when(r.data.savedAt)}.`, true);
          void writeSave(false);
        });
      },
      onQuitToTitle: () => {
        game?.setState('title');
        refreshTitle();
      },
      onSettingsChanged: (s) => {
        const presetChanged = s.preset !== settings.preset;
        const adaptiveChanged = s.adaptive !== settings.adaptive;
        settings = s;
        if (game) {
          game.settings = s;
          game.audio.setVolume(s.volume);
          game.audio.setMix(s.music, s.effects);
          if (presetChanged) {
            game.applyPreset(s.preset);
            menus.setSettingsNote('Preset applied. Sky and terrain shader detail and the antialiasing mode switch fully after a reload.');
          } else if (adaptiveChanged) {
            game.adaptive.reset(s.preset === 'low' ? 33.3 : 16.7);
            game.applyAdaptive();
          }
        }
        void kv?.put('settings', s).catch(() => {});
      },
      onRetry: () => location.reload(),
    },
    settings,
  );

  /** Title-screen save state: continue, previous save, or an honest storage note. */
  const refreshTitle = () => {
    const l = saves.latest;
    const p = saves.previous;
    if (!saves.available) {
      menus.setContinueAvailable(false, 'Browser storage is unavailable — progress cannot be saved this session. Backup export and import still work.', true);
      menus.setPreviousAvailable(false);
    } else if (l.data) {
      menus.setContinueAvailable(true, `Last saved ${when(l.data.savedAt)} · ${summary(l.data)}`);
      menus.setPreviousAvailable(false);
    } else if (l.present) {
      menus.setContinueAvailable(
        false,
        `The latest save could not be loaded (${l.error}). It is kept aside unchanged. ${p.data ? 'Load the previous save or start' : 'Start'} a new expedition.`,
        true,
      );
      menus.setPreviousAvailable(!!p.data);
    } else {
      menus.setContinueAvailable(false, saves.failure ?? '');
      menus.setPreviousAvailable(false);
    }
  };

  menus.show('title');
  menus.setTitleStatus('Initializing renderer…', false);

  try {
    kv = await KvStore.open();
    settings = sanitizeSettings(await kv.get('settings'));
    menus.setSettings(settings);
  } catch {
    kv = null;
  }
  saves = new SaveStore(kv);
  await saves.read();
  refreshTitle();

  // Safe-mode overrides, e.g. ?preset=low when a heavier preset is too slow to
  // reach the menu, or ?adaptive=0 to pin the preset's full resolution.
  const params = new URLSearchParams(location.search);
  const forced = params.get('preset');
  if (forced === 'low' || forced === 'balanced' || forced === 'high') {
    settings = { ...settings, preset: forced };
    menus.setSettings(settings);
  }
  if (params.get('adaptive') === '0') {
    settings = { ...settings, adaptive: false };
    menus.setSettings(settings);
  }

  let render: RenderSystem;
  try {
    render = new RenderSystem(canvas, settings.preset);
  } catch (e) {
    const isGl = e instanceof WebGL2UnavailableError;
    menus.showError(
      isGl ? 'WebGL 2 is required' : 'Renderer failed to start',
      isGl
        ? 'MERIDIAN needs a browser with WebGL 2 enabled (current Chrome, Edge, Firefox or Safari). Check that hardware acceleration is turned on, then retry.'
        : `The graphics context could not be created: ${(e as Error).message}`,
    );
    return;
  }

  menus.setTitleStatus('Initializing physics…', false);
  try {
    await initPhysics();
  } catch (e) {
    menus.showError('Physics failed to start', `The physics engine (WebAssembly) could not be initialized: ${(e as Error).message}`);
    return;
  }

  game = new Game(render, settings);
  const panel = new Panel();
  const closePanel = () => {
    if (!game || game.state !== 'panel') return;
    game.setState('playing');
    game.input.requestLock();
  };
  panel.onClose = closePanel;
  panel.onSetCourse = (id) => game?.setNavTarget(id);
  panel.view = () => {
    const g = game!;
    const sys = g.ship.currPos.clone().add(g.origin);
    const e = g.expedition;
    return {
      target: g.navTarget,
      here: g.ref.id,
      rows: BODY_IDS.map((id) => {
        const def = BODIES[id];
        const d = Math.hypot(sys.x - def.center[0], sys.y - def.center[1], sys.z - def.center[2]) - def.radius;
        const pending = def.survey === 'extended' ? 'Extended survey' : 'Survey pending';
        return { id, distance: d, status: e.relayActive(id) ? 'Relay active' : pending };
      }),
    };
  };
  panel.renderJournal = (el) => renderJournal(el, game!.expedition.state);
  panel.renderSurvey = (el) => renderSurvey(el, game!.expedition);
  // Tab opens the panel in play and closes it again; elsewhere it keeps its
  // normal focus behaviour.
  game.input.onTab = (repeat) => {
    if (game?.state === 'playing') {
      if (!repeat) game.setState('panel');
      return true;
    }
    if (game?.state === 'panel') {
      if (!repeat) closePanel();
      return true;
    }
    return false;
  };
  game.input.onEscape = () => {
    if (!game) return;
    if (game.state === 'panel') {
      closePanel();
      return;
    }
    if (menus.closeSub()) return;
    if (game.state === 'playing') game.setState('paused');
    else if (game.state === 'paused' && performance.now() - game.pausedAt > 500) {
      // Chrome delivers the Escape keydown that also released pointer lock;
      // ignore it so one press doesn't pause and immediately resume.
      game.setState('playing');
      game.input.requestLock();
    }
  };
  game.input.onPointerLockLost = () => {
    if (game?.state === 'playing') game.setState('paused');
  };
  game.onStateChange = (s) => {
    if (s === 'panel') panel.show();
    else panel.hide();
    if (s === 'playing' || s === 'panel') menus.show('none');
    else if (s === 'paused') {
      menus.setPauseStatus(saves.available ? '' : 'Browser storage is unavailable: progress is not saved. Export Backup still works.', !saves.available);
      menus.show('pause');
    } else if (s === 'title') menus.show('title');
    else if (s === 'loading') menus.show('loading');
    document.getElementById('hud')?.classList.toggle('hidden', s !== 'playing' && s !== 'paused' && s !== 'panel');
  };
  game.onLoadingProgress = (text) => menus.setLoading(text);
  game.onNotice = (title, text, teal) => game?.hud.notice(title, text, teal);
  game.onAutosave = () => void writeSave(false);
  // An extra best-effort save when the tab is hidden (never the only save).
  document.addEventListener('visibilitychange', () => {
    if (document.hidden && game && game.state !== 'title' && game.saveDirty()) void writeSave(false);
  });
  canvas.addEventListener('webglcontextlost', (e) => {
    e.preventDefault();
    menus.showError('Graphics context lost', 'The browser reset the graphics device. Your last save is intact; retry to reload.');
  });
  if (__TEST_HOOKS__) {
    const { installTestHooks } = await import('../debug/testHooks');
    installTestHooks(game, { saves: () => saves });
  }
  game.start();
  menus.setTitleStatus('Ready.', true);
  if (__TEST_HOOKS__) (window as unknown as { __meridianBooted?: boolean }).__meridianBooted = true;
}
