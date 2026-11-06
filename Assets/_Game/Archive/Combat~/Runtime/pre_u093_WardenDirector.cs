using System.Collections.Generic;
using Meridian.Art;
using Meridian.FX;
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
    /// and wakes the patrols nearby. Hunting sentinels hold a firing point beside the surveyor and fire
    /// fx/warden_bolt bolts that come off the suit first (HazardSystem.DamageSuit). Everything is pooled:
    /// MaxSentinels bodies, BoltPool bolts, no allocation per frame. Lives on the PlanetSide root.
    /// </summary>
    public sealed class WardenDirector : MonoBehaviour
    {
        public const int MaxSentinels = 6, BoltPool = 12;
        public const float SpawnDelay = 2.5f, AlertRadius = 60f, GiveUpDistance = 70f, FireRange = 14f, FireEvery = 1.6f;
        public const float BoltSpeed = 14f, BoltDamage = 10f, BoltRange = 24f, BoltHitRadius = 0.7f;
        static readonly string[] SiteIds = { "warden_vault", "warden_outpost" };

        public TerrainStreamer terrain;
        public PlayerController player;
        public HazardSystem hazards;
        public PoiPlacer pois;

        public readonly WardenMeter meter = new WardenMeter();
        public readonly List<Sentinel> sentinels = new List<Sentinel>(MaxSentinels);
        /// <summary>Time spent in the last Update (ms): the AI budget (≤ 0.3 ms with six sentinels).</summary>
        public float LastAiMs { get; private set; }
        public int Active { get; private set; }
        public int BoltsLive { get; private set; }
        public int Trips { get; private set; }

        sealed class Bolt { public SpriteRenderer view; public Vector2 pos, dir; public float travelled, age; public bool live, reflected; }
        readonly List<Bolt> bolts = new List<Bolt>(BoltPool);
        readonly List<(float at, Vector2 where)> pending = new List<(float, Vector2)>(4);
        readonly System.Diagnostics.Stopwatch watch = new System.Diagnostics.Stopwatch();
        FxSheet boltSheet;
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
            for (int i = 0; i < BoltPool; i++)
            {
                var go = new GameObject("WardenBolt" + i);
                go.transform.SetParent(transform, false);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sortingOrder = 7;
                go.SetActive(false);
                bolts.Add(new Bolt { view = sr });
            }
            boltSheet = FxSheet.Get(ArtKeys.Fx.WardenBolt);
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
            foreach (var b in bolts) if (b.live) Retire(b);
            Active = 0;
        }

        /// <summary>Places a patrol at each Warden site once the POIs are placed.</summary>
        void PlaceSites()
        {
            if (pois == null || pois.placed.Count == 0) return;
            sitesPending = false;
            foreach (var p in pois.placed)
            {
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
                if (s.State == SentinelState.Dying)
                {
                    s.dyingFor += dt;
                    s.Body.MovePosition(pos + Vector2.down * 1.5f * dt);
                    if (s.dyingFor >= Sentinel.DeathSeconds) { s.gameObject.SetActive(false); active--; continue; }
                }
                else if (s.State == SentinelState.Patrol)
                {
                    float tx = s.Post.x + s.sweep * Sentinel.PatrolHalfWidth;
                    if ((s.sweep > 0 && pos.x >= tx) || (s.sweep < 0 && pos.x <= tx)) s.sweep = -s.sweep;
                    var to = new Vector2(tx, s.Post.y + Mathf.Sin(now * 1.3f + s.Post.x) * 0.4f);
                    s.Body.MovePosition(Vector2.MoveTowards(pos, to, Sentinel.PatrolSpeed * dt));
                    face = s.sweep;
                }
                else
                {
                    var off = target - pos;
                    if (off.sqrMagnitude > GiveUpDistance * GiveUpDistance) { s.State = SentinelState.Patrol; continue; }
                    float side = pos.x >= target.x ? 1f : -1f;
                    var hold = target + new Vector2(side * 5f, 4f + Mathf.Sin(now * 2f + s.Post.x) * 0.5f);
                    s.Body.MovePosition(Vector2.MoveTowards(pos, hold, Sentinel.HuntSpeed * dt));
                    face = off.x;
                    s.fireIn -= dt;
                    if (s.fireIn <= 0f && off.sqrMagnitude <= FireRange * FireRange)
                    {
                        s.fireIn = FireEvery;
                        if (Fire(pos, off)) s.Play("attack");
                    }
                }
                s.Animate(dt, face);
            }
            Active = active;
            StepBolts(dt, target);
            watch.Stop();
            LastAiMs = (float)watch.Elapsed.TotalMilliseconds;
        }

        /// <summary>Tests: bolt slot `i` (position, direction, reflected); false for a free or missing slot.</summary>
        public bool TryGetBolt(int i, out Vector2 pos, out Vector2 dir, out bool reflected)
        {
            pos = dir = Vector2.zero; reflected = false;
            if (i < 0 || i >= bolts.Count || !bolts[i].live) return false;
            pos = bolts[i].pos; dir = bolts[i].dir; reflected = bolts[i].reflected;
            return true;
        }

        public bool Fire(Vector2 from, Vector2 direction)
        {
            if (direction.sqrMagnitude < 1e-6f) return false;
            foreach (var b in bolts)
            {
                if (b.live) continue;
                b.live = true;
                b.pos = from;
                b.dir = direction.normalized;
                b.travelled = 0f;
                b.age = 0f;
                b.reflected = false;
                b.view.transform.SetPositionAndRotation(from, Quaternion.Euler(0f, 0f, Mathf.Atan2(b.dir.y, b.dir.x) * Mathf.Rad2Deg));
                if (boltSheet != null && boltSheet.Ready)
                {
                    b.view.sprite = boltSheet.frames[0];
                    if (boltSheet.material != null) b.view.sharedMaterial = boltSheet.material;
                }
                b.view.gameObject.SetActive(true);
                BoltsLive++;
                return true;
            }
            return false;
        }

        void StepBolts(float dt, Vector2 target)
        {
            float step = BoltSpeed * dt;
            foreach (var b in bolts)
            {
                if (!b.live) continue;
                b.age += dt;
                b.pos += b.dir * step;
                b.travelled += step;
                bool stop = b.travelled >= BoltRange;
                if (!stop && !b.reflected && player != null && (b.pos - target).sqrMagnitude <= BoltHitRadius * BoltHitRadius)
                {
                    // U-088: a parried bolt flies back along the aim (the facing when there is no aim) and never hits the player again.
                    if (player.TryParryAttack(b.pos))
                    {
                        var aim = player.Aim.sqrMagnitude > 1e-4f ? player.Aim.normalized : new Vector2(player.Facing, 0f);
                        b.dir = aim;
                        b.reflected = true;
                        b.travelled = 0f;
                        b.view.transform.rotation = Quaternion.Euler(0f, 0f, Mathf.Atan2(aim.y, aim.x) * Mathf.Rad2Deg);
                    }
                    else
                    {
                        player.Knock(b.pos); // U-089
                        if (hazards != null) hazards.DamageSuit(BoltDamage);
                        stop = true;
                    }
                }
                if (!stop && terrain != null && TileId.IsSolid(terrain.GetTile(Mathf.FloorToInt(b.pos.x), Mathf.FloorToInt(b.pos.y)))) stop = true;
                if (stop) { Retire(b); continue; }
                b.view.transform.position = b.pos;
                if (boltSheet != null && boltSheet.Ready)
                {
                    int f = boltSheet.FrameAt(b.age);
                    if (f >= 0) b.view.sprite = boltSheet.frames[f];
                }
            }
        }

        void Retire(Bolt b)
        {
            b.live = false;
            b.view.gameObject.SetActive(false);
            BoltsLive--;
        }
    }
}
