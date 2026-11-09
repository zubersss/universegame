using System.Collections.Generic;
using Meridian.Hazards;
using Meridian.Planet.POI;
using Meridian.Planets;
using Meridian.Player;
using Meridian.Terrain;
using UnityEngine;

namespace Meridian.Creatures.Wardens
{
    /// <summary>
    /// U-053 Wardens, basic (Bible §2, §9): a sentinel patrols each Warden site on the planet (vault, outpost);
    /// digging feeds the per-area WardenMeter and an area past its threshold calls a sentinel within SpawnDelay
    /// and wakes the patrols nearby. D-087 (no combat): called sentinels close in beside the surveyor, ring their
    /// bell every RingEvery within RingRange (the `attack` clip) and bump them on contact (PlayerController.Bump:
    /// a knock, never a meter). The tow and the Beam lock arrive with their own task. Everything is pooled:
    /// MaxSentinels bodies, no allocation per frame. Lives on the PlanetSide root.
    /// </summary>
    public sealed class WardenDirector : MonoBehaviour
    {
        public const int MaxSentinels = 6;
        public const float SpawnDelay = 2.5f, AlertRadius = 60f, GiveUpDistance = 70f, RingRange = 14f, RingEvery = 1.6f;
        /// <summary>Contact distance (sentinel centre to the surveyor's centre) and the time between two bumps by one sentinel.</summary>
        public const float BumpRadius = 1.1f, BumpEvery = 1.2f;
        static readonly string[] SiteIds = { "warden_vault", "warden_outpost" };
        /// <summary>U-190 (Bible 5.3 §8.1): sites the meter guards without a patrol of their own (the Survey Archive).</summary>
        static readonly string[] GuardOnlyIds = { "survey_archive" };
        /// <summary>U-190: how often a hunting sentinel re-plans its way through open air (s), and how finely a path is sampled (m).</summary>
        public const float ReplanEvery = 0.25f, PathStep = 0.5f;
        /// <summary>U-190: steps a sentinel took that would have entered rock and were refused (tests: 0 is never needed, it is a guard).</summary>
        public int RockRefusals { get; private set; }

        public TerrainStreamer terrain;
        public PlayerController player;
        public HazardSystem hazards;
        public PoiPlacer pois;

        public readonly WardenMeter meter = new WardenMeter();
        public readonly List<Sentinel> sentinels = new List<Sentinel>(MaxSentinels);
        /// <summary>Time spent in the last Update (ms): the AI budget (≤ 0.3 ms with six sentinels).</summary>
        public float LastAiMs { get; private set; }
        public int Active { get; private set; }
        public int Trips { get; private set; }
        /// <summary>Bumps sentinels have given the surveyor (tests).</summary>
        public int Bumps { get; private set; }

        readonly List<(float at, Vector2 where)> pending = new List<(float, Vector2)>(4);
        readonly System.Diagnostics.Stopwatch watch = new System.Diagnostics.Stopwatch();
        bool sitesPending, built;

        void Build()
        {
            if (built) return;
            built = true;
            for (int i = 0; i < MaxSentinels; i++)
            {
                var go = new GameObject("Sentinel" + i);
                go.transform.SetParent(transform, false);
                go.SetActive(false);
                var s = go.AddComponent<Sentinel>();
                s.director = this;
                s.Build();
                sentinels.Add(s);
            }
        }

        public void ConfigureFor(PlanetConfig planet)
        {
            Build();
            if (terrain != null) { terrain.TileChanged -= OnTile; terrain.TileChanged += OnTile; }
            DespawnAll();
            meter.Clear();
            pending.Clear();
            Trips = 0;
            sitesPending = true;
        }

        void OnDestroy() { if (terrain != null) terrain.TileChanged -= OnTile; }

        public void DespawnAll()
        {
            foreach (var s in sentinels) s.gameObject.SetActive(false);
            Active = 0;
        }

        /// <summary>Places a patrol at each Warden site once the POIs are placed.</summary>
        void PlaceSites()
        {
            if (pois == null || pois.placed.Count == 0) return;
            sitesPending = false;
            foreach (var p in pois.placed)
            {
                if (System.Array.IndexOf(GuardOnlyIds, p.def.id) >= 0) { meter.Guard(p.def.CenterX); continue; }
                if (System.Array.IndexOf(SiteIds, p.def.id) < 0) continue;
                meter.Guard(p.def.CenterX);
                var post = new Vector2(p.def.CenterX, p.groundY + 7f);
                Spawn(post, post, SentinelState.Patrol);
            }
        }

        void OnTile(int x, int y, byte old, byte now)
        {
            if (!TileId.IsSolid(old) || TileId.IsSolid(now)) return;
            if (!meter.Dig(x, Time.time)) return;
            Trips++;
            pending.Add((Time.time + SpawnDelay, new Vector2(x + 0.5f, y)));
        }

        /// <summary>
        /// Moves a kinematic sentinel toward `to` at `speed` through its velocity (applied per physics step, whatever the frame
        /// rate). MovePosition from the Update loop crawled at high frame rates: the body position only changes at physics steps, so
        /// every Update re-aimed the same step (a sentinel 12 m away took minutes: the WardenPlayTests flake).
        /// </summary>
        static void Steer(Sentinel s, Vector2 pos, Vector2 to, float speed)
        {
            var off = to - pos;
            float dist = off.magnitude;
            if (dist < 1e-4f) { s.Body.linearVelocity = Vector2.zero; return; }
            float v = Mathf.Min(speed, dist / Time.fixedDeltaTime); // never overshoot the point within one step
            s.Body.linearVelocity = off / dist * v;
        }

        // ---- U-190: sentinels move through open air only ----

        /// <summary>Open air at p (the terrain's tile there is not solid; no terrain: everything is air).</summary>
        public bool Air(Vector2 p) => terrain == null || !TileId.IsSolid(terrain.GetTile(Mathf.FloorToInt(p.x), Mathf.FloorToInt(p.y)));

        /// <summary>Open air all along a → b (sampled every PathStep).</summary>
        public bool ClearPath(Vector2 a, Vector2 b)
        {
            var d = b - a;
            float len = d.magnitude;
            int n = Mathf.Max(1, Mathf.CeilToInt(len / PathStep));
            for (int i = 1; i <= n; i++) if (!Air(a + d * (i / (float)n))) return false;
            return true;
        }

        /// <summary>The open sky over column x: 3 m over the natural surface (or over `atLeast`), lifted past any overhang.</summary>
        Vector2 SkyOver(float x, float atLeast)
        {
            float y = Mathf.Max(terrain != null ? terrain.SurfaceAt(x) : atLeast, atLeast) + 3f;
            var p = new Vector2(x, y);
            for (int k = 0; k < 64 && !Air(p); k++) p.y += 1f;
            return p;
        }

        /// <summary>Where a hunting sentinel heads now: beside the surveyor when open air leads there; else to the open sky over the
        /// surveyor (a shaft's mouth), from where an open shaft leads down; else straight up to open air; else it holds.</summary>
        Vector2 HuntGoal(Sentinel s, Vector2 pos, Vector2 hold, Vector2 target)
        {
            if (ClearPath(pos, hold)) return hold;
            var mouth = SkyOver(target.x, pos.y);
            if (ClearPath(pos, mouth)) return mouth;
            var up = SkyOver(pos.x, pos.y);
            return ClearPath(pos, up) ? up : pos;
        }

        /// <summary>Steer, never into rock: a step whose end is solid is refused (the sentinel holds instead).</summary>
        void SteerInAir(Sentinel s, Vector2 pos, Vector2 to, float speed)
        {
            Steer(s, pos, to, speed);
            var next = pos + s.Body.linearVelocity * Time.fixedDeltaTime;
            if (!Air(next) && Air(pos)) { s.Body.linearVelocity = Vector2.zero; RockRefusals++; }
        }

        /// <summary>Takes a pooled sentinel; null when all MaxSentinels are out.</summary>
        public Sentinel Spawn(Vector2 at, Vector2 post, SentinelState state)
        {
            Build();
            foreach (var s in sentinels)
            {
                if (s.gameObject.activeSelf) continue;
                s.Begin(at, post, state);
                Active++;
                return s;
            }
            return null;
        }

        Vector2 PlayerCentre => player != null ? player.Body.position + new Vector2(0f, 0.9f) : Vector2.zero;

        void Update()
        {
            watch.Restart();
            if (sitesPending) PlaceSites();
            float dt = Time.deltaTime, now = Time.time;
            var target = PlayerCentre;

            for (int i = pending.Count - 1; i >= 0; i--)
            {
                if (pending[i].at > now) continue;
                var where = pending[i].where;
                pending.RemoveAt(i);
                // In from above the dig, on the far side from the surveyor.
                float side = where.x >= target.x ? 1f : -1f;
                var at = new Vector2(where.x + side * 6f, Mathf.Max(where.y, target.y) + 9f);
                if (!Air(at)) at = SkyOver(at.x, at.y); // U-190: called in the open sky, never inside rock
                Spawn(at, at, SentinelState.Hunt);
                foreach (var s in sentinels)
                    if (s.Alive && s.State == SentinelState.Patrol && (s.Post - where).sqrMagnitude <= AlertRadius * AlertRadius)
                        s.State = SentinelState.Hunt;
            }

            int active = 0;
            foreach (var s in sentinels)
            {
                if (!s.gameObject.activeSelf) continue;
                active++;
                Vector2 pos = s.Body.position;
                float face = 0f;
                if (s.State == SentinelState.Patrol)
                {
                    float tx = s.Post.x + s.sweep * Sentinel.PatrolHalfWidth;
                    if ((s.sweep > 0 && pos.x >= tx) || (s.sweep < 0 && pos.x <= tx)) s.sweep = -s.sweep;
                    var to = new Vector2(tx, s.Post.y + Mathf.Sin(now * 1.3f + s.Post.x) * 0.4f);
                    SteerInAir(s, pos, to, Sentinel.PatrolSpeed);
                    if (s.Body.linearVelocity == Vector2.zero && !Air(to)) s.sweep = -s.sweep; // a hill in the sweep: turn back
                    face = s.sweep;
                }
                else
                {
                    var off = target - pos;
                    if (off.sqrMagnitude > GiveUpDistance * GiveUpDistance) { s.State = SentinelState.Patrol; continue; }
                    // D-087: hover close beside the surveyor (2 m out, 1 m up) and ring the bell; walking into it bumps.
                    float side = pos.x >= target.x ? 1f : -1f;
                    var hold = target + new Vector2(side * 2f, 1f + Mathf.Sin(now * 2f + s.Post.x) * 0.3f);
                    if (!Air(hold)) hold = target + new Vector2(0f, 1.6f); // a narrow shaft: over the surveyor's head
                    // U-190: through open air only (re-planned every ReplanEvery; a refused step holds)
                    if (now >= s.replanAt)
                    {
                        s.replanAt = now + ReplanEvery * (0.8f + 0.4f * Mathf.Repeat(s.Post.x * 0.37f + s.Post.y * 0.11f, 1f)); // staggered: not all on one frame
                        s.goal = HuntGoal(s, pos, hold, target);
                        s.direct = s.goal == hold;
                    }
                    SteerInAir(s, pos, s.direct ? hold : s.goal, Sentinel.HuntSpeed);
                    face = off.x;
                    s.ringIn -= dt;
                    if (s.ringIn <= 0f && off.sqrMagnitude <= RingRange * RingRange) { s.ringIn = RingEvery; s.Play("attack"); }
                    if (player != null && now >= s.bumpReady && off.sqrMagnitude <= BumpRadius * BumpRadius)
                    {
                        s.bumpReady = now + BumpEvery;
                        player.Bump(pos);
                        Bumps++;
                    }
                }
                s.Animate(dt, face);
            }
            Active = active;
            watch.Stop();
            LastAiMs = (float)watch.Elapsed.TotalMilliseconds;
        }
    }
}
