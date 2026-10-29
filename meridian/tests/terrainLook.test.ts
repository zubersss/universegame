import { describe, expect, it } from 'vitest';
import { DataTexture } from 'three';
import { BODIES, BODY_IDS } from '../src/world/bodies';
import { DEFAULT_LOOK, makeTerrainUniforms, setTerrainPalette, terrainLook } from '../src/terrain/terrainMaterial';

describe('terrain look data', () => {
  it('every body resolves a complete, bounded look', () => {
    for (const id of BODY_IDS) {
      const look = terrainLook(BODIES[id]);
      for (const k of Object.keys(DEFAULT_LOOK) as (keyof typeof DEFAULT_LOOK)[]) expect(look[k]).toBeDefined();
      for (const k of ['specialSheen', 'strata', 'macro', 'sedimentAmount', 'peakRock'] as const) {
        expect(look[k]).toBeGreaterThanOrEqual(0);
        expect(look[k]).toBeLessThanOrEqual(1);
      }
      expect(look.strataSpacing).toBeGreaterThan(0);
      expect(look.rockSlope[0]).toBeLessThan(look.rockSlope[1]);
    }
  });

  it('a body without its own look falls back to the defaults, and its own fields win', () => {
    const plain = { ...BODIES.ilex, id: 'unknown' as never };
    expect(terrainLook(plain)).toEqual(DEFAULT_LOOK);
    const own = { ...plain, look: { strata: 0.9, sediment: 0x123456 } };
    const look = terrainLook(own);
    expect(look.strata).toBe(0.9);
    expect(look.sediment).toBe(0x123456);
    expect(look.macro).toBe(DEFAULT_LOOK.macro);
  });

  it('setting a body palette fills the shared uniforms with finite values', () => {
    const u = makeTerrainUniforms(new DataTexture(new Uint8Array(4), 1, 1));
    for (const id of BODY_IDS) {
      setTerrainPalette(u, BODIES[id]);
      const look = terrainLook(BODIES[id]);
      expect(u.uLook.value.toArray()).toEqual([look.strata, look.strataSpacing, look.macro, look.sedimentAmount]);
      expect(u.uLook2.value.y).toBe(BODIES[id].maxHeight);
      for (const v of [...u.uLook.value.toArray(), ...u.uLook2.value.toArray(), u.uSediment.value.r, u.uSediment.value.g, u.uSediment.value.b]) {
        expect(Number.isFinite(v)).toBe(true);
      }
    }
  });
});
