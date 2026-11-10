using Meridian.FX;
using Meridian.Rendering;
using Meridian.Rig;
using Meridian.Terrain;
using UnityEngine;

namespace Meridian.Mining
{
    /// <summary>
    /// U-195 (D-183, the owner's 0.6.0 playtest): the stroke feels like something. On every stroke that opens ground: 4-8 clods thrown out
    /// of the cell at 3-4.5 m/s in the dug tier's tone under the planet's gravity, resting where they land and gone 0.6 s after the stroke (B-232's
    /// fx/dig_clods/t&lt;tier&gt;: 24 frames, four 6-frame clips clod_1..4, one clod tumbling in place per clip, the travel in code; until that
    /// sheet is exported a drawn stand-in of the same shape, one clod per sprite, tumbled by rotation); a one-frame 2 px camera kick along
    /// the stroke; a shovel scoop's clod-fall sound. When the pack takes a dug material its icon flies to the PACK readout (HudPackFlight),
    /// which ticks and bumps as it lands. All of it is drawn only: no body, no collider, nothing in physics; off while a transition runs.
    /// A fixed pool; nothing allocates per stroke or per frame.
    /// </summary>
    public sealed class DigFeel : MonoBehaviour
    {
        public const int MinClods = 4, MaxClods = 8, Pool = 48, Tiers = 5, ClipsPerSheet = 4;
        /// <summary>A clod's launch speed (m/s), its life (s), the fade at its end (s), the throw's half-angle about its axis (degrees).</summary>
        public const float SpeedMin = 3f, SpeedMax = 4.5f, ClodLife = 0.6f, ClodFade = 0.15f, SpreadDeg = 35f; // LEAD 17:0x: 3-4.5 m/s (it replaces the card's 2-4): every clod peaks 0.25-0.8 m over the line and is down by 0.6 s
        /// <summary>The camera kick (screen px, one frame) and the stand-in clods' tumble (degrees a second).</summary>
        public const float KickPixels = 2f, StandInSpinDeg = 540f;
        /// <summary>How far toward the open side a clod starts from the stroke's point (m: the bowl's mouth).</summary>
        public const float MouthM = 0.45f;
        /// <summary>D-190 (LEAD, from BLENDER's B-232 / B-238 sheet): the dig's debris is drawn once in cream and ink and coloured here by
        /// the dug cell's tone, lifted toward white so the art keeps its light side: clods 35 % on T1-T3 and 60 % on T4-T5 (the deep tiers'
        /// thin shards read weakly on their dark fills), the dust puff 60 %. The tone is the fill's drawn at the cell (D-190 (1): its
        /// json's "tone_hex"; Earth's sand puffs cream, Topsoil brown), the tier's depth-chip colour where a fill carries none.</summary>
        public const float ToneLiftShallow = 0.35f, ToneLiftDeep = 0.6f, PuffLift = 0.6f;
        public const int DeepLiftFromTier = 3;
        public static float ToneLiftOf(int tier) => tier >= DeepLiftFromTier ? ToneLiftDeep : ToneLiftShallow;

        /// <summary>B-238's puff (a low, small dust, drawn to be played at scale 1 and 0.85 alpha) is imported: set with its import. Until
        /// then B-184's lobed ball plays at 0.6 scale and 0.7 alpha (LEAD 17:0x) and the shovel's flick stays off (D-190 (4)).</summary>
        public static readonly bool PuffRedrawn = true; // B-238 imported (df2defa3): the dust at scale 1 and 0.85 alpha, the flick's crumbs back
        public static float PuffScaleNow => PuffRedrawn ? 1f : 0.6f;
        public static float PuffAlphaNow => PuffRedrawn ? 0.85f : 0.7f;

        // ---------- D-190 (1): the tone of the fill drawn at the dug cell ----------

        /// <summary>The key of the fill drawn at a cell: in the first tier the planet's ground_fill, or the band's own fill where the
        /// planet has one and the cell lies in that band (Earth's sand, Mars's basalt; the other bands lie over ground_fill);
        /// ground_fill_t2..t5 under it (0-based tier; past the last: the last). Pure.</summary>
        public static string FillKey(Meridian.Planets.PlanetId planet, int tier, bool bandFill)
        {
            string p = planet.ToString().ToLowerInvariant();
            int t = Mathf.Clamp(tier, 0, Tiers - 1);
            if (t >= 1) return $"terrain/{p}/ground_fill_t{t + 1}";
            string alt = bandFill ? Meridian.View2D.SmoothGround.AltFillKey(planet) : null;
            return $"terrain/{p}/{alt ?? "ground_fill"}";
        }

        static readonly System.Collections.Generic.Dictionary<int, Color> groundTones = new System.Collections.Generic.Dictionary<int, Color>(64);
        static int groundTonesOf = -2;

        /// <summary>The ground's own tone at a cell: the drawn fill's (its json's "tone_hex", BLENDER's db44edd1, in the ArtMaterials
        /// registry), else the tier's depth-chip colour (a fill without the field). Looked up once a fill; nothing allocates after.</summary>
        public static Color GroundTone(Meridian.Planets.PlanetId planet, int tier, bool bandFill)
        {
            var reg = ArtMaterials.Active;
            int count = reg != null && reg.tones != null ? reg.tones.Count : -1;
            if (count != groundTonesOf) { groundTones.Clear(); groundTonesOf = count; }
            int t = Mathf.Clamp(tier, 0, Tiers - 1);
            bool band = bandFill && t == 0 && Meridian.View2D.SmoothGround.AltFillKey(planet) != null;
            int id = ((int)planet * Tiers + t) * 2 + (band ? 1 : 0);
            if (groundTones.TryGetValue(id, out var c)) return c;
            if (!ArtMaterials.ToneFor(FillKey(planet, t, band), out c))
            {
                var tiers = D1Tables.Current.tiers;
                c = tiers.Length == 0 ? Color.white : tiers[Mathf.Clamp(t, 0, tiers.Length - 1)].ChipColor;
            }
            c.a = 1f;
            groundTones[id] = c;
            return c;
        }

        /// <summary>The tone a cell's clods (and the shovel's crumbs) are multiplied by: the ground's tone there lifted toward white.</summary>
        public static Color Tone(Meridian.Planets.PlanetId planet, int tier, bool bandFill)
        {
            var c = Color.Lerp(GroundTone(planet, tier, bandFill), Color.white, ToneLiftOf(tier));
            c.a = 1f;
            return c;
        }
        /// <summary>The dust puff's tint at a cell: the ground's tone there lifted PuffLift, at the puff's alpha.</summary>
        public static Color PuffTone(Meridian.Planets.PlanetId planet, int tier, bool bandFill)
        {
            var c = Color.Lerp(GroundTone(planet, tier, bandFill), Color.white, PuffLift);
            c.a = PuffAlphaNow;
            return c;
        }

        /// <summary>At a point of a planet side: the planet from its terrain, the band's fill from the ground drawn at that x.</summary>
        public static Color ToneAt(TerrainStreamer t, Vector2 at, int tier) => Tone(PlanetOf(t), tier, BandFillAt(at.x));
        public static Color PuffToneAt(TerrainStreamer t, Vector2 at, int tier) => PuffTone(PlanetOf(t), tier, BandFillAt(at.x));
        static Meridian.Planets.PlanetId PlanetOf(TerrainStreamer t) => t != null && t.Config != null ? t.Config.id : Meridian.Planets.PlanetId.Earth;
        /// <summary>The cell's column draws the band's own fill (the smooth ground of the planet side that is up).</summary>
        public static bool BandFillAt(float x)
        {
            var g = Meridian.View2D.SmoothGround.Current;
            return g != null && g.BandFillAt(x);
        }
        public const int SortingOrder = 41; // over the stroke's puff (FxPool, 40)

        public Meridian.Core.PlanetSideRoot side;

        /// <summary>Clods for a stroke that opened `cells` cells: 4 for one, two more per further cell, 8 at most.</summary>
        public static int ClodsFor(int cells) => Mathf.Clamp(MinClods + 2 * (cells - 1), MinClods, MaxClods);
        /// <summary>B-232's sheet for a depth tier (0-based, D1Tables' order).</summary>
        public static string ClodsKey(int tier) => TierKeys[Mathf.Clamp(tier, 0, Tiers - 1)];
        static readonly string[] TierKeys = { "fx/dig_clods/t1", "fx/dig_clods/t2", "fx/dig_clods/t3", "fx/dig_clods/t4", "fx/dig_clods/t5" };

        /// <summary>Clods drawn now (this planet's; every planet's for the budget's particle count).</summary>
        public int Alive { get; private set; }
        public static int TotalAlive { get; private set; }
        /// <summary>Tests: the bursts since load, the last one's clods, whether it drew B-232's sheet (false: the stand-in), the last kick's
        /// direction, the material flights started.</summary>
        public int Bursts { get; private set; }
        public int LastBurst { get; private set; }
        public bool LastBurstOnSheet { get; private set; }
        public Vector2 LastKick { get; private set; }
        public int Flights { get; private set; }

        readonly SpriteRenderer[] views = new SpriteRenderer[Pool];
        readonly Vector2[] pos = new Vector2[Pool], vel = new Vector2[Pool];
        readonly float[] born = new float[Pool], spin = new float[Pool], angle = new float[Pool];
        readonly bool[] alive = new bool[Pool], landed = new bool[Pool];
        readonly FxSheet[] sheetOf = new FxSheet[Pool];
        readonly int[] clipStart = new int[Pool], clipLength = new int[Pool], shown = new int[Pool];
        readonly Color[] tintOf = new Color[Pool];

        RigTools rig;
        ItemDrops drops;
        Meridian.Player.CameraFollow follow;
        Meridian.UI.HudPackFlight flight;
        Meridian.Transitions.TransitionDirector director;
        float directorSearchAt;
        bool hooked;

        void Awake()
        {
            for (int i = 0; i < Pool; i++)
            {
                var go = new GameObject("Clod" + i);
                go.transform.SetParent(transform, false);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sortingOrder = SortingOrder;
                sr.enabled = false;
                views[i] = sr;
            }
        }

        void Hook()
        {
            if (hooked || side == null || side.rig == null) return;
            hooked = true;
            rig = side.rig;
            rig.Dug += OnDug;
            drops = rig.drops;
            if (drops != null) drops.PickedUpAt += OnPicked;
            for (int t = 0; t < Tiers; t++) FxSheet.Get(TierKeys[t]); // asked now: the first stroke finds B-232's sheets ready (or known absent)
        }

        void OnDestroy()
        {
            if (rig != null) rig.Dug -= OnDug;
            if (drops != null) drops.PickedUpAt -= OnPicked;
            if (flight != null) flight.Arrived -= OnArrived;
            TotalAlive -= Alive;
            Alive = 0;
        }

        /// <summary>A climb or an entry runs: nothing new starts (the clods in the air finish).</summary>
        bool Busy
        {
            get
            {
                if (director == null && Time.unscaledTime >= directorSearchAt)
                {
                    director = FindAnyObjectByType<Meridian.Transitions.TransitionDirector>();
                    directorSearchAt = Time.unscaledTime + 1f;
                }
                return director != null && director.Busy;
            }
        }

        void OnDug(Vector2 at)
        {
            if (!isActiveAndEnabled || Busy) return;
            int cells = rig.LastDugCells;
            if (cells <= 0) return; // a base piece came down or a node was cut: no ground opened
            var t = rig.terrain;
            int tier = t != null && rig.D1 ? DigRun.TierAt(t, at) : 0;
            Vector2 hand = rig.owner != null ? (Vector2)rig.owner.position + new Vector2(0f, 0.9f) : at + Vector2.up;
            Burst(at, hand, ClodsFor(cells), tier, ToneAt(t, at, tier));
            if (follow == null && side.sideCamera != null) follow = side.sideCamera.GetComponent<Meridian.Player.CameraFollow>();
            var stroke = at - hand;
            if (follow != null && stroke.sqrMagnitude > 1e-6f) { follow.Kick(stroke, KickPixels); LastKick = stroke.normalized; }
            var audio = Meridian.Audio.AudioDirector.Instance;
            if (audio != null && rig.Tool == DigTool.Shovel) audio.Play(Meridian.Audio.Sfx.ClodFall, 0.7f);
        }

        /// <summary>Throws `count` clods out of the cell at `at`: about the axis from the cell back toward the hand and up (the open side),
        /// within SpreadDeg of it, each at SpeedMin..SpeedMax. Tests call it directly.</summary>
        public void Burst(Vector2 at, Vector2 hand, int count, int tier, Color tint)
        {
            var sheet = FxSheet.Get(ClodsKey(tier));
            bool onSheet = sheet.Ready && sheet.frames.Length >= ClipsPerSheet;
            var clips = onSheet ? ArtMaterials.ClipsFor(sheet.key) : null;
            Vector2 back = hand - at;
            Vector2 axis = ((back.sqrMagnitude > 1e-6f ? back.normalized : Vector2.zero) + Vector2.up * 1.2f).normalized;
            float axisDeg = Mathf.Atan2(axis.y, axis.x) * Mathf.Rad2Deg;
            float now = Time.time;
            for (int n = 0; n < count; n++)
            {
                int i = Take();
                float a = (axisDeg + Random.Range(-SpreadDeg, SpreadDeg)) * Mathf.Deg2Rad;
                float speed = Random.Range(SpeedMin, SpeedMax);
                // from the cell's mouth, not its middle: 2-4 m/s clears 0.2-0.8 m, and thrown from the bowl's centre (u195's first captures)
                // the burst stayed in the hole as one clump
                pos[i] = at + axis * MouthM + new Vector2(Random.Range(-0.2f, 0.2f), Random.Range(-0.08f, 0.12f));
                vel[i] = new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * speed;
                born[i] = now;
                landed[i] = false;
                shown[i] = -1;
                tintOf[i] = tint;
                int clip = Random.Range(0, ClipsPerSheet);
                var sr = views[i];
                if (onSheet)
                {
                    sheetOf[i] = sheet;
                    if (clips != null && clip < clips.clips.Count && clips.clips[clip].length > 0) { clipStart[i] = clips.clips[clip].start; clipLength[i] = clips.clips[clip].length; }
                    else { clipLength[i] = Mathf.Max(1, sheet.frames.Length / ClipsPerSheet); clipStart[i] = clip * clipLength[i]; }
                    if (sheet.material != null) sr.sharedMaterial = sheet.material;
                    sr.transform.localScale = Vector3.one;
                    spin[i] = 0f; angle[i] = 0f; // the sheet's frames tumble
                }
                else
                {
                    sheetOf[i] = null;
                    sr.sprite = StandIn(clip);
                    sr.transform.localScale = Vector3.one; // drawn at B-232's size (13-20 px at 64 px a metre): the swap to the sheet changes nothing
                    if (standInMaterial == null) standInMaterial = ArtMaterials.MaterialFor(Meridian.Art.ArtKeys.Fx.ShovelFlick); // lit as the shovel's flick is
                    if (standInMaterial != null) sr.sharedMaterial = standInMaterial;
                    spin[i] = Random.Range(-StandInSpinDeg, StandInSpinDeg);
                    angle[i] = Random.Range(0f, 360f);
                }
                sr.color = tint;
                sr.transform.SetPositionAndRotation(new Vector3(pos[i].x, pos[i].y, 0f), Quaternion.Euler(0f, 0f, angle[i]));
                sr.enabled = true;
            }
            Bursts++;
            LastBurst = count;
            LastBurstOnSheet = onSheet;
        }

        /// <summary>Tests: clod `i`'s place, velocity and whether it has landed (false when the slot is free).</summary>
        public bool Clod(int i, out Vector2 position, out Vector2 velocity, out bool resting)
        {
            position = velocity = default; resting = false;
            if (i < 0 || i >= Pool || !alive[i]) return false;
            position = pos[i]; velocity = vel[i]; resting = landed[i];
            return true;
        }

        /// <summary>Tests: the tint clod `i` was thrown with (clear when the slot is free).</summary>
        public Color TintOf(int i) => i >= 0 && i < Pool && alive[i] ? tintOf[i] : Color.clear;

        /// <summary>A free slot, else the oldest clod's.</summary>
        int Take()
        {
            int pick = 0;
            float oldest = float.MaxValue;
            for (int i = 0; i < Pool; i++)
            {
                if (!alive[i]) { alive[i] = true; Alive++; TotalAlive++; return i; }
                if (born[i] < oldest) { oldest = born[i]; pick = i; }
            }
            return pick;
        }

        void Free(int i)
        {
            alive[i] = false;
            views[i].enabled = false;
            sheetOf[i] = null;
            Alive--; TotalAlive--;
        }

        void OnPicked(int itemId, Vector2 at)
        {
            if (!isActiveAndEnabled || Busy || side == null || side.sideHud == null || side.sideCamera == null) return;
            if (flight == null)
            {
                flight = side.sideHud.PackFlight;
                if (flight == null) return;
                flight.Arrived += OnArrived;
            }
            var icon = Meridian.UI.ItemIcons.Get(itemId, rig != null ? rig.terrain : null);
            if (icon == null || !flight.Fly(icon, side.sideCamera.WorldToScreenPoint(new Vector3(at.x, at.y, 0f)))) { OnArrived(); side.sideHud.BumpPack(); return; } // no icon yet: the tick and the bump alone
            Flights++;
        }

        void OnArrived()
        {
            var audio = Meridian.Audio.AudioDirector.Instance;
            if (audio != null) audio.Play(Meridian.Audio.Sfx.PackTick, 0.8f);
        }

        void Update()
        {
            Hook();
            if (Alive == 0) return;
            float now = Time.time, dt = Time.deltaTime;
            float g = Physics2D.gravity.y < -0.01f ? Physics2D.gravity.y : -9.81f;
            var t = rig != null ? rig.terrain : null;
            for (int i = 0; i < Pool; i++)
            {
                if (!alive[i]) continue;
                float age = now - born[i];
                if (age >= ClodLife) { Free(i); continue; }
                var sr = views[i];
                if (!landed[i])
                {
                    vel[i].y += g * dt;
                    pos[i] += vel[i] * dt;
                    angle[i] += spin[i] * dt;
                    // it lands where it meets the ground again (a few tile reads, falling clods only) and rests there until it goes
                    if (vel[i].y < 0f && age > 0.08f && t != null && Solid(t, pos[i])) landed[i] = true;
                    sr.transform.SetPositionAndRotation(new Vector3(pos[i].x, pos[i].y, 0f), Quaternion.Euler(0f, 0f, angle[i]));
                }
                var sheet = sheetOf[i];
                if (sheet != null && sheet.Ready)
                {
                    int f = clipStart[i] + (landed[i] ? clipLength[i] - 1 : (int)(age * sheet.fps) % clipLength[i]);
                    if (f >= sheet.frames.Length) f = sheet.frames.Length - 1;
                    if (f != shown[i]) { shown[i] = f; sr.sprite = sheet.frames[f]; }
                }
                float left = ClodLife - age;
                if (left < ClodFade) { var c = tintOf[i]; c.a *= left / ClodFade; sr.color = c; }
            }
        }

        /// <summary>The point is in the ground: inside the drawn outline on a smooth planet, a solid tile on a block one.</summary>
        static bool Solid(TerrainStreamer t, Vector2 p) =>
            t.SmoothGround ? SolidRescue.Inside(t, p) : TileId.IsSolid(t.GetTile(Mathf.FloorToInt(p.x), Mathf.FloorToInt(p.y)));

        // ---------- the stand-in until B-232's sheets are exported: four clods, one a sprite, cream with an ink edge (tinted per ground) ----------

        static Sprite[] standIns;
        Material standInMaterial;

        /// <summary>The stand-in's clod `n` (0..3), drawn once: a lumpy cream blob with an ink rim, 64 px at 64 px a metre, pivot centre: the
        /// shape of one frame of B-232's sheet, so the swap is the sheet turning Ready.</summary>
        public static Sprite StandIn(int n)
        {
            if (standIns == null)
            {
                const int N = 64;
                var tex = new Texture2D(N * ClipsPerSheet, N, TextureFormat.RGBA32, false) { name = "DigClodStandIn", wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear };
                var px = new Color32[N * ClipsPerSheet * N];
                var cream = new Color32(238, 224, 196, 255);
                var ink = new Color32(38, 30, 26, 255);
                for (int c = 0; c < ClipsPerSheet; c++)
                {
                    float r0 = 6.5f + 1.17f * c, lobes = 3 + c, phase = 0.9f * c; // four sizes and outlines: 13-20 px across, B-232's clods (0.2-0.3 m)
                    for (int y = 0; y < N; y++)
                        for (int x = 0; x < N; x++)
                        {
                            float dx = x + 0.5f - N * 0.5f, dy = y + 0.5f - N * 0.5f;
                            float d = Mathf.Sqrt(dx * dx + dy * dy), th = Mathf.Atan2(dy, dx);
                            float r = r0 * (1f + 0.16f * Mathf.Sin(lobes * th + phase) + 0.07f * Mathf.Sin((lobes + 2f) * th - phase));
                            float edge = r - d; // > 0 inside
                            Color32 col = default;
                            if (edge > 1.7f) col = cream;
                            else if (edge > 0f) col = ink;
                            else if (edge > -1f) col = new Color32(ink.r, ink.g, ink.b, (byte)(255f * (1f + edge)));
                            px[y * N * ClipsPerSheet + c * N + x] = col;
                        }
                }
                tex.SetPixels32(px);
                tex.Apply(false, true);
                standIns = new Sprite[ClipsPerSheet];
                for (int c = 0; c < ClipsPerSheet; c++)
                {
                    standIns[c] = Sprite.Create(tex, new Rect(c * N, 0, N, N), new Vector2(0.5f, 0.5f), N);
                    standIns[c].name = "dig_clod_standin_" + c;
                }
            }
            return standIns[Mathf.Clamp(n, 0, ClipsPerSheet - 1)];
        }
    }
}
