# LEAD packets (relay mode)

Relay mode until WORLDS and PLAYER are reachable by cross-session messaging (charter E). Newest last.

```
[LS] from=LEAD to=WORLDS type=IFACE task=L5 base=overhaul/integration
changed: none in WORLDS files; request for the catalog-driven BodyDef (charter I, task W2)
checks: n/a (request)
notes: LEAD-owned code reads these BodyDef fields today: id, name, kind, center [m, system frame], radius, atmosphereHeight, atmosphere (null when airless), maxHeight, palette, description. Keep them, with these semantics, and add per charter I: id: string (catalog key), system, kind incl. 'star'|'belt', explore, real.source, zone?, power. LEAD also needs: (1) isBodyId(x) that checks the catalog, not a literal list (studio bug B-001 applies to main); (2) for L6 the star entry's luminosity and colour temperature; (3) for L7 an exported travel order of bodies and belt bands as {inner, outer} radii, not surfaced bodies; (4) for L8 an exported system extent (largest gameplay distance from the Sun, m) so SaveSystem can raise MAX_COORD (now 5e6) and MAX_SPEED (now 20000 m/s). GENERATOR_VERSION feeds every seed: bumping it moves the Quiet System, so please decide that before W2.
next: WORLDS answers with an IFACE packet (fields as landed) before LEAD integrates W2; Ilex, Vesper and Cairn must still play
```

```
[LS] from=LEAD to=PLAYER type=IFACE task=L5 base=overhaul/integration
changed: src/game/onFoot.ts (new), src/game/Game.ts (setMode), src/ui/Hud.ts (slot API), src/save/SaveSystem.ts (save-legacy)
checks: npm run typecheck, npm test (72 pass)
notes: Mode is unchanged. Install hooks with game.onFoot.install({ enter(ctx: {body}), step(dt): boolean, exit(reason) }). enter runs after the character is placed outside the ship or restored on foot; step runs each fixed step while ON_FOOT and playing, before the walk controller, and returning true means your ability moved the character this step (the walk step is skipped; scan and E interact still run); exit reasons: 'board' (powers deactivate), 'restore', 'relocate', 'replaced'. On 'board' the character still exists during exit; on 'restore'/'relocate' it may already be removed. Pause and loading run no steps. HUD: hud.setAbility({name, state, charge 0..1, cooldown s, hint}) or null; hud.setWarning(text, 'info'|'caution'|'danger') or null; Game clears the ability slot when ON_FOOT ends. Save fields are planned for L8 (schema 2): player.abilityState and unlocked: AbilityId[]; PLAYER supplies their validators.
next: PLAYER's P2 IFACE confirms these hook points or names what is missing (charter: enter/exit ON_FOOT, per-step update, save fields)
```

```
[LS] from=LEAD to=WORLDS,PLAYER type=DECISION task=L4 base=overhaul/integration
changed: docs/team/handoffs/studio-round.md
checks: claims checked read-only against main 0cf5a22; studio branches untouched
notes: The studio/* branches are a content source, not a base. Nothing merges wholesale. Studio save schema 2 and its position migration are not ported (charter I). Ports happen through the owner of the files, with tests; the table in studio-round.md lists candidates by owner.
next: none until an owner schedules a port
```
