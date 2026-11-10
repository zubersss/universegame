using System.Collections;
using System.Collections.Generic;
using Meridian.UI;
using UnityEngine;

namespace Meridian.Core
{
    /// <summary>
    /// U-188 (Build 0.6.0, D1): the digging game in the player smoke. Earth after its ground shots (smoke_47-60): the first dig at the camp
    /// with the DIG DOWN card and the HUD (PACK, Scrip, Rank), the Surface Line crossed with its card, a room in each depth tier, PACK FULL,
    /// the jetpack out with the full pack, a ladder, the winch and a grapple reel in a 24 m shaft, the Sell panel and the Skill Tree with a
    /// node bought; Mars a T4 room (smoke_61); space the minimap and the system map (smoke_62 / 63). Holes are dug with Beam strokes (round
    /// scoops, D-168) with the Rig's reach lifted, and every card is put up by the run (the hints' own triggers held off meanwhile).
    /// ScreenCapture takes the HUD and the cards as the player draws them.
    /// </summary>
    public sealed partial class BuildSmoke
    {
        static void Put(PlanetSideRoot side, Vector2 feet)
        {
            var b = side.player.Body;
            b.position = feet; side.player.transform.position = feet; b.linearVelocity = Vector2.zero;
        }

        /// <summary>Waits for the ground round the surveyor; with `follow`, the camera follows it again at the default height.</summary>
        static IEnumerator Settle(PlanetSideRoot side, bool follow = true)
        {
            yield return null;
            float until = Time.realtimeSinceStartup + 15f;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
            if (!follow) yield break;
            Meridian.CameraRig.SideView.SetHalfHeight(side.sideCamera, Meridian.CameraRig.SideView.DefaultHalfHeight);
            var f = side.sideCamera.GetComponent<Meridian.Player.CameraFollow>();
            if (f != null) { f.enabled = true; f.SnapToTarget(); }
        }

        /// <summary>Beam strokes from y0 up to y1 across a 3 m column centred on x, with the Rig's reach lifted for the call. Returns the strokes that dug.</summary>
        static int Bore(Meridian.Rig.RigTools rig, float x, float y0, float y1)
        {
            int n = 0;
            using (new Unreached(rig)) // U-212 (1): the staging's reach, for this call alone
                for (float y = y0; y <= y1 + 1e-3f; y += 0.5f)
                    foreach (float dx in new[] { -1.1f, -0.55f, 0f, 0.55f, 1.1f })
                        if (rig.Dig(new Vector2(x + dx, y))) n++;
            return n;
        }

        /// <summary>The drawn floor under (x, from) on the outline's colliders, or `fallback`.</summary>
        static float FloorAt(float x, float from, float fallback)
        {
            foreach (var h in Physics2D.RaycastAll(new Vector2(x, from), Vector2.down, 6f))
                if (h.collider is EdgeCollider2D && h.collider.GetComponent<Meridian.Terrain.TerrainChunk>() != null) return h.point.y;
            return fallback;
        }

        /// <summary>A 3 × 3 m room `depth` m under the Surface Line at x, dug with Beam strokes, the surveyor on its floor, the camera following.</summary>
        static IEnumerator Room(PlanetSideRoot side, float x, float depth)
        {
            var t = side.terrain;
            var b = side.player.Body;
            float floorY = Meridian.Mining.DigRun.LineAt(t, x) - depth;
            b.simulated = false;
            Put(side, new Vector2(x, floorY + 1.05f));
            yield return Settle(side, false);
            int n = Bore(side.rig, x, floorY + 0.7f, floorY + 2.2f);
            yield return new WaitForFixedUpdate();
            Put(side, new Vector2(x, FloorAt(x, floorY + 2.3f, floorY) + 0.05f));
            b.simulated = true;
            yield return Settle(side);
            for (int k = 0; k < 40; k++) yield return new WaitForFixedUpdate();
            // U-205 (BLENDER's 0.6.2 read, G10: a small red mark on the PACK bar at 0 / 30 kg in smoke_61): it was a dug piece's icon caught
            // as it landed in the readout (U-195's pack flight; a piece under 1 kg leaves the reading at 0). The room is shot with nothing
            // in the air: the pieces still lying about go back to their pool and the flights under way land first.
            var drops = side.rig.drops;
            if (drops != null) for (int k = drops.Live.Count - 1; k >= 0; k--) drops.Collect(drops.Live[k]);
            var flight = FindAnyObjectByType<HudPackFlight>();
            float landBy = Time.realtimeSinceStartup + 2f;
            while (flight != null && flight.InFlight > 0 && Time.realtimeSinceStartup < landBy) yield return null;
            yield return Wait(0.8f);
            Debug.Log($"[MERIDIAN] smoke room at x {x:F1}, {depth:F0} m under the line: {n} strokes dug, tier {Meridian.Mining.DigRun.TierAt(t, b.position) + 1}, depth {Meridian.Mining.DigRun.Depth(t, b.position):F1} m; pack flights landed {(flight != null ? flight.Landed : -1)}, in the air {(flight != null ? flight.InFlight : -1)}");
        }

        static IEnumerator EarthDigRun(string folder, PlanetSideRoot side)
        {
            var t = side.terrain;
            var rig = side.rig;
            var hud = side.sideHud;
            var state = GameState.Instance;
            var player = side.player;
            if (t == null || rig == null || hud == null || state == null || player == null || !t.SmoothGround) yield break;
            var input = player.GetComponent<Meridian.Player.PlayerRigInput>();
            var hints = hud.Hints;
            bool ext = player.externalInput, haz = side.hazards != null && side.hazards.enabled, spawn = side.creatures != null && side.creatures.autoSpawn;
            var blocked = HintCards.Blocked;
            HintCards.Blocked = () => true; // the run puts each card up itself
            // U-212 (1): the Rig's owner stays ON through the run; Bore and the first scoop take it off for their own call
            player.externalInput = true; player.intent = default;
            if (side.hazards != null) side.hazards.enabled = false;
            if (side.creatures != null) { side.creatures.autoSpawn = false; side.creatures.DespawnAll(); }
            if (side.dayNight != null) side.dayNight.Override = 0.45f;
            // The ascent nodes granted for the staging, one tool after the other (nothing is unbought: only a New Expedition does that, U-178).
            void Grant(params string[] ids) { foreach (var id in ids) if (!state.skillNodes.Contains(id)) state.skillNodes.Add(id); Meridian.Progress.SkillStats.Apply(state); }
            try
            {
                state.hintsSeen.Clear();
                state.inventory.Clear();
                int sx = side.spawnX;

                // smoke_47: topside at the camp, the HUD (PACK, Scrip, Rank), the first scoop and the DIG DOWN card.
                float tx = sx + 14.5f;
                Put(side, new Vector2(tx, t.SurfaceAt(tx) + 0.05f));
                yield return Settle(side);
                yield return Staged(side);
                using (new Unreached(rig)) rig.Dig(new Vector2(tx + 2f, t.SurfaceAt(tx + 2f) - 0.25f));
                if (hints != null) hints.Show(HintCards.DigDown);
                yield return Wait(1.2f);
                yield return Shot(folder, "smoke_47_d1_first_dig_dig_down.png");
                if (hints != null) hints.Dismiss();

                // smoke_65 / 66 (U-194, D-182; U-212 (2)): a new surveyor's shovel on fresh ground inside its reach beside the first
                // scoop: the CONTACT drawing of the first swing, then the follow-through of the swing that opens the ground; the HUD's
                // tool slot reads SHOVEL.
                if (input != null)
                {
                    yield return ShovelShots(side, new Vector2(tx + 1.3f, t.SurfaceAt(tx + 1.3f) - 0.5f), name => Shot(folder, name),
                        "smoke_65_d1_shovel_contact.png", "smoke_66_d1_shovel_follow_through.png");
                    Debug.Log($"[MERIDIAN] smoke shovel slot: '{(hud.ToolSlot != null ? hud.ToolSlot.Name.text : "-")}'");
                    FreeAim();
                }

                // smoke_48: 2 m under the Surface Line in a pit beside the camp: the line in the cutaway, its card.
                float px = sx + 27.5f, ps = t.SurfaceAt(px);
                Bore(rig, px, ps - 3.6f, ps + 0.5f);
                yield return new WaitForFixedUpdate();
                Put(side, new Vector2(px, FloorAt(px, ps, ps - 4f) + 0.05f));
                yield return Settle(side);
                for (int k = 0; k < 30; k++) yield return new WaitForFixedUpdate();
                if (hints != null) hints.Show(HintCards.SurfaceLine);
                yield return Wait(1.2f);
                yield return Shot(folder, "smoke_48_d1_surface_line.png");
                if (hints != null) hints.Dismiss();
                Debug.Log($"[MERIDIAN] smoke surface line: feet {player.Body.position.y:F2}, the line {Meridian.Mining.DigRun.LineAt(t, px):F2}");

                // smoke_49-53: a room in each depth tier, stacked down one column east of the camp (T3 the stone room).
                string[] rooms = { "smoke_49_d1_t1_room.png", "smoke_50_d1_t2_room.png", "smoke_51_d1_t3_room.png", "smoke_52_d1_t4_room.png", "smoke_53_d1_t5_room.png" };
                var tiers = Meridian.Mining.D1Tables.Current.tiers;
                float rx = sx + 62.5f;
                for (int i = 0; i < tiers.Length && i < rooms.Length; i++)
                {
                    float from = tiers[i].fromM, to = i + 1 < tiers.Length ? tiers[i + 1].fromM : from + 60f;
                    yield return Room(side, rx, Mathf.Max(5f, from + Mathf.Min(to - from, 60f) * 0.5f));
                    yield return Shot(folder, rooms[i]);
                }

                // The ways back up (U-176) in a 24 m shaft beside the camp: PACK FULL at its floor, the jetpack out with the full pack,
                // a ladder, the winch, a grapple reel.
                float ax = sx + 19.5f, top = t.SurfaceAt(ax), bottom = Mathf.Floor(top) - 24f;
                int bored = Bore(rig, ax, bottom + 0.7f, top + 0.5f);
                yield return new WaitForFixedUpdate();
                float shaftFloor = FloorAt(ax, bottom + 2.3f, bottom);
                Debug.Log($"[MERIDIAN] smoke shaft at x {ax:F1}: {bored} strokes, floor {shaftFloor:F2}, top {top:F2}");
                IEnumerator AtFloor()
                {
                    player.LetGo(); player.intent = default;
                    if (input != null) input.holdUse = false;
                    Put(side, new Vector2(ax, shaftFloor + 0.05f));
                    yield return Settle(side);
                    for (int k = 0; k < 30; k++) yield return new WaitForFixedUpdate();
                    var f = side.sideCamera.GetComponent<Meridian.Player.CameraFollow>();
                    if (f != null) f.SnapToTarget();
                }

                // smoke_54: the pack filled to its limit at the floor, the next piece refused: the HUD's cue and the PACK FULL card.
                yield return AtFloor();
                var material = Meridian.Items.ItemRegistry.Get(Meridian.Mining.D1Tables.Current.materials[0].item);
                if (material != null)
                {
                    state.inventory.Add(material.id, state.inventory.FitsByWeight(material.id));
                    state.inventory.Add(material.id, 1); // refused
                }
                if (hints != null) hints.Show(HintCards.PackFull);
                yield return Wait(1.2f);
                yield return Shot(folder, "smoke_54_d1_pack_full.png");
                if (hints != null) hints.Dismiss();

                // smoke_55: the jetpack out of the shaft with that full pack (the load factor).
                yield return AtFloor();
                player.intent = new Meridian.Player.PlayerIntent { jumpPressed = true, jumpHeld = true };
                for (int i = 0; i < 45; i++) { yield return new WaitForFixedUpdate(); player.intent.jumpPressed = false; player.intent.jumpHeld = true; }
                yield return Shot(folder, "smoke_55_d1_jetpack_full_pack.png");
                Debug.Log($"[MERIDIAN] smoke jetpack: {player.Body.position.y - shaftFloor:F1} m up in 45 steps with the full pack");
                player.intent = default;

                // smoke_56: a ladder 20 m up the shaft, climbed to 9 m.
                Grant("asc_ladder_1", "asc_ladder_2");
                state.dirt.count = state.dirt.capacity;
                if (side.ladders != null)
                {
                    side.ladders.player = null;
                    for (int k = 0; k < 20; k += 3) side.ladders.Place(new Vector2(ax, shaftFloor + k + 0.5f));
                    side.ladders.player = player.transform;
                    yield return AtFloor();
                    player.intent = new Meridian.Player.PlayerIntent { climb = 1f };
                    for (int k = 0; k < 600 && player.Body.position.y < shaftFloor + 9f; k++) yield return new WaitForFixedUpdate();
                    yield return Shot(folder, "smoke_56_d1_ladder.png");
                    player.intent = default;
                    foreach (var c in new List<Vector2Int>(side.ladders.Cells)) side.ladders.Remove(c);
                }

                // smoke_57: the winch's post at the mouth, ridden up from the floor.
                Grant("asc_winch");
                if (side.winch != null)
                {
                    side.winch.player = null;
                    side.winch.Place(new Vector2(ax, top - 0.5f));
                    side.winch.player = player.transform;
                    yield return AtFloor();
                    player.intent = new Meridian.Player.PlayerIntent { climb = 1f };
                    for (int k = 0; k < 600 && player.Body.position.y < shaftFloor + 12f; k++) yield return new WaitForFixedUpdate();
                    yield return Shot(folder, "smoke_57_d1_winch.png");
                    player.intent = default;
                    side.winch.Remove();
                }

                // smoke_58: the Grapple thrown at the wall 10 m up, reeling in.
                Grant("asc_grapple_1");
                if (input != null && input.Grapple != null)
                {
                    yield return AtFloor();
                    var module = input.module;
                    input.module = Meridian.Rig.RigModule.Grapple;
                    var hands = input.Grapple.Hands;
                    // the left wall 10 m up (the bored shaft's walls are round scoops, wider than a carved one), aimed just into it
                    var aim = new Vector2(ax - 2.1f, hands.y + 14.7f);
                    foreach (var h in Physics2D.RaycastAll(new Vector2(ax, hands.y + 10f), Vector2.left, 6f))
                        if (h.collider is EdgeCollider2D && h.collider.GetComponent<Meridian.Terrain.TerrainChunk>() != null) { aim = h.point + new Vector2(-0.3f, 0f); break; }
                    PinAim(input, aim);
                    input.holdUse = true;
                    for (int k = 0; k < 150 && !input.Grapple.Attached; k++) yield return new WaitForFixedUpdate();
                    for (int k = 0; k < 400 && input.Grapple.Attached && player.Body.position.y < shaftFloor + 4f; k++) yield return new WaitForFixedUpdate();
                    yield return Shot(folder, "smoke_58_d1_grapple_reel.png");
                    Debug.Log($"[MERIDIAN] smoke grapple: attached {input.Grapple.Attached}, {player.Body.position.y - shaftFloor:F1} m up");
                    input.holdUse = false;
                    player.LetGo();
                    input.module = module;
                    FreeAim();
                }

                // smoke_59 / 60: topside at the camp, the Sell panel over a pack of Earth's materials; then the Skill Tree with Beam Power I bought.
                player.LetGo();
                Put(side, new Vector2(sx + 0.5f, t.SurfaceAt(sx + 0.5f) + 0.05f));
                yield return Settle(side);
                state.inventory.Clear();
                foreach (var (item, n) in new[] { ("clay", 6), ("carbon", 4), ("iron", 5), ("copper", 3), ("silica", 2) })
                {
                    var def = Meridian.Items.ItemRegistry.Get(item);
                    if (def != null) state.inventory.Add(def.id, n);
                }
                for (int k = 0; k < 30; k++) yield return new WaitForFixedUpdate();
                if (hud.Sell != null)
                {
                    hud.Sell.SetOpen(true);
                    yield return Wait(1f);
                    yield return Shot(folder, "smoke_59_d1_sell.png");
                    int paid = hud.Sell.SellAll();
                    hud.Sell.SetOpen(false);
                    Debug.Log($"[MERIDIAN] smoke sell: {paid} Scrip, purse {state.scrip}, earned {state.scripEarned}");
                }
                if (hud.Skills != null)
                {
                    const string node = "dig_power_1";
                    var bought = Meridian.Progress.SkillTree.Current.Buy(state, node, true);
                    hud.Skills.SetOpen(true);
                    hud.Skills.Select(node);
                    yield return Wait(2f); // the chart, frames, icons and papers
                    yield return Shot(folder, "smoke_60_d1_skill_tree.png");
                    hud.Skills.SetOpen(false);
                    Debug.Log($"[MERIDIAN] smoke skill tree: {node} {bought}, purse {state.scrip}");
                    // smoke_67 (U-194): The Beam bought: the Beam Mk1 in hand and the HUD's tool slot reads BEAM MK1.
                    if (input != null)
                    {
                        input.module = Meridian.Rig.RigModule.Beam;
                        PinAim(input, new Vector2(sx + 3.5f, t.SurfaceAt(sx + 3.5f) - 0.4f));
                        yield return Wait(1f);
                        yield return Shot(folder, "smoke_67_d1_tool_slot_beam.png");
                        Debug.Log($"[MERIDIAN] smoke tool slot: '{(hud.ToolSlot != null ? hud.ToolSlot.Name.text : "-")}' {(hud.ToolSlot != null ? hud.ToolSlot.IconKey : "-")}, tool {rig.Tool}");
                        // smoke_68 (U-212 (2)): the Beam mid-dig on fresh ground west of the first scoop: the ray on its contact, the spark,
                        // the crack growing under the brackets.
                        Put(side, new Vector2(tx, t.SurfaceAt(tx) + 0.05f));
                        yield return Settle(side);
                        for (int k = 0; k < 30; k++) yield return new WaitForFixedUpdate();
                        yield return BeamShot(side, new Vector2(tx - 3f, t.SurfaceAt(tx - 3f) - 0.6f), name => Shot(folder, name), "smoke_68_d1_beam_mid_dig.png");
                        FreeAim();
                    }
                }
                yield return Wait(0.3f);
            }
            finally
            {
                player.externalInput = ext; player.intent = default;
                if (input != null) input.holdUse = false;
                FreeAim();
                HintCards.Blocked = blocked;
                if (side.hazards != null) side.hazards.enabled = haz;
                if (side.creatures != null) side.creatures.autoSpawn = spawn;
            }
        }

        /// <summary>smoke_61: a room in Mars's T4 (140 m under its Surface Line) east of the landing.</summary>
        static IEnumerator MarsRoom(string folder, PlanetSideRoot side)
        {
            var rig = side.rig;
            if (rig == null || side.terrain == null || side.player == null) yield break;
            bool haz = side.hazards != null && side.hazards.enabled; // U-212 (1): the owner stays on (Room's Bore lifts the reach itself)
            if (side.hazards != null) side.hazards.enabled = false;
            try
            {
                yield return Room(side, side.spawnX + 40.5f, 140f);
                yield return Shot(folder, "smoke_61_mars_t4_room.png");
            }
            finally
            {
                if (side.hazards != null) side.hazards.enabled = haz;
            }
        }

        /// <summary>The follow-through's drawing a shot waits for (the swing's five: 0 the wind-up, 1 the contact, 2-4 the follow-through).</summary>
        public const int FollowDrawing = 3;

        /// <summary>
        /// U-212 (2): the shovel's stroke as play shows it, on its own moments. The Rig's owner is ON and the cursor is pinned on `aim`
        /// (fresh ground inside the reach): `contactName` is taken in the first swing's CONTACT drawing (the blade on the ground, the
        /// crack, the crumbs leaving the face, the brackets on the contact), `followName` in the follow-through of the swing that opens
        /// the ground (the clods in the air). `shot` takes a picture by name: the player's screenshot here, a capture's own grab in
        /// the Editor (SceneCapture.CaptureU212), so both show one staging. The caller frees the aim.
        /// </summary>
        public static IEnumerator ShovelShots(PlanetSideRoot side, Vector2 aim, System.Func<string, IEnumerator> shot, string contactName, string followName)
        {
            var input = side != null && side.player != null ? side.player.GetComponent<Meridian.Player.PlayerRigInput>() : null;
            var rig = side != null ? side.rig : null;
            if (input == null || rig == null) yield break;
            var stroke = input.Stroke;
            input.module = Meridian.Rig.RigModule.Beam; // the dig slot: the shovel until The Beam is bought
            input.holdUse = false;
            PinAim(input, aim);
            float until = Time.realtimeSinceStartup + 3f;
            while (stroke.Active && Time.realtimeSinceStartup < until) yield return null;
            yield return Wait(0.5f); // at rest: the tool carried, the reticle on the next contact
            bool found = rig.DigTarget(aim, out var lands, out bool pulled);
            float from = (lands - rig.DigOrigin).magnitude;
            int opens = stroke.Opens, contacts = stroke.Contacts;
            input.holdUse = true;
            until = Time.realtimeSinceStartup + 10f;
            while (!(stroke.Phase == Meridian.Player.DigPhase.Swing && stroke.ContactDone && stroke.Drawing == Meridian.Player.DigStroke.ContactDrawing) && Time.realtimeSinceStartup < until) yield return null;
            // up to two frames on while the contact drawing still stands: the crumbs are off the face
            for (int k = 0; k < 2; k++)
            {
                if (stroke.Phase != Meridian.Player.DigPhase.Swing || stroke.SwingTime + Time.deltaTime >= 2f * Meridian.Player.DigStroke.ContactSeconds) break;
                yield return null;
            }
            var first = stroke.LastContact;
            int drawing = stroke.Drawing, crack = input.ToolView != null ? input.ToolView.CrackStage : -1;
            yield return shot(contactName);
            // held on to the swing that opens the ground; that swing is committed, so the button comes up and it runs out
            until = Time.realtimeSinceStartup + 10f;
            while (stroke.Opens == opens && Time.realtimeSinceStartup < until) yield return null;
            input.holdUse = false;
            while (stroke.Phase == Meridian.Player.DigPhase.Swing && stroke.Drawing < FollowDrawing && Time.realtimeSinceStartup < until) yield return null;
            int followOn = stroke.Drawing;
            yield return shot(followName);
            Debug.Log($"[MERIDIAN] smoke shovel: tool {rig.Tool}; the aim {(found ? "lands" : "finds NOTHING")} {from:0.00} m from the shoulder (reach {rig.DigReach:0.0} m{(pulled ? ", pulled in" : "")}); {contactName} on drawing {drawing}, first contact {first}, crack stage {crack}; {followName} on drawing {followOn}; contacts {stroke.Contacts - contacts}, opened {stroke.Opens - opens}; the Rig's owner {(rig.owner != null ? "on" : "OFF")}");
            until = Time.realtimeSinceStartup + 3f;
            while (stroke.Active && Time.realtimeSinceStartup < until) yield return null;
        }

        /// <summary>
        /// U-212 (2): the Beam mid-dig, the owner ON and the cursor pinned on `aim` (fresh ground inside the reach): the ray on its
        /// contact, the spark there, the crack at its second or third stage (the work between 0.35 and 0.9 of the cell's). A cell that
        /// opens before a frame lands in that window is no loss: the ray works on into the next and the shot is taken there.
        /// </summary>
        public static IEnumerator BeamShot(PlanetSideRoot side, Vector2 aim, System.Func<string, IEnumerator> shot, string name)
        {
            var input = side != null && side.player != null ? side.player.GetComponent<Meridian.Player.PlayerRigInput>() : null;
            var rig = side != null ? side.rig : null;
            if (input == null || rig == null) yield break;
            var stroke = input.Stroke;
            var view = input.ToolView;
            input.module = Meridian.Rig.RigModule.Beam;
            input.holdUse = false;
            PinAim(input, aim);
            float until = Time.realtimeSinceStartup + 5f;
            while ((stroke.Active || view == null || view.Tool == null || view.Tool.sprite == null || !view.RayReady) && Time.realtimeSinceStartup < until) { view = input.ToolView; yield return null; }
            yield return Wait(0.5f);
            bool found = rig.DigTarget(aim, out var lands, out bool pulled);
            float from = (lands - rig.DigOrigin).magnitude;
            int opens = stroke.Opens;
            input.holdUse = true;
            until = Time.realtimeSinceStartup + 10f;
            while (!(stroke.Phase == Meridian.Player.DigPhase.Beam && stroke.Diggable && input.StrokeProgress >= 0.35f && input.StrokeProgress <= 0.9f) && Time.realtimeSinceStartup < until) yield return null;
            float work = input.StrokeProgress;
            var phase = stroke.Phase;
            yield return shot(name);
            input.holdUse = false;
            Debug.Log($"[MERIDIAN] smoke beam: tool {rig.Tool}; the aim {(found ? "lands" : "finds NOTHING")} {from:0.00} m from the shoulder (reach {rig.DigReach:0.0} m{(pulled ? ", pulled in" : "")}); {name} in phase {phase} with the cell's work at {work:0.00} (crack stage {Meridian.Player.DigStroke.StageOf(work)}); cells opened before it {stroke.Opens - opens}; the Rig's owner {(rig.owner != null ? "on" : "OFF")}");
            until = Time.realtimeSinceStartup + 3f;
            while (stroke.Active && Time.realtimeSinceStartup < until) yield return null;
        }

        /// <summary>smoke_62 / 63 (U-184): the ship off Earth's well, the minimap over the flight HUD, then the system map (M) open.</summary>
        static IEnumerator SpaceMaps(string folder, SceneDirector scenes, Meridian.Space.SpaceShip craft)
        {
            var spaceHud = scenes.Space != null ? scenes.Space.GetComponentInChildren<Meridian.Space.SpaceHud>() : null;
            var map = spaceHud != null ? spaceHud.Map : null;
            if (craft == null || map == null) yield break;
            float until = Time.realtimeSinceStartup + 10f;
            while (!map.Built && Time.realtimeSinceStartup < until) yield return null;
            var earth = craft.world.Find("earth");
            if (earth == null) yield break;
            var at = earth.Value.position + new Vector2(earth.Value.WellRadius + 140f, -60f);
            IEnumerator Hold(float seconds)
            {
                for (float s = 0f; s < seconds; s += Time.unscaledDeltaTime) { craft.Position = at; craft.Velocity = Vector2.zero; craft.Heading = 30f; yield return null; }
            }
            yield return Hold(2.5f);
            yield return Shot(folder, "smoke_62_space_minimap.png");
            map.SetSystemOpen(true);
            yield return Hold(1.5f);
            yield return Shot(folder, "smoke_63_system_map.png");
            map.SetSystemOpen(false);
        }
    }
}
