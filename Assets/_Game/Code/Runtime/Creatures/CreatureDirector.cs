using Meridian.Art;
using System.Collections.Generic;
using System.Diagnostics;
using Meridian.Planet.Lighting;
using Meridian.Planets;
using Meridian.Player;
using Meridian.Rendering;
using Meridian.Terrain;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Creatures
{
    /// <summary>
    /// U-027: spawns the planet's creatures off-screen by biome and time of day, despawns them far away,
    /// and runs every creature's AI in one loop: think 4×/s (flee or chase the player, wander), steer
    /// every frame (run, hop 1–2 tile steps, turn at walls), bump when a hunter reaches the player (U-093, D-087: no bites).
    /// Creatures whose chunk isn't loaded with collision are held in place, so none falls through
    /// streamed ground. At most 20 alive. No allocation per frame.
    /// U-055: fliers (a hover band over the ground, or Venus's cloud deck) steer in 2D without gravity;
    /// spawn rules see Mercury's zones and Venus's features; creatures animate from their sheets
    /// (idle/walk/attack/hurt); the Cinderhulk wears its night sheet past the terminator and tracks nightfall.
    /// U-108: each tick reports ground contact to Creature.Animate, so a sheet with a `fly` clip (B-127 gull) plays it while airborne.
    /// </summary>
    public sealed class CreatureDirector : MonoBehaviour
    {
        public const int MaxCreatures = 20;
        public const float SpawnInterval = 1.5f;
        public const float SpawnMin = 24f, SpawnMax = 40f, DespawnDistance = 64f;
        internal const float ThinkInterval = 0.25f;
        const float Accel = 30f, FlyAccel = 12f;

        public TerrainStreamer terrain;
        public PlayerController player;
        public DayNightLighting dayNight;
        /// <summary>Mercury: the flare state (Flarewings) and Mercury's clock offset (U-055).</summary>
        public Meridian.Hazards.HazardSystem hazards;
        /// <summary>Natural spawning. Off in batch runs (other tests stay deterministic) unless AutoSpawnOverride says otherwise.</summary>
        public bool autoSpawn = true;
        public static bool? AutoSpawnOverride;

        public PlanetConfig Planet { get; private set; }
        public int AliveCount { get; private set; }
        public double LastAiMs { get; private set; }
        /// <summary>U-121: what the last frame over SpikeMs did (spawn tick ms, creature ticks ms and count, holds, despawns, the frame's dt); empty until a spike. Tests print it.</summary>
        public string LastSpikeNote { get; private set; } = "";
        public const double SpikeMs = 1.0;
        int tickHolds, tickDespawns, tickCount;
        public IReadOnlyList<Creature> All => pool;

        readonly List<Creature> pool = new List<Creature>(MaxCreatures);
        /// <summary>U-118 (D-126): the den props placed for den species (the tube mounds), cleared with the planet.</summary>
        readonly List<Transform> dens = new List<Transform>(8);
        public IReadOnlyList<Transform> Dens => dens;
        public const int DenOrder = 6, MaxDens = 8;
        public const float DenReuseRange = 6f;
        static readonly int SpeciesCount = SpeciesSpec.Count;
        readonly Sprite[] art = new Sprite[SpeciesCount];
        readonly Sprite[][] frames = new Sprite[SpeciesCount][];
        readonly Sprite[][] nightFrames = new Sprite[SpeciesCount][];
        readonly AsyncOperationHandle<IList<Sprite>>[] artHandles = new AsyncOperationHandle<IList<Sprite>>[SpeciesCount];
        readonly AsyncOperationHandle<IList<Sprite>>[] nightHandles = new AsyncOperationHandle<IList<Sprite>>[SpeciesCount];
        readonly Stopwatch watch = new Stopwatch();
        static Sprite placeholder;
        float nextSpawn;
        int serial, seed;
        PlayerVitals vitals;
        Collider2D[] playerColliders;
        Meridian.Core.TimeSystem clock;

        void Awake()
        {
            autoSpawn = AutoSpawnOverride ?? !Application.isBatchMode;
            for (int i = 0; i < MaxCreatures; i++) pool.Add(Creature.Create(transform, i));
            if (placeholder == null)
            {
                placeholder = Sprite.Create(Texture2D.whiteTexture, new Rect(0, 0, 4, 4), new Vector2(0.5f, 0.5f), 4f);
                placeholder.name = "CreaturePlaceholder";
            }
        }

        public void ConfigureFor(PlanetConfig planet, int worldSeed)
        {
            Planet = planet;
            if (terrain != null) SeaAhead(0, 0); // U-188: JIT the shore check now, not inside the AI budget's worst frame (D-047)
            seed = worldSeed;
            DespawnAll();
            ClearDens();
            nextSpawn = 0f;
            for (int s = 0; s < SpeciesCount; s++)
            {
                var spec = SpeciesSpec.Get((Species)s);
                // U-060: the PlanetSide scene is reused across planets; drop other planets' creature sheets
                // (they stayed loaded until destroy and the dev-build texture memory grew with every planet).
                if (spec.planet != planet.id) { ReleaseArt(s); continue; }
                if (spec.rig) continue; // U-119: a rig-set creature loads its own json, parts and controller (Creature.EnsureRig)
                if (art[s] == null && !artHandles[s].IsValid()) LoadArt(s, spec.artKey, false);
                if (spec.nightArtKey != null && nightFrames[s] == null && !nightHandles[s].IsValid()) LoadArt(s, spec.nightArtKey, true);
            }
        }

        /// <summary>Real art when BLENDER's creature sheets exist; a tinted box until then. Frames by their _N index.</summary>
        void LoadArt(int s, string key, bool night)
        {
            var loc = Addressables.LoadResourceLocationsAsync(key);
            loc.Completed += l =>
            {
                bool exists = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                global::Meridian.Art.ArtLoad.Release(l);
                if (!exists || this == null) return;
                // Left the species' planet while the lookup ran: don't load it (nothing would release it).
                if (Planet == null || SpeciesSpec.Get((Species)s).planet != Planet.id) return;
                if ((night ? nightHandles[s] : artHandles[s]).IsValid()) return;
                var h = ArtLoad.Asset<IList<Sprite>>(key);
                if (night) nightHandles[s] = h; else artHandles[s] = h;
                h.Completed += op =>
                {
                    if (this == null) return; // the planet side unloaded before its sheet arrived
                    if (op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                    var list = new Sprite[op.Result.Count];
                    foreach (var sp in op.Result)
                    {
                        int u = sp.name.LastIndexOf('_');
                        if (u >= 0 && int.TryParse(sp.name.Substring(u + 1), out int n) && n >= 0 && n < list.Length) list[n] = sp;
                    }
                    for (int i = 0; i < list.Length; i++) if (list[i] == null) list[i] = op.Result[0];
                    if (night) { nightFrames[s] = list; return; }
                    frames[s] = list;
                    art[s] = list[0];
                    // U-108: bodies that spawned before the sheet (the stage's load-time gull) take it now instead of keeping the placeholder box.
                    var arrived = SpeciesSpec.Get((Species)s);
                    foreach (var live in pool)
                        if (live != null && live.Alive && live.Spec != null && live.Spec.id == (Species)s && live.IsPlaceholder) // U-184: a body destroyed before its sheet arrived
                            live.ApplyArt(list[0], list, nightFrames[s], ArtMaterials.ClipsFor(arrived.artKey));
                };
            };
        }

        void ReleaseArt(int s)
        {
            if (artHandles[s].IsValid()) global::Meridian.Art.ArtLoad.Release(artHandles[s]);
            if (nightHandles[s].IsValid()) global::Meridian.Art.ArtLoad.Release(nightHandles[s]);
            artHandles[s] = default;
            nightHandles[s] = default;
            art[s] = null;
            frames[s] = null;
            nightFrames[s] = null;
        }

        /// <summary>Whether a species' art has arrived (tests wait on it).</summary>
        public bool ArtReady(Species s) => art[(int)s] != null && (SpeciesSpec.Get(s).nightArtKey == null || nightFrames[(int)s] != null);

        public float Daylight => dayNight != null ? DayNightMath.Daylight(dayNight.LocalTime) : 1f;

        /// <summary>Mercury's clock (real seconds), as the hazards and lighting read it.</summary>
        public double MercuryNow
        {
            get
            {
                if (clock == null) clock = FindAnyObjectByType<Meridian.Core.TimeSystem>();
                return MercuryTerminator.Now(clock != null ? clock.GameSeconds : 0) + (hazards != null ? hazards.mercuryClockOffset : 0);
            }
        }

        /// <summary>The Mercury zone at x (cold-trap floors are always night). Day elsewhere.</summary>
        public MercuryZone ZoneAt(float x)
        {
            if (Planet == null || Planet.id != PlanetId.Mercury) return MercuryZone.Day;
            int wx = terrain != null ? terrain.WrapX(Mathf.FloorToInt(x)) : Mathf.FloorToInt(x);
            if (MercuryLandforms.PermanentShadow(wx, Planet.worldWidth)) return MercuryZone.Night;
            return MercuryTerminator.ZoneAt(x, MercuryNow, Planet.worldWidth);
        }

        bool FlareActive => hazards != null && hazards.flares != null && hazards.flares.Current == Meridian.Hazards.SolarFlares.Phase.Active;

        // ---------- spawning ----------

        /// <summary>One spawn attempt per species of this planet (called every 1.5 s when autoSpawn).</summary>
        public void SpawnTick()
        {
            if (Planet == null || terrain == null || terrain.Generator == null || player == null) return;
            float daylight = Daylight;
            var p = player.transform.position;
            for (int s = 0; s < SpeciesCount; s++)
            {
                var spec = SpeciesSpec.Get((Species)s);
                if (spec.planet != Planet.id || !spec.ActiveAt(daylight)) continue;
                if (CountOf(spec.id) + spec.packMin > spec.maxAlive) continue;
                serial++;
                if (Hash01(serial, 1) > (spec.apex ? 0.08f : 0.4f)) continue; // not every tick; apexes rarely
                float side = Hash01(serial, 2) < 0.5f ? -1f : 1f;
                float x = p.x + side * Mathf.Lerp(SpawnMin, SpawnMax, Hash01(serial, 3));
                int pack = spec.packMin + (int)(Hash01(serial, 4) * (spec.packMax - spec.packMin + 1));
                SpawnPack(spec, x, p.y, Mathf.Min(pack, spec.maxAlive - CountOf(spec.id)));
            }
        }

        /// <summary>What the spawn rule sees at column tx.</summary>
        public SpawnSite SiteAt(int tx, float playerY)
        {
            int surface = terrain.TopSolidY(tx); // real ground: stamps (spawn camp, POIs) included
            var site = new SpawnSite
            {
                x = terrain.WrapX(tx), surfaceY = surface, surfaceTile = terrain.GetTile(tx, surface),
                aboveTile = terrain.GetTile(tx, surface + 1), waterDepth = WaterDepthAbove(tx, surface), // U-114: the pool over the floor, if any
                datumY = Planet.datumY, worldWidth = Planet.worldWidth, planet = Planet.id, playerY = playerY,
            };
            if (Planet.id == PlanetId.Mercury)
            {
                site.zone = ZoneAt(tx + 0.5f);
                site.localTime = MercuryTerminator.LocalTime(tx + 0.5f, MercuryNow, Planet.worldWidth);
            }
            return site;
        }

        void SpawnPack(SpeciesSpec spec, float x, float playerY, int count)
        {
            for (int i = 0; i < count; i++)
                if (SpawnAt(spec.id, Mathf.FloorToInt(x + i * 1.6f), playerY) == null) return;
        }

        /// <summary>
        /// One creature at column tx by the natural rules (tests use this): its spawn rule must allow the site,
        /// then walkers stand on the ground, Air fliers hover in their band over it, Deck fliers take a lane in
        /// the deck band near the surveyor's height. Null when the rule refuses or the pool is full.
        /// </summary>
        public Creature SpawnAt(Species species, int tx, float playerY)
        {
            var spec = SpeciesSpec.Get(species);
            var site = SiteAt(tx, playerY);
            if (!spec.Allows(site)) return null;
            if (spec.habitat == Habitat.Ground && site.waterDepth > 0) return null; // U-188: no land creature on a seabed
            Vector2 at;
            if (spec.habitat == Habitat.Deck)
            {
                float y = Mathf.Clamp(playerY + (Hash01(serial, 5) - 0.5f) * 12f,
                    VenusLandforms.DeckY - VenusLandforms.DeckHalfBand, VenusLandforms.DeckY + VenusLandforms.DeckHalfBand);
                if (TileId.IsSolid(terrain.GetTile(tx, Mathf.FloorToInt(y)))) return null;
                at = new Vector2(tx + 0.5f, y);
            }
            else
            {
                if (!terrain.IsCollisionReady(tx, site.surfaceY)) return null;
                at = spec.habitat == Habitat.Air
                    ? new Vector2(tx + 0.5f, site.surfaceY + 1f + site.waterDepth + Mathf.Lerp(spec.hoverMin, spec.hoverMax, Hash01(serial, 6))) // U-188: over the sea, above its water line
                    : spec.habitat == Habitat.Water
                    ? new Vector2(tx + 0.5f, site.surfaceY + 1f + spec.floorClearance + spec.size.y * 0.5f) // U-114: its clearance over the pool floor
                    : new Vector2(tx + 0.5f, site.surfaceY + 1f + spec.size.y * 0.5f + 0.05f);
            }
            return Spawn(species, at);
        }

        /// <summary>Places one creature (tests use this directly). Null when 20 are already alive.</summary>
        public Creature Spawn(Species species, Vector2 position)
        {
            foreach (var c in pool)
            {
                if (c.Alive) continue;
                var spec = SpeciesSpec.Get(species);
                int s = (int)species;
                c.director = this;
                c.Setup(spec, position, art[s] != null ? art[s] : placeholder, frames[s], nightFrames[s],
                    art[s] != null ? ArtMaterials.ClipsFor(spec.artKey) : null, ++serial);
                c.Zone = ZoneAt(position.x);
                if (spec.HasDen) c.DenX = EnsureDen(spec, position); // U-118 (D-126): spawned at its mound
                IgnoreBodies(c);
                AliveCount++;
                return c;
            }
            return null;
        }

        void IgnoreBodies(Creature c)
        {
            // Creatures pass through each other and through the player (contact is a bump, not a physics shove).
            foreach (var o in pool) if (o != c) Physics2D.IgnoreCollision(c.Box, o.Box, true);
            if (player != null)
            {
                playerColliders ??= player.GetComponents<Collider2D>(); // once: no per-spawn allocation
                foreach (var col in playerColliders) Physics2D.IgnoreCollision(c.Box, col, true);
            }
        }

        public void Despawn(Creature c)
        {
            if (!c.Alive) return;
            c.gameObject.SetActive(false);
            AliveCount--;
        }

        public void DespawnAll() { foreach (var c in pool) Despawn(c); }

        /// <summary>
        /// U-118 (D-126): the den prop for a den species spawned at `position` (the body centre): an existing den within DenReuseRange is reused, else
        /// a new one is placed on the ground under the body — a SpriteRenderer in front of the creatures (DenOrder) that ModelSwap fills with the
        /// prop's sheet (or model). Returns the den's x. Dens stay for the planet's visit and go with it.
        /// </summary>
        float EnsureDen(SpeciesSpec spec, Vector2 position)
        {
            foreach (var d in dens) if (d != null && d.name == spec.den && Mathf.Abs(d.position.x - position.x) <= DenReuseRange) return d.position.x;
            if (dens.Count >= MaxDens) { var oldest = dens[0]; dens.RemoveAt(0); if (oldest != null) Destroy(oldest.gameObject); }
            var go = new GameObject(spec.den);
            go.transform.SetParent(transform, false);
            go.transform.position = new Vector3(position.x, position.y - spec.size.y * 0.5f - 0.05f, 0f); // the ground line under the body
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sortingOrder = DenOrder; // in front of the creature (order 5): it peeks from behind the mound
            Meridian.Art.ModelSwap.Attach(sr, spec.den, go.transform, Vector3.zero);
            dens.Add(go.transform);
            return position.x;
        }

        void ClearDens()
        {
            foreach (var d in dens) if (d != null) Destroy(d.gameObject);
            dens.Clear();
        }

        public int CountOf(Species s)
        {
            int n = 0;
            foreach (var c in pool) if (c.Alive && c.Spec.id == s) n++;
            return n;
        }

        // ---------- AI ----------

        void Update()
        {
            watch.Restart();
            double spawnMs = 0; tickHolds = tickDespawns = tickCount = 0;
            if (Planet != null && terrain != null && terrain.Generator != null)
            {
                if (autoSpawn && Time.time >= nextSpawn)
                {
                    UnityEngine.Profiling.Profiler.BeginSample("Creatures.SpawnTick");
                    nextSpawn = Time.time + SpawnInterval; SpawnTick();
                    UnityEngine.Profiling.Profiler.EndSample();
                    spawnMs = watch.Elapsed.TotalMilliseconds;
                }
                if (vitals == null && player != null) vitals = player.GetComponent<PlayerVitals>();
                var p = player != null ? (Vector2)player.transform.position : Vector2.zero;
                float daylight = Daylight, now = Time.time, dt = Time.deltaTime;
                bool flare = FlareActive;
                UnityEngine.Profiling.Profiler.BeginSample("Creatures.Tick");
                foreach (var c in pool)
                {
                    if (!c.Alive) continue;
                    tickCount++;
                    if (now < c.StagedUntil)
                    {
                        // U-153: a staged shot: still, facing where the shot wants it (the whale head first), no steering or reaction.
                        if (c.Body != null) c.Body.linearVelocity = Vector2.zero;
                        if (c.View != null) c.View.flipX = c.StagedFacing < 0;
                        if (c.Rig != null) c.SetRigFacing(c.StagedFacing > 0);
                        continue;
                    }
                    Tick(c, p, daylight, now, dt, flare);
                }
                UnityEngine.Profiling.Profiler.EndSample();
            }
            LastAiMs = watch.Elapsed.TotalMilliseconds;
            if (LastAiMs > SpikeMs) // only then: the string allocates
                LastSpikeNote = $"{LastAiMs:F2} ms at t {Time.time:F2} (dt {Time.deltaTime * 1000f:F0} ms, frame {Time.frameCount}): spawn tick {spawnMs:F2} ms, {tickCount} ticks {LastAiMs - spawnMs:F2} ms, holds {tickHolds}, despawns {tickDespawns}, GC gen0 {System.GC.CollectionCount(0)}";
        }

        void Tick(Creature c, Vector2 player, float daylight, float now, float dt, bool flare)
        {
            var spec = c.Spec;
            Vector2 pos = c.Body.position;
            float dx = player.x - pos.x, dy = player.y - pos.y, adx = Mathf.Abs(dx);

            if (adx > DespawnDistance || Mathf.Abs(dy) > DespawnDistance || (!spec.ActiveAt(daylight) && adx > 22f)) { tickDespawns++; Despawn(c); return; } // night hunters leave at dawn, off-screen

            float feetY = pos.y - spec.size.y * 0.5f;
            // U-156 (D-161): on a smooth planet the feet ride the traced outline, up to ½ m off the hidden grid's tops: the tile under them is the
            // one whose top is nearest the feet; elsewhere the tile just under the feet, as before.
            int tx = Mathf.FloorToInt(pos.x), ty = terrain.SmoothGround ? Mathf.RoundToInt(feetY) - 1 : Mathf.FloorToInt(feetY - 0.1f);
            if (!spec.Flies)
            {
                // Hold bodies whose ground isn't there yet (streamed chunk not resident or still building).
                bool ready = terrain.IsCollisionReady(tx, ty) && terrain.IsCollisionReady(tx, ty - 2);
                if (!ready)
                {
                    tickHolds++;
                    if (!c.Held) { c.Held = true; c.Body.simulated = false; }
                    return;
                }
                if (c.Held) { c.Held = false; c.Body.simulated = true; c.Body.linearVelocity = Vector2.zero; }
            }

            // The Cinderhulk follows the terminator every frame: its night sheet shows (and its window opens)
            // the moment it crosses, not at its next think (LEAD, U-055 review).
            if (spec.nightArtKey != null) TrackZone(c, now);
            if (now >= c.nextThink)
            {
                c.nextThink = now + ThinkInterval;
                Think(c, dx, dy, adx, flare, now);
            }

            // Steer.
            float speed = c.State switch
            {
                CreatureState.Flee or CreatureState.Chase => spec.runSpeed,
                CreatureState.Wander => spec.wanderSpeed,
                _ => 0f,
            };
            var v = c.Body.linearVelocity;
            bool grounded; // U-108: ground contact this tick, for the fly clip (Creature.Animate keeps the hysteresis)
            if (spec.Flies)
            {
                // U-108: a flier's contact is the tile under its feet alone (no gravity, so no velocity test: a flier steered
                // back to its band still counts as landed while its feet touch). One GetTile: within the 0.5 ms AI budget.
                grounded = TileId.IsSolid(terrain.GetTile(tx, ty));
                // U-114: a swimmer turns at the pool's wall or shore (the tile ahead is not water) instead of leaving the water.
                if (spec.habitat == Habitat.Water && c.State != CreatureState.Chase && terrain.GetTile(tx + c.dir, ty) != TileId.Water) c.dir = -c.dir;
                // 2D: chase straight at the surveyor; otherwise hold the altitude chosen at the last think.
                Vector2 want;
                if (c.State == CreatureState.Chase)
                {
                    var to = new Vector2(dx, dy + 0.6f);
                    want = to.sqrMagnitude > 1e-4f ? to.normalized * speed : Vector2.zero;
                    if (HoldsOff(spec.followDistance, to.magnitude)) want = Vector2.zero; // U-119 (D-087): the Maw follows at a distance
                }
                else want = new Vector2(c.dir * speed, Mathf.Clamp((c.altitude - pos.y) * 1.5f, -speed - 1f, speed + 1f));
                v = Vector2.MoveTowards(v, want, FlyAccel * dt);
            }
            else
            {
                bool quiet = Mathf.Abs(v.y) < 1.0f; // not airborne (a body pressed into a prop jitters a little)
                grounded = quiet && TileId.IsSolid(terrain.GetTile(tx, ty));
                // U-099: a wall the tiles cannot show (a crate stack, a base piece, the pad): the body has not moved for BlockedSeconds
                // while it wanted to run, whatever it stands on. Judged on position over time, never on the velocity: between two
                // physics steps an Update reads back the velocity it set the frame before.
                bool stuck = false;
                if (speed > 0f && quiet)
                {
                    if (now - c.blockAnchorT >= BlockedSeconds)
                    {
                        stuck = c.blockAnchorT > 0f && Mathf.Abs(pos.x - c.blockAnchorX) < 0.1f;
                        c.blockAnchorX = pos.x; c.blockAnchorT = now;
                    }
                }
                else { c.blockAnchorX = pos.x; c.blockAnchorT = now; }
                if (c.State == CreatureState.Chase && now < c.waitUntil) speed = 0f; // waiting at a wall it cannot see
                if ((grounded && speed > 0f) || stuck)
                {
                    int ahead = Mathf.FloorToInt(pos.x + c.dir * (spec.size.x * 0.5f + 0.3f));
                    int feet = ty + 1;
                    // U-156 (D-161): on the traced outline a 1-tile step is a slope the body walks up; only 2 tiles is a wall (no hop needed).
                    int rise = terrain.SmoothGround ? 1 : 0;
                    bool wall = grounded && TileId.IsSolid(terrain.GetTile(ahead, feet + rise));
                    if (wall || stuck)
                    {
                        // A 1-tile step is hopped (air above it and headroom); anything taller is a wall (U-099: a 2-tile wall stops a chase).
                        bool climbable = wall && rise == 0 && !TileId.IsSolid(terrain.GetTile(ahead, feet + 1)) && !TileId.IsSolid(terrain.GetTile(tx, feet + Mathf.CeilToInt(spec.size.y) + 1));
                        if (climbable) v.y = spec.jumpSpeed;
                        else if (c.State == CreatureState.Chase) { speed = 0f; if (stuck) c.waitUntil = now + BlockedSeconds; } // waits at the wall, never bumps through it; the legs stop with the body
                        else { c.dir = -c.dir; c.keepDirUntil = now + WallTurnSeconds; c.blockAnchorX = pos.x; c.blockAnchorT = now; } // Wander and Flee turn and move on along the wall
                    }
                }
                // U-188 (BLENDER's 0.6.0 smoke read: a bear swimming beside the shark): a land walker never walks into the sea. Water ahead (half
                // its body, half a metre and its stopping distance at this speed) at its feet or down the shore's slope turns it like a wall, and a
                // chase waits at the shore; judged grounded or not (a run down the shore's slope leaves the ground between steps).
                if (speed > 0f)
                {
                    float look = spec.size.x * 0.5f + 0.5f + v.x * v.x / (2f * Accel);
                    if (SeaAhead(Mathf.FloorToInt(pos.x + c.dir * look), ty + 1))
                    {
                        if (c.State == CreatureState.Chase) speed = 0f;
                        else { c.dir = -c.dir; c.keepDirUntil = now + WallTurnSeconds; }
                    }
                }
                v.x = Mathf.MoveTowards(v.x, c.dir * speed, Accel * dt);
            }
            if (c.knockFor > 0f) { c.knockFor -= dt; v.x = c.knockVx; } // U-089: the hit knock overrides the steering
            c.Body.linearVelocity = v;
            if (c.View != null) c.View.flipX = (spec.Flies ? (v.x != 0f ? Mathf.Sign(v.x) : c.dir) : c.dir) < 0;
            if (c.Model != null && c.Model.Ready && c.View != null) c.Model.SetFacing(!c.View.flipX); // U-075: the model faces like the sprite
            if (c.Rig != null)
            {
                c.SetRigFacing(!c.View.flipX); // U-119: the rig faces like the sprite
                if (spec.reactRadius > 0f) c.SetRigReacting(vitals != null && !vitals.Dead && dx * dx + dy * dy < spec.reactRadius * spec.reactRadius);
            }

            // U-093 (D-087): a chasing creature that reaches the surveyor bumps them (no damage).
            bool hunting = c.State == CreatureState.Chase;
            float reachX = spec.size.x * 0.5f + 0.6f, reachY = spec.Flies ? spec.size.y * 0.5f + 1.2f : 1.4f;
            if (hunting && spec.followDistance <= 0f && vitals != null && !vitals.Dead && adx < reachX && Mathf.Abs(dy) < reachY && now >= c.biteReady) Bump(c, now); // U-119: a follower never bumps
            c.Animate(dt, Mathf.Abs(v.x) + (spec.Flies ? Mathf.Abs(v.y) : 0f), grounded);
        }

        /// <summary>
        /// U-093 (D-087): contact. The surveyor is bumped 0.8 m away with dizzy stars (PlayerController.Bump), the creature
        /// bounces 0.5 m back with a squash (Creature.React) and plays its `attack` clip as the bump; no meter changes.
        /// One bump per creature per BumpEvery.
        /// </summary>
        public void Bump(Creature c, float now)
        {
            c.biteReady = now + BumpEvery;
            c.attackFor = 0.4f;
            if (player == null) return;
            Vector2 from = c.Body.position;
            player.Bump(from);
            c.React(from - player.Body.position);
            Bumps++;
        }

        /// <summary>U-119 (D-087): a hunter with a follow distance stops short of it (the Maw keeps 14 m off the surveyor). Pure.</summary>
        public static bool HoldsOff(float followDistance, float distance) => followDistance > 0f && distance < followDistance;

        /// <summary>Seconds between two bumps by one creature.</summary>
        public const float BumpEvery = 1.2f;
        /// <summary>U-099: a creature that wanted to move but stood still this long is blocked by something the tiles do not show.</summary>
        public const float BlockedSeconds = 0.2f;
        /// <summary>U-099: after a wall turn a fleeing creature keeps its new direction this long before its thinks may re-aim it away from the surveyor.</summary>
        public const float WallTurnSeconds = 1.5f;
        /// <summary>U-114 (D-119): a territorial creature bolts when the surveyor comes inside PushRange, rears (react) every HuffEvery s while they stand inside senseRange, and runs TerritorialFleeSeconds after a push.</summary>
        public const float PushRange = 1.6f, HuffEvery = 2.5f, RearSeconds = 0.8f, TerritorialFleeSeconds = 4f;
        /// <summary>Bumps given since load (tests).</summary>
        public int Bumps { get; private set; }

        void Think(Creature c, float dx, float dy, float adx, bool flare, float now)
        {
            var spec = c.Spec;
            if (Planet.id == PlanetId.Mercury) TrackZone(c, now);
            if (spec.Flies) c.altitude = AltitudeFor(c);

            bool playerAlive = vitals == null || !vitals.Dead;
            if (spec.temper == Temper.Territorial)
            {
                // U-114 (D-119, Bible §7.1): the bear holds its ground. Pushed: it bolts. In range: it stands, faces the surveyor and rears.
                if (playerAlive && adx < PushRange && Mathf.Abs(dy) < 2f) { c.fleeUntil = now + TerritorialFleeSeconds; c.State = CreatureState.Flee; c.dir = dx > 0f ? -1 : 1; return; }
                if (now < c.fleeUntil) { c.State = CreatureState.Flee; if (now >= c.keepDirUntil) c.dir = dx > 0f ? -1 : 1; return; }
                if (playerAlive && adx < spec.senseRange && Mathf.Abs(dy) < 4f)
                {
                    c.State = CreatureState.Idle;
                    c.dir = dx > 0f ? 1 : -1;
                    if (now >= c.nextHuff) { c.nextHuff = now + HuffEvery; c.Rear(RearSeconds); }
                    return;
                }
            }
            bool hunts = spec.temper == Temper.Hunts || (spec.huntsDuringFlare && flare);
            if (now < c.fleeUntil) hunts = false; // the Veil Serpent recoils from cold
            if (!hunts)
            {
                if (adx < spec.senseRange || now < c.fleeUntil) { c.State = CreatureState.Flee; if (now >= c.keepDirUntil) c.dir = dx > 0f ? -1 : 1; return; } // U-099: a wall turn holds
                if (c.State == CreatureState.Flee && adx < spec.senseRange * 1.8f) return; // keep running a while
            }
            else
            {
                float reachY = spec.Flies ? spec.senseRange : 6f;
                if (playerAlive && adx < spec.senseRange && Mathf.Abs(dy) < reachY) { c.State = CreatureState.Chase; c.dir = dx > 0f ? 1 : -1; return; }
                if (c.State == CreatureState.Chase && playerAlive && adx < spec.senseRange * 1.6f) { c.dir = dx > 0f ? 1 : -1; return; }
            }
            // Wander: walk a while, pause a while, sometimes turn.
            float r = Hash01(c.serial * 31 + Mathf.FloorToInt(Time.time * 0.5f), 9);
            c.State = r < 0.25f ? CreatureState.Idle : CreatureState.Wander;
            if (spec.Flies && c.State == CreatureState.Idle) c.State = CreatureState.Wander; // fliers keep moving
            if (r > 0.9f) c.dir = -c.dir;
        }

        /// <summary>The terminator (Mercury): the zone where it stands, and when it crossed into night.</summary>
        void TrackZone(Creature c, float now)
        {
            if (Planet.id != PlanetId.Mercury) return;
            var zone = ZoneAt(c.Body.position.x);
            if (zone == MercuryZone.Night && c.Zone != MercuryZone.Night) c.NightfallAt = now;
            c.Zone = zone;
        }

        /// <summary>The height a flier keeps: its hover band over the ground below, or a lane in the deck band.</summary>
        float AltitudeFor(Creature c)
        {
            var spec = c.Spec;
            float wobble = Hash01(c.serial * 17 + Mathf.FloorToInt(Time.time * 0.2f), 11);
            if (spec.habitat == Habitat.Deck)
                return VenusLandforms.DeckY + (wobble - 0.5f) * 2f * (VenusLandforms.DeckHalfBand - 10f);
            int ground = terrain.TopSolidY(Mathf.FloorToInt(c.Body.position.x));
            if (spec.habitat == Habitat.Water)
            {
                // U-114: between the floor clearance and the surface of the pool it is in (a swimmer that finds no water holds its floor height).
                int depth = WaterDepthAbove(Mathf.FloorToInt(c.Body.position.x), ground);
                float lo = ground + 1f + spec.floorClearance + spec.size.y * 0.5f;
                float hi = Mathf.Max(lo, ground + 1f + depth - spec.size.y * 0.5f);
                return Mathf.Lerp(lo, hi, wobble);
            }
            // U-188: over the sea the band stands on the water line, not the seabed (a gull never flies under the water)
            return ground + 1f + WaterDepthAbove(Mathf.FloorToInt(c.Body.position.x), ground) + Mathf.Lerp(spec.hoverMin, spec.hoverMax, wobble);
        }

        /// <summary>U-188: water at the feet's cell in column x or within four cells under it (a shore's slope).</summary>
        bool SeaAhead(int x, int feet)
        {
            // within the AI budget (D-047): only Earth holds water and only in its sea columns (U-166), and the walk down stops at the ground
            if (Planet == null || Planet.id != PlanetId.Earth) return false;
            if (terrain.BaseGenerator is SolidWorldGenerator g && !g.SeaAt(x)) return false;
            for (int k = 0; k <= 4; k++)
            {
                byte id = terrain.GetTile(x, feet - k);
                if (id == TileId.Water) return true;
                if (TileId.IsSolid(id)) return false; // the shore's ground: no water under it
            }
            return false;
        }

        /// <summary>U-114: water tiles standing on the floor at `floorY` in column tx (0 on dry ground); at most 64 looked at.</summary>
        int WaterDepthAbove(int tx, int floorY)
        {
            int depth = 0;
            for (int y = floorY + 1; y < floorY + 65 && y < Planet.worldHeight && terrain.GetTile(tx, y) == TileId.Water; y++) depth++;
            return depth;
        }

        float Hash01(int k, int salt) => (float)Meridian.Planet.Weather.DustStormSchedule.Hash01(seed, k, salt + 40);

        void OnDestroy()
        {
            for (int i = 0; i < artHandles.Length; i++) if (artHandles[i].IsValid()) global::Meridian.Art.ArtLoad.Release(artHandles[i]);
            for (int i = 0; i < nightHandles.Length; i++) if (nightHandles[i].IsValid()) global::Meridian.Art.ArtLoad.Release(nightHandles[i]);
        }
    }
}
