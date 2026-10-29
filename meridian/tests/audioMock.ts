// Minimal mock of the Web Audio graph for unit tests: tracks connections,
// disconnections, automation calls and scheduled source stops. Time advances
// only through `advance()`, which also fires `onended` like a browser would.

export class MockParam {
  private v: number;
  automation = 0;
  directSets = 0;
  constructor(v = 0) {
    this.v = v;
  }
  get value(): number {
    return this.v;
  }
  set value(x: number) {
    this.v = x;
    this.directSets++;
  }
  setValueAtTime(x: number): this {
    this.automation++;
    this.v = x;
    return this;
  }
  linearRampToValueAtTime(x: number): this {
    this.automation++;
    this.v = x;
    return this;
  }
  exponentialRampToValueAtTime(x: number): this {
    this.automation++;
    this.v = x;
    return this;
  }
  setTargetAtTime(x: number): this {
    this.automation++;
    this.v = x;
    return this;
  }
  cancelScheduledValues(): this {
    this.automation++;
    return this;
  }
}

let nextNodeId = 1;

export class MockNode {
  readonly id = nextNodeId++;
  outputs = new Set<MockNode>();
  disconnected = false;
  constructor(readonly ctx: MockContext, readonly kind: string) {
    ctx.nodes.push(this);
  }
  connect(n: MockNode): MockNode {
    this.outputs.add(n);
    return n;
  }
  disconnect(): void {
    this.outputs.clear();
    this.disconnected = true;
  }
  params(): MockParam[] {
    return Object.values(this).filter((x): x is MockParam => x instanceof MockParam);
  }
}

export class MockGain extends MockNode {
  gain = new MockParam(1);
  constructor(ctx: MockContext) {
    super(ctx, 'gain');
  }
}

export class MockFilter extends MockNode {
  type = 'lowpass';
  frequency = new MockParam(350);
  Q = new MockParam(1);
  constructor(ctx: MockContext) {
    super(ctx, 'filter');
  }
}

export class MockCompressor extends MockNode {
  threshold = new MockParam(-24);
  knee = new MockParam(30);
  ratio = new MockParam(12);
  attack = new MockParam(0.003);
  release = new MockParam(0.25);
  constructor(ctx: MockContext) {
    super(ctx, 'compressor');
  }
}

export class MockSource extends MockNode {
  onended: (() => void) | null = null;
  startAt = -1;
  stopAt = Infinity;
  ended = false;
  constructor(ctx: MockContext, kind: string) {
    super(ctx, kind);
  }
  start(t = 0): void {
    if (this.startAt >= 0) throw new Error('start called twice');
    this.startAt = t;
  }
  stop(t = this.ctx.currentTime): void {
    if (this.startAt < 0) throw new Error('stop before start');
    this.stopAt = t;
  }
}

export class MockOsc extends MockSource {
  type = 'sine';
  frequency = new MockParam(440);
  constructor(ctx: MockContext) {
    super(ctx, 'osc');
  }
}

export class MockBufferSource extends MockSource {
  buffer: unknown = null;
  loop = false;
  constructor(ctx: MockContext) {
    super(ctx, 'buffer');
  }
}

export class MockAnalyser extends MockNode {
  fftSize = 2048;
  constructor(ctx: MockContext) {
    super(ctx, 'analyser');
  }
  getFloatTimeDomainData(b: Float32Array): void {
    b.fill(0);
  }
}

export class MockContext {
  currentTime = 0;
  sampleRate = 8000;
  state: 'running' | 'suspended' | 'closed' = 'running';
  nodes: MockNode[] = [];
  readonly destination: MockNode;
  constructor() {
    this.destination = new MockNode(this, 'destination');
  }
  createGain(): MockGain {
    return new MockGain(this);
  }
  createBiquadFilter(): MockFilter {
    return new MockFilter(this);
  }
  createDynamicsCompressor(): MockCompressor {
    return new MockCompressor(this);
  }
  createOscillator(): MockOsc {
    return new MockOsc(this);
  }
  createBufferSource(): MockBufferSource {
    return new MockBufferSource(this);
  }
  createAnalyser(): MockAnalyser {
    return new MockAnalyser(this);
  }
  createBuffer(_ch: number, len: number): { getChannelData(): Float32Array } {
    const d = new Float32Array(len);
    return { getChannelData: () => d };
  }
  suspend(): Promise<void> {
    this.state = 'suspended';
    return Promise.resolve();
  }
  resume(): Promise<void> {
    this.state = 'running';
    return Promise.resolve();
  }
  close(): Promise<void> {
    this.state = 'closed';
    return Promise.resolve();
  }
  /** Advance time; sources whose stop time has passed end and fire `onended`. */
  advance(dt: number): void {
    this.currentTime += dt;
    for (const n of this.nodes) {
      if (n instanceof MockSource && !n.ended && n.startAt >= 0 && n.stopAt <= this.currentTime) {
        n.ended = true;
        n.onended?.();
      }
    }
  }
  /** Total automation calls on every param of every node. */
  automationCount(): number {
    let c = 0;
    for (const n of this.nodes) for (const p of n.params()) c += p.automation;
    return c;
  }
  /** Is `to` reachable from `from` through connections? */
  reaches(from: MockNode, to: MockNode): boolean {
    const seen = new Set<MockNode>();
    const stack = [from];
    while (stack.length) {
      const n = stack.pop()!;
      if (n === to) return true;
      if (seen.has(n)) continue;
      seen.add(n);
      for (const o of n.outputs) stack.push(o);
    }
    return false;
  }
}
