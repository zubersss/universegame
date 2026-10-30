using System.Collections.Generic;
using System.Diagnostics;
using Meridian.Planet.Lighting;
using Meridian.Planets;
using Meridian.Player;
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
    /// </summary>
    public sealed class CreatureDirector : MonoBehaviour
    {
        public const int MaxCreatures = 20;
        public const float SpawnInterval = 1.5f;
        public const float SpawnMin = 24f, SpawnMax = 40f, DespawnDistance = 64f;
        const float ThinkInterval = 0.25f, Accel = 30f;

        public TerrainStreamer terrain;
        public PlayerController player;
        public DayNightLighting dayNight;
        /// <summary>Natural spawning. Off in batch runs (other tests stay deterministic) unless AutoSpawnOverride says otherwise.</summary>
        public bool autoSpawn = true;
        public static bool? AutoSpawnOverride;

        public PlanetConfig Planet { get; private set; }
        public int AliveCount { get; private set; }
        public double LastAiMs { get; private set; }
        public IReadOnlyList<Creature> All => pool;

        readonly List<Creature> pool = new List<Creature>(MaxCreatures);
        readonly Sprite[] art = new Sprite[4];
        readonly AsyncOperationHandle<IList<Sprite>>[] artHandles = new AsyncOperationHandle<IList<Sprite>>[4];
        readonly Stopwatch watch = new Stopwatch();
        static Sprite placeholder;
        float nextSpawn;
        int serial, seed;
        PlayerVitals vitals;
        Collider2D[] playerColliders;

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
            for (int s = 0; s < SpeciesSpec.Count; s++)
                if (SpeciesSpec.Get((Species)s).planet == planet.id && art[s] == null && !artHandles[s].IsValid()) LoadArt(s);
        }

        /// <summary>Real art when BLENDER's creature sheets exist (B-015/B-016); a tinted box until then.</summary>
        void LoadArt(int s)
        {
            string key = SpeciesSpec.Get((Species)s).artKey;
            var loc = Addressables.LoadResourceLocationsAsync(key);
            loc.Completed += l =>
            {
                bool exists = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                Addressables.Release(l);
                if (!exists || this == null) return;
                artHandles[s] = Addressables.LoadAssetAsync<IList<Sprite>>(key);
                artHandles[s].Completed += op =>
                {
                    if (op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                    Sprite first = op.Result[0];
                    foreach (var sp in op.Result) if (sp.name.EndsWith("_0")) first = sp;
                    art[s] = first;
                };
            };
        }

        public float Daylight => dayNight != null ? DayNightMath.Daylight(dayNight.LocalTime) : 1f;

        // ---------- spawning ----------

        /// <summary>One spawn attempt per species of this planet (called every 1.5 s when autoSpawn).</summary>
        public void SpawnTick()
        {
            if (Planet == null || terrain == null || terrain.Generator == null || player == null) return;
            float daylight = Daylight;
            var p = player.transform.position;
            for (int s = 0; s < SpeciesSpec.Count; s++)
            {
                var spec = SpeciesSpec.Get((Species)s);
                if (spec.planet != Planet.id || !spec.ActiveAt(daylight)) continue;
                if (CountOf(spec.id) + spec.packMin > spec.maxAlive) continue;
                serial++;
                if (Hash01(serial, 1) > 0.4f) continue; // not every tick
                float side = Hash01(serial, 2) < 0.5f ? -1f : 1f;
                float x = p.x + side * Mathf.Lerp(SpawnMin, SpawnMax, Hash01(serial, 3));
                int pack = spec.packMin + (int)(Hash01(serial, 4) * (spec.packMax - spec.packMin + 1));
                SpawnPack(spec, x, Mathf.Min(pack, spec.maxAlive - CountOf(spec.id)));
            }
        }

        void SpawnPack(SpeciesSpec spec, float x, int count)
        {
            for (int i = 0; i < count; i++)
            {
                int tx = Mathf.FloorToInt(x + i * 1.6f);
                int surface = terrain.Generator.SurfaceHeight(terrain.WrapX(tx));
                byte top = terrain.GetTile(tx, surface);
                if (!spec.BiomeAllows(top, surface, Planet.datumY)) return;
                if (!terrain.IsCollisionReady(tx, surface)) return;
                if (Spawn(spec.id, new Vector2(tx + 0.5f, surface + 1f + spec.size.y * 0.5f + 0.05f)) == null) return;
            }
        }

        /// <summary>Places one creature (tests use this directly). Null when 20 are already alive.</summary>
        public Creature Spawn(Species species, Vector2 position)
        {
            foreach (var c in pool)
            {
                if (c.Alive) continue;
                var spec = SpeciesSpec.Get(species);
                c.Setup(spec, position, art[(int)species] != null ? art[(int)species] : placeholder, ++serial);
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
                foreach (var c in pool)
                {
                    if (!c.Alive) continue;
                    Tick(c, p, daylight, now, dt);
                }
            }
            LastAiMs = watch.Elapsed.TotalMilliseconds;
        }

        void Tick(Creature c, Vector2 player, float daylight, float now, float dt)
        {
            var spec = c.Spec;
            Vector2 pos = c.Body.position;
            float dx = player.x - pos.x, dy = player.y - pos.y, adx = Mathf.Abs(dx);

            if (adx > DespawnDistance || (!spec.ActiveAt(daylight) && adx > 22f)) { Despawn(c); return; } // night hunters leave at dawn, off-screen

            // Hold bodies whose ground isn't there yet (streamed chunk not resident or still building).
            int tx = Mathf.FloorToInt(pos.x), ty = Mathf.FloorToInt(pos.y - spec.size.y * 0.5f - 0.1f);
            bool ready = terrain.IsCollisionReady(tx, ty) && terrain.IsCollisionReady(tx, ty - 2);
            if (!ready)
            {
                if (!c.Held) { c.Held = true; c.Body.simulated = false; }
                return;
            }
            if (c.Held) { c.Held = false; c.Body.simulated = true; c.Body.linearVelocity = Vector2.zero; }

            if (now >= c.nextThink)
            {
                c.nextThink = now + ThinkInterval;
                Think(c, dx, dy, adx);
            }

            // Steer.
            float speed = c.State switch
            {
                CreatureState.Flee or CreatureState.Chase => spec.runSpeed,
                CreatureState.Wander => spec.wanderSpeed,
                _ => 0f,
            };
            var v = c.Body.linearVelocity;
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
            c.Body.linearVelocity = v;
            if (c.View != null) c.View.flipX = c.dir < 0;

            // Bite.
            if (spec.temper == Temper.Hunts && c.State == CreatureState.Chase && vitals != null && !vitals.Dead
                && adx < spec.size.x * 0.5f + 0.6f && Mathf.Abs(dy) < 1.4f && now >= c.biteReady)
            {
                c.biteReady = now + 1.2f;
                vitals.Damage(spec.biteDamage);
            }
        }

        void Think(Creature c, float dx, float dy, float adx)
        {
            var spec = c.Spec;
            bool playerAlive = vitals == null || !vitals.Dead;
            if (spec.temper == Temper.Flees)
            {
                if (adx < spec.senseRange) { c.State = CreatureState.Flee; c.dir = dx > 0f ? -1 : 1; return; }
                if (c.State == CreatureState.Flee && adx < spec.senseRange * 1.8f) return; // keep running a while
            }
            else
            {
                if (playerAlive && adx < spec.senseRange && Mathf.Abs(dy) < 6f) { c.State = CreatureState.Chase; c.dir = dx > 0f ? 1 : -1; return; }
                if (c.State == CreatureState.Chase && playerAlive && adx < spec.senseRange * 1.6f) { c.dir = dx > 0f ? 1 : -1; return; }
            }
            // Wander: walk a while, pause a while, sometimes turn.
            float r = Hash01(c.serial * 31 + Mathf.FloorToInt(Time.time * 0.5f), 9);
            c.State = r < 0.25f ? CreatureState.Idle : CreatureState.Wander;
            if (r > 0.9f) c.dir = -c.dir;
        }

        float Hash01(int k, int salt) => (float)Meridian.Planet.Weather.DustStormSchedule.Hash01(seed, k, salt + 40);

        void OnDestroy()
        {
            for (int i = 0; i < artHandles.Length; i++) if (artHandles[i].IsValid()) Addressables.Release(artHandles[i]);
        }
    }
}
