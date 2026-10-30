// Fetches heliocentric J2000-ecliptic position vectors at EPOCH from JPL
// Horizons and rebuilds src/data/sol.json with them (task W1).
// Needs network access to ssd.jpl.nasa.gov. Usage (inside meridian/):
//   node scripts/data/horizons.mjs && python3 -I scripts/data/build_sol.py scripts/data/horizons-vectors.json > src/data/sol.json
import { writeFileSync } from 'node:fs';

const EPOCH = '2026-01-01 00:00'; // TDB, JD 2461041.5 (keep equal to scale.ts EPOCH)
const IDS = { mercury: 199, venus: 299, earth: 399, moon: 301, mars: 499, jupiter: 599, europa: 502, saturn: 699, titan: 606, uranus: 799, neptune: 899 };
const API = 'https://ssd.jpl.nasa.gov/api/horizons.api';

export function parseVectors(text) {
  const s = text.indexOf('$$SOE');
  const e = text.indexOf('$$EOE');
  if (s < 0 || e < 0) throw new Error('no $$SOE/$$EOE block');
  const row = text.slice(s + 5, e).trim().split('\n')[0].split(',').map((x) => x.trim());
  // CSV: JDTDB, Calendar Date (TDB), X, Y, Z,
  const v = [Number(row[2]), Number(row[3]), Number(row[4])];
  if (!v.every(Number.isFinite)) throw new Error(`bad vector row: ${row.join(',')}`);
  return { jd: Number(row[0]), v };
}

async function main() {
  const vectors = {};
  const notes = {};
  for (const [name, id] of Object.entries(IDS)) {
    const q = new URLSearchParams({
      format: 'text', COMMAND: `'${id}'`, OBJ_DATA: 'YES', MAKE_EPHEM: 'YES', EPHEM_TYPE: 'VECTORS', CENTER: "'500@10'",
      START_TIME: `'${EPOCH}'`, STOP_TIME: `'2026-01-01 00:01'`, STEP_SIZE: "'1'", VEC_TABLE: "'1'", REF_PLANE: "'ECLIPTIC'",
      REF_SYSTEM: "'ICRF'", OUT_UNITS: "'KM-S'", CSV_FORMAT: "'YES'", TIME_TYPE: "'TDB'",
    });
    const res = await fetch(`${API}?${q}`);
    if (!res.ok) throw new Error(`${name}: HTTP ${res.status}`);
    const text = await res.text();
    const { jd, v } = parseVectors(text);
    if (Math.abs(jd - 2461041.5) > 1e-6) throw new Error(`${name}: epoch ${jd}`);
    vectors[name] = v;
    // Radius line for a manual cross-check of the physical table.
    notes[name] = (text.match(/(Vol\. [Mm]ean [Rr]adius[^\n]*|Mean [Rr]adius[^\n]*|Radius[^\n]*km[^\n]*)/) || [''])[0].trim();
    console.log(name, v.map((x) => x.toFixed(1)).join(' '), '|', notes[name]);
  }
  writeFileSync(new URL('./horizons-vectors.json', import.meta.url), JSON.stringify({ source: 'horizons', jd_tdb: 2461041.5, accessed: new Date().toISOString().slice(0, 10), vectors, radiusLines: notes }, null, 1));
}

if (process.argv[1] && import.meta.url.endsWith(process.argv[1].split('/').pop())) main().catch((e) => { console.error(e); process.exit(1); });
