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
    /// every frame (run, hop 1–2 tile steps, turn at walls), bite when a hunter reaches the player.
    /// Creatures whose chunk isn't loaded with collision are held in place, so none falls through
    /// streamed ground. At most 20 alive. No allocation per frame.
    /// U-055: fliers (a hover band over the ground, or Venus's cloud deck) steer in 2D without gravity;
    /// spawn rules see Mercury's zones and Venus's features; creatures animate from their sheets
    /// (idle/walk/attack/hurt); the Cinderhulk wears its night sheet past the terminator and tracks nightfall.
    /// </summary>
    public sealed class CreatureDirector : MonoBehaviour
    {
        public const int MaxCreatures = 20;
        public const float SpawnInterval = 1.5f;
        public const float SpawnMin = 24f, SpawnMax = 40f, DespawnDistance = 64f;
        const float ThinkInterval = 0.25f, Accel = 30f, FlyAccel = 12f;

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
        public IReadOnlyList<Creature> All => pool;

        readonly List<Creature> pool = new List<Creature>(MaxCreatures);
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
            seed = worldSeed;
            DespawnAll();
            nextSpawn = 0f;
            for (int s = 0; s < SpeciesCount; s++)
            {
                var spec = SpeciesSpec.Get((Species)s);
                // U-060: the PlanetSide scene is reused across planets; drop other planets' creature sheets
                // (they stayed loaded until destroy and the dev-build texture memory grew with every planet).
                if (spec.planet != planet.id) { ReleaseArt(s); continue; }
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
                Addressables.Release(l);
                if (!exists || this == null) return;
                // Left the species' planet while the lookup ran: don't load it (nothing would release it).
                if (Planet == null || SpeciesSpec.Get((Species)s).planet != Planet.id) return;
                if ((night ? nightHandles[s] : artHandles[s]).IsValid()) return;
                var h = ArtLoad.Asset<IList<Sprite>>(key);
                if (night) nightHandles[s] = h; else artHandles[s] = h;
                h.Completed += op =>
                {
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
                };
            };
        }

        void ReleaseArt(int s)
        {
            if (artHandles[s].IsValid()) Addressables.Release(artHandles[s]);
            if (nightHandles[s].IsValid()) Addressables.Release(nightHandles[s]);
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
                    ? new Vector2(tx + 0.5f, site.surfaceY + 1f + Mathf.Lerp(spec.hoverMin, spec.hoverMax, Hash01(serial, 6)))
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
                IgnoreBodies(c);
                AliveCount++;
                return c;
            }
            return null;
        }

        void IgnoreBodies(Creature c)
        {
            // Creatures pass through each other and through the player (contact is a bite, not a shove).
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
            if (Planet != null && terrain != null && terrain.Generator != null)
            {
                if (autoSpawn && Time.time >= nextSpawn) { nextSpawn = Time.time + SpawnInterval; SpawnTick(); }
                if (vitals == null && player != null) vitals = player.GetComponent<PlayerVitals>();
                var p = player != null ? (Vector2)player.transform.position : Vector2.zero;
                float daylight = Daylight, now = Time.time, dt = Time.deltaTime;
                bool flare = FlareActive;
                foreach (var c in pool)
                {
                    if (!c.Alive) continue;
                    Tick(c, p, daylight, now, dt, flare);
                }
            }
            LastAiMs = watch.Elapsed.TotalMilliseconds;
        }

        void Tick(Creature c, Vector2 player, float daylight, float now, float dt, bool flare)
        {
            var spec = c.Spec;
            Vector2 pos = c.Body.position;
            // U-088: a parried creature is staggered (Creature.StaggerSeconds): it stands, bites nothing, then resumes.
            if (c.staggerFor > 0f)
            {
                c.staggerFor -= dt;
                var sv = c.Body.linearVelocity;
                if (c.knockFor > 0f) { c.knockFor -= dt; sv.x = c.knockVx; } else sv.x = Mathf.MoveTowards(sv.x, 0f, Creature.StaggerBrake * dt);
                c.Body.linearVelocity = sv;
                c.Animate(dt, 0f);
                return;
            }
            float dx = player.x - pos.x, dy = player.y - pos.y, adx = Mathf.Abs(dx);

            if (adx > DespawnDistance || Mathf.Abs(dy) > DespawnDistance || (!spec.ActiveAt(daylight) && adx > 22f)) { Despawn(c); return; } // night hunters leave at dawn, off-screen

            int tx = Mathf.FloorToInt(pos.x), ty = Mathf.FloorToInt(pos.y - spec.size.y * 0.5f - 0.1f);
            if (!spec.Flies)
            {
                // Hold bodies whose ground isn't there yet (streamed chunk not resident or still building).
                bool ready = terrain.IsCollisionReady(tx, ty) && terrain.IsCollisionReady(tx, ty - 2);
                if (!ready)
                {
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
            if (spec.Flies)
            {
                // 2D: chase straight at the surveyor; otherwise hold the altitude chosen at the last think.
                Vector2 want;
                if (c.State == CreatureState.Chase)
                {
                    var to = new Vector2(dx, dy + 0.6f);
                    want = to.sqrMagnitude > 1e-4f ? to.normalized * speed : Vector2.zero;
                }
                else want = new Vector2(c.dir * speed, Mathf.Clamp((c.altitude - pos.y) * 1.5f, -speed - 1f, speed + 1f));
                v = Vector2.MoveTowards(v, want, FlyAccel * dt);
            }
            else
            {
                bool grounded = Mathf.Abs(v.y) < 0.6f && TileId.IsSolid(terrain.GetTile(tx, ty));
                if (grounded && speed > 0f)
                {
                    int ahead = Mathf.FloorToInt(pos.x + c.dir * (spec.size.x * 0.5f + 0.3f));
                    int feet = ty + 1;
                    bool wall = TileId.IsSolid(terrain.GetTile(ahead, feet));
                    if (wall)
                    {
                        bool climbable = !TileId.IsSolid(terrain.GetTile(ahead, feet + 2)) && !TileId.IsSolid(terrain.GetTile(tx, feet + Mathf.CeilToInt(spec.size.y) + 1));
                        if (climbable) v.y = spec.jumpSpeed;
                        else if (c.State == CreatureState.Wander) c.dir = -c.dir; // a cliff: turn back
                    }
                }
                v.x = Mathf.MoveTowards(v.x, c.dir * speed, Accel * dt);
            }
            if (c.knockFor > 0f) { c.knockFor -= dt; v.x = c.knockVx; } // U-089: the hit knock overrides the steering
            c.Body.linearVelocity = v;
            if (c.View != null) c.View.flipX = (spec.Flies ? (v.x != 0f ? Mathf.Sign(v.x) : c.dir) : c.dir) < 0;
            if (c.Model != null && c.Model.Ready && c.View != null) c.Model.SetFacing(!c.View.flipX); // U-075: the model faces like the sprite

            // Bite.
            bool hunting = c.State == CreatureState.Chase;
            float reachX = spec.size.x * 0.5f + 0.6f, reachY = spec.Flies ? spec.size.y * 0.5f + 1.2f : 1.4f;
            if (hunting && vitals != null && !vitals.Dead && adx < reachX && Mathf.Abs(dy) < reachY && now >= c.biteReady) Bite(c, now);
            c.Animate(dt, Mathf.Abs(v.x) + (spec.Flies ? Mathf.Abs(v.y) : 0f));
        }

        /// <summary>U-088: a bite lands unless the player's parry window catches it: then 0 damage and the attacker staggers 1.2 s.</summary>
        public void Bite(Creature c, float now)
        {
            c.biteReady = now + 1.2f;
            c.attackFor = 0.4f;
            if (player != null && player.TryParryAttack(c.Body.position)) { c.staggerFor = Creature.StaggerSeconds; c.attackFor = 0f; return; }
            if (vitals == null && player != null) vitals = player.GetComponent<PlayerVitals>();
            player?.Knock(c.Body.position); // U-089: knocked away from the biter, flash, hit_react
            if (vitals != null) vitals.Damage(c.Spec.biteDamage);
        }

        void Think(Creature c, float dx, float dy, float adx, bool flare, float now)
        {
            var spec = c.Spec;
            if (Planet.id == PlanetId.Mercury) TrackZone(c, now);
            if (spec.Flies) c.altitude = AltitudeFor(c);

            bool playerAlive = vitals == null || !vitals.Dead;
            bool hunts = spec.temper == Temper.Hunts || (spec.huntsDuringFlare && flare);
            if (now < c.fleeUntil) hunts = false; // the Veil Serpent recoils from cold
            if (!hunts)
            {
                if (adx < spec.senseRange || now < c.fleeUntil) { c.State = CreatureState.Flee; c.dir = dx > 0f ? -1 : 1; return; }
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
            return ground + 1f + Mathf.Lerp(spec.hoverMin, spec.hoverMax, wobble);
        }

        float Hash01(int k, int salt) => (float)Meridian.Planet.Weather.DustStormSchedule.Hash01(seed, k, salt + 40);

        void OnDestroy()
        {
            for (int i = 0; i < artHandles.Length; i++) if (artHandles[i].IsValid()) Addressables.Release(artHandles[i]);
            for (int i = 0; i < nightHandles.Length; i++) if (nightHandles[i].IsValid()) Addressables.Release(nightHandles[i]);
        }
    }
}
