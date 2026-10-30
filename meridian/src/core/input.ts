// Keyboard/mouse input. Only active while the game is in a playing state so
// menus keep normal text/keyboard behavior. Edge presses are latched until a
// simulation step consumes them; held keys are cleared on blur/pause/mode change.

const GAME_KEYS = new Set([
  'KeyW', 'KeyA', 'KeyS', 'KeyD', 'KeyQ', 'KeyE', 'KeyX', 'KeyL', 'KeyG', 'KeyF', 'KeyT', 'KeyR', 'KeyC',
  'Space', 'ControlLeft', 'ControlRight', 'ShiftLeft', 'ShiftRight', 'Tab',
  'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight',
]);

/** Mouse buttons as input codes (event.button 0, 1, 2); tracked only while the pointer is locked. */
const MOUSE_CODES = ['MouseLeft', 'MouseMiddle', 'MouseRight'];

export class Input {
  readonly held = new Set<string>();
  private readonly pressed = new Set<string>();
  private mdx = 0;
  private mdy = 0;
  /** True when keyboard/mouse events should drive the game. */
  active = false;
  pointerLocked = false;
  pointerLockSupported = true;
  private dragging = false;
  /** Virtual input injected by test hooks (merged with real input). */
  readonly injected = new Set<string>();
  private canvas: HTMLElement | null = null;
  onPointerLockLost: (() => void) | null = null;
  onEscape: (() => void) | null = null;
  /** Tab handler; returns true when the game used the key (menus keep normal focus order). */
  onTab: ((repeat: boolean) => boolean) | null = null;

  attach(canvas: HTMLElement): void {
    this.canvas = canvas;
    this.pointerLockSupported = 'requestPointerLock' in canvas;
    window.addEventListener('keydown', this.onKeyDown);
    window.addEventListener('keyup', this.onKeyUp);
    window.addEventListener('blur', this.clearAll);
    document.addEventListener('pointerlockchange', this.onLockChange);
    document.addEventListener('pointerlockerror', this.onLockError);
    document.addEventListener('mousemove', this.onMouseMove);
    canvas.addEventListener('mousedown', this.onMouseDown);
    window.addEventListener('mouseup', this.onMouseUp);
    canvas.addEventListener('contextmenu', (e) => e.preventDefault());
  }

  private isTextTarget(t: EventTarget | null): boolean {
    if (!(t instanceof HTMLElement)) return false;
    const tag = t.tagName;
    return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || t.isContentEditable;
  }

  private onKeyDown = (e: KeyboardEvent): void => {
    if (this.isTextTarget(e.target)) return;
    if (e.code === 'Escape') {
      this.onEscape?.();
      return;
    }
    if (e.code === 'Tab') {
      if (this.onTab?.(e.repeat)) e.preventDefault();
      return;
    }
    if (!this.active) return;
    if (GAME_KEYS.has(e.code)) {
      e.preventDefault();
      if (!e.repeat && !this.held.has(e.code)) this.pressed.add(e.code);
      this.held.add(e.code);
    }
  };

  private onKeyUp = (e: KeyboardEvent): void => {
    this.held.delete(e.code);
  };

  private onMouseMove = (e: MouseEvent): void => {
    if (!this.active) return;
    // Some browsers report one large bogus delta right after locking.
    if (performance.now() - this.lockedAt < 150) return;
    if (this.pointerLocked || this.dragging) {
      // Guard against occasional huge spikes some browsers emit on lock.
      const dx = Math.max(-300, Math.min(300, e.movementX || 0));
      const dy = Math.max(-300, Math.min(300, e.movementY || 0));
      this.mdx += dx;
      this.mdy += dy;
    }
  };

  private onMouseDown = (e: MouseEvent): void => {
    if (!this.active) return;
    const code = this.pointerLocked ? MOUSE_CODES[e.button] : undefined;
    if (code) {
      if (!this.held.has(code)) this.pressed.add(code);
      this.held.add(code);
    }
    if (!this.pointerLocked) {
      if (this.pointerLockSupported) this.requestLock();
      // Drag-look fallback works while the button is held.
      this.dragging = true;
      e.preventDefault();
    }
  };

  private onMouseUp = (e: MouseEvent): void => {
    this.dragging = false;
    const code = MOUSE_CODES[e.button];
    if (code) this.held.delete(code);
  };

  private lockedAt = 0;

  private onLockChange = (): void => {
    const locked = document.pointerLockElement === this.canvas;
    const was = this.pointerLocked;
    this.pointerLocked = locked;
    if (locked && !was) {
      this.lockedAt = performance.now();
      this.mdx = 0;
      this.mdy = 0;
    }
    if (was && !locked) {
      this.clearAll();
      this.onPointerLockLost?.();
    }
  };

  private onLockError = (): void => {
    this.pointerLocked = false;
  };

  requestLock(): void {
    if (!this.canvas || !this.pointerLockSupported) return;
    try {
      const r = (this.canvas as HTMLCanvasElement).requestPointerLock() as unknown;
      if (r && typeof (r as Promise<void>).catch === 'function') {
        (r as Promise<void>).catch(() => {
          this.pointerLocked = false;
        });
      }
    } catch {
      this.pointerLocked = false;
    }
  }

  releaseLock(): void {
    if (document.pointerLockElement) document.exitPointerLock();
  }

  isDown(code: string): boolean {
    return this.held.has(code) || this.injected.has(code);
  }

  /** Consume an edge press (returns true once per physical press). */
  consume(code: string): boolean {
    if (this.pressed.has(code)) {
      this.pressed.delete(code);
      return true;
    }
    return false;
  }

  /** Inject an edge press (test hooks / UI buttons). */
  press(code: string): void {
    this.pressed.add(code);
  }

  /** Read and reset accumulated mouse delta (pixels). */
  takeMouse(): [number, number] {
    const r: [number, number] = [this.mdx, this.mdy];
    this.mdx = 0;
    this.mdy = 0;
    return r;
  }

  clearAll = (): void => {
    this.held.clear();
    this.pressed.clear();
    this.mdx = 0;
    this.mdy = 0;
    this.dragging = false;
  };

  /** Clear latched presses only (e.g. on mode change). */
  clearPresses(): void {
    this.pressed.clear();
  }
}
