using System;
using System.Collections.Generic;
using Meridian.Art;
using Meridian.Core;
using Meridian.Planet.Lighting;
using Meridian.Planets;
using Meridian.Space;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Planet.Weather
{
    /// <summary>
    /// U-026 Mars dust storm (Bible §7.2) on PlanetSide: follows DustStormSchedule (or a forced storm),
    /// raises Warning 60 s ahead, then Started/Ended; while it blows, a dust fog limits visibility to
    /// 15 m around the player, fx/dust puffs stream past (when the art exists), daylight dims, Cryo is +1
    /// and static discharges flash. Phase and intensity come from the game clock (8 s ramps), so tests
    /// can step the clock. No allocation per frame.
    /// </summary>
    public sealed class DustStorm : MonoBehaviour
    {
        public const float StormVisibility = 15f;
        public const float ClearVisibility = 60f;
        public const float RampRealSeconds = 8f;
        public const float WindSpeed = 16f;
        const int PuffCount = 20;

        public TimeSystem time;
        public Camera view;
        public Transform focus;
        public DayNightLighting dayNight;
        public Material fogMaterial;

        public event Action Warning, Started, Ended;
        public event Action<Vector2> Discharge;

        public bool OnMars { get; private set; }
        public StormPhase Phase { get; private set; }
        /// <summary>0 clear … 1 full storm.</summary>
        public float Intensity { get; private set; }
        /// <summary>How far the player can see, in metres (15 in a full storm).</summary>
        public float Visibility => Mathf.Lerp(ClearVisibility, StormVisibility, Intensity);
        /// <summary>Added to the Cryo level while a storm blows (Bible: Cryo +1).</summary>
        public int CryoBonus => OnMars && Phase == StormPhase.Storm ? 1 : 0;
        public DustStormSchedule.Storm Current => storm;
        public int Discharges { get; private set; }
        public bool PuffsLoaded => frames != null;

        int seed;
        double day;
        DustStormSchedule.Storm storm, forced;
        bool hasForced;
        int warnedIndex = int.MinValue, lastPhaseIndex = int.MinValue;
        StormPhase lastPhase;
        float nextDischarge, flash;

        MeshRenderer fog;
        MaterialPropertyBlock block;
        readonly SpriteRenderer[] puffs = new SpriteRenderer[PuffCount];
        readonly Vector2[] puffOffset = new Vector2[PuffCount];
        Sprite[] frames;
        AsyncOperationHandle<IList<Sprite>> handle;

        static readonly int CenterId = Shader.PropertyToID("_Center");
        static readonly int VisibilityId = Shader.PropertyToID("_Visibility");
        static readonly int IntensityId = Shader.PropertyToID("_Intensity");
        static readonly int ColorId = Shader.PropertyToID("_DustColor");
        static readonly int FlashId = Shader.PropertyToID("_Flash");
        static readonly Color DustColor = new Color(0.72f, 0.5f, 0.33f);

        void Awake()
        {
            block = new MaterialPropertyBlock();
            if (view == null) return;
            var go = new GameObject("DustFog");
            go.transform.SetParent(view.transform, false);
            go.transform.localPosition = new Vector3(0f, 0f, 1f);
            go.AddComponent<MeshFilter>().sharedMesh = SpaceWorld.Quad();
            fog = go.AddComponent<MeshRenderer>();
            fog.sharedMaterial = fogMaterial;
            fog.sortingOrder = 500; // over terrain, player and ship; HUD canvases are overlays above
            fog.enabled = false;
        }

        void OnEnable() => RenderWarmup.Warming += OnWarming;
        void OnDisable() => RenderWarmup.Warming -= OnWarming;

        /// <summary>The fog joins the load warm-up render (U-028) so the first storm frame doesn't compile its shader.</summary>
        void OnWarming(Camera cam, bool on)
        {
            if (fog == null || cam != view) return;
            if (on)
            {
                fog.GetPropertyBlock(block);
                block.SetFloat(IntensityId, 0.001f);
                fog.SetPropertyBlock(block);
                fog.enabled = true;
            }
            else fog.enabled = OnMars && Intensity > 0f;
        }

        void Start()
        {
            handle = Addressables.LoadAssetAsync<IList<Sprite>>(ArtKeys.Fx.Dust);
            handle.Completed += op =>
            {
                if (this == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                var list = new Sprite[op.Result.Count];
                foreach (var s in op.Result)
                {
                    int u = s.name.LastIndexOf('_');
                    if (u >= 0 && int.TryParse(s.name.Substring(u + 1), out int n) && n < list.Length) list[n] = s;
                }
                for (int i = 0; i < list.Length; i++) if (list[i] == null) list[i] = op.Result[0];
                frames = list;
                BuildPuffs();
            };
        }

        public void ConfigureFor(PlanetConfig planet, int worldSeed)
        {
            OnMars = planet != null && planet.id == PlanetId.Mars;
            seed = worldSeed;
            day = planet != null ? planet.dayLengthRealMinutes * 60.0 * TimeSystem.GameSecondsPerRealSecond : 0;
            storm = default;
            hasForced = false;
            Intensity = 0f;
            Phase = StormPhase.Clear;
            lastPhase = StormPhase.Clear;
            Apply();
        }

        /// <summary>Tests and debugging: a storm whose warning starts now, `leadRealSeconds` before it blows.</summary>
        public void Force(float leadRealSeconds, float durationRealSeconds)
        {
            if (time == null) time = FindAnyObjectByType<TimeSystem>();
            double now = time.GameSeconds, g = TimeSystem.GameSecondsPerRealSecond;
            double start = now + leadRealSeconds * g;
            forced = new DustStormSchedule.Storm(-1 - Discharges, now, start, start + durationRealSeconds * g);
            hasForced = true;
        }

        void Update()
        {
            if (!OnMars || day <= 0) return;
            if (time == null) time = FindAnyObjectByType<TimeSystem>();
            if (time == null) return;
            double now = time.GameSeconds;

            if (hasForced && now >= forced.end) hasForced = false;
            storm = hasForced ? forced : DustStormSchedule.Current(seed, now, day, storm);
            var phase = DustStormSchedule.PhaseAt(storm, now);

            if (phase == StormPhase.Warning && warnedIndex != storm.index) { warnedIndex = storm.index; Warning?.Invoke(); }
            if (phase != lastPhase || storm.index != lastPhaseIndex)
            {
                if (phase == StormPhase.Storm) Started?.Invoke();
                else if (lastPhase == StormPhase.Storm) Ended?.Invoke();
                lastPhase = phase;
                lastPhaseIndex = storm.index;
            }
            Phase = phase;

            double ramp = RampRealSeconds * TimeSystem.GameSecondsPerRealSecond;
            Intensity = phase == StormPhase.Storm
                ? (float)Math.Min(Math.Min((now - storm.start) / ramp, (storm.end - now) / ramp), 1.0)
                : 0f;

            // Static discharges: one every 2–7 s while the storm is well under way.
            if (Intensity > 0.5f)
            {
                nextDischarge -= Time.deltaTime;
                if (nextDischarge <= 0f)
                {
                    Discharges++;
                    nextDischarge = 2f + 5f * (float)DustStormSchedule.Hash01(seed, Discharges, 7);
                    flash = 1f;
                    var c = focus != null ? (Vector2)focus.position : Vector2.zero;
                    float dx = -12f + 24f * (float)DustStormSchedule.Hash01(seed, Discharges, 8);
                    Discharge?.Invoke(new Vector2(c.x + dx, c.y + 3f));
                }
            }
            flash = Mathf.Max(0f, flash - Time.deltaTime / 0.15f);
        }

        void LateUpdate() => Apply();

        void Apply()
        {
            float k = OnMars ? Intensity : 0f;
            if (dayNight != null) { dayNight.StormDim = k; dayNight.Flash = flash * k; }
            var tint = dayNight != null ? dayNight.SkyTint : Color.white;

            if (fog != null)
            {
                bool on = k > 0f;
                if (fog.enabled != on) fog.enabled = on;
                if (on && view != null)
                {
                    float h = view.orthographicSize * 2f, w = h * Mathf.Max(view.aspect, 2.5f);
                    fog.transform.localScale = new Vector3(w, h, 1f);
                    var c = focus != null ? focus.position : view.transform.position;
                    fog.GetPropertyBlock(block);
                    block.SetVector(CenterId, new Vector4(c.x, c.y + 0.9f, 0f, 0f));
                    block.SetFloat(VisibilityId, Visibility);
                    block.SetFloat(IntensityId, k);
                    block.SetFloat(FlashId, flash);
                    block.SetColor(ColorId, new Color(DustColor.r * tint.r, DustColor.g * tint.g, DustColor.b * tint.b, 1f));
                    fog.SetPropertyBlock(block);
                }
            }
            UpdatePuffs(k, tint);
        }

        void BuildPuffs()
        {
            if (view == null) return;
            for (int i = 0; i < PuffCount; i++)
            {
                var go = new GameObject("DustPuff" + i);
                go.transform.SetParent(transform, false);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sortingOrder = 510; // over the fog: the nearest dust streams past the player
                sr.enabled = false;
                puffs[i] = sr;
                puffOffset[i] = new Vector2(
                    -20f + 40f * (float)DustStormSchedule.Hash01(1, i, 3),
                    -6f + 12f * (float)DustStormSchedule.Hash01(1, i, 4));
            }
        }

        void UpdatePuffs(float k, Color tint)
        {
            if (frames == null || puffs[0] == null || view == null) return;
            bool on = k > 0f;
            var cam = view.transform.position;
            float t = Time.time;
            for (int i = 0; i < PuffCount; i++)
            {
                var sr = puffs[i];
                if (sr.enabled != on) sr.enabled = on;
                if (!on) continue;
                // Puffs stream right-to-left across a 40 m band around the view and wrap.
                float x = Mathf.Repeat(puffOffset[i].x - t * WindSpeed * (0.8f + 0.4f * (i % 3) / 2f) + 20f, 40f) - 20f;
                float y = puffOffset[i].y + Mathf.Sin(t * 1.3f + i) * 0.6f;
                sr.transform.position = new Vector3(cam.x + x, cam.y + y, 0f);
                float s = 3f + (i % 4);
                sr.transform.localScale = new Vector3(s, s, 1f);
                sr.sprite = frames[(int)(t * 12f + i) % frames.Length];
                sr.color = new Color(0.85f * tint.r, 0.62f * tint.g, 0.45f * tint.b, 0.75f * k);
            }
        }

        void OnDestroy()
        {
            if (handle.IsValid()) Addressables.Release(handle);
        }
    }
}
