using System.Collections.Generic;
using Meridian.Art;
using Meridian.Rendering;
using UnityEngine;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Space
{
    /// <summary>
    /// U-116 (D-123, B-137): the painted Sun as a rig. `planets/sun/disc_rig` is one sheet of five named parts (body, tongue,
    /// prominence_a, prominence_b, corona) sliced by the importer; its json says how Unity draws them: every part at draw_scale over
    /// space_ppu (the 928 px body spans 2 × R and its flame bases), the tongue instanced `ring.count` times round the rim at base_r R
    /// (alternating alt_scale, a slow spin, a ± pulse on the beat, stepped at 12 Hz), each prominence on the rim at its angle with a slow
    /// wobble, the corona wash at radius_r R breathing. Replaces the lit spheroid where the sheet exists (SpaceWorld.ProbeSunRig); the
    /// glow, the Space light and the planet discs are untouched. Unlit: the Sun is the light.
    /// </summary>
    public sealed class SunView : MonoBehaviour
    {
        public const string Key = "planets/sun/disc_rig";

        [System.Serializable] public sealed class Ring { public int count = 14; public float[] alt_scale; public float base_r = 0.97f, spin_deg_per_s = 2f, pulse = 0.08f, beat_bpm = 110f, stepped_hz = 12f; public string part = "tongue"; }
        [System.Serializable] public sealed class Corona { public string part = "corona"; public float radius_r = 1.42f, breathe = 0.03f; }
        [System.Serializable] public sealed class Prominence { public string part; public float angle_deg; }
        [System.Serializable]
        public sealed class Rig
        {
            public string key;
            public float space_ppu = 3f, export_scale = 0.5f, draw_scale = 2f;
            public Meridian.Flora.RigSet.Part[] parts;
            public Ring ring;
            public Corona corona;
            public Prominence[] prominences;
        }

        /// <summary>The json with its defaults filled (a missing ring or corona object, an empty alt_scale). Pure.</summary>
        public static Rig Parse(string json)
        {
            var r = JsonUtility.FromJson<Rig>(json);
            if (r == null) return null;
            if (r.ring == null) r.ring = new Ring();
            if (r.corona == null) r.corona = new Corona();
            if (r.ring.alt_scale == null || r.ring.alt_scale.Length == 0) r.ring.alt_scale = new[] { 1f, 0.62f };
            if (r.prominences == null) r.prominences = new Prominence[0];
            return r;
        }

        // ---------- pure ----------

        /// <summary>Transform scale for a part sprite imported at `ppu`, so one sheet pixel draws draw_scale / space_ppu units. Pure.</summary>
        public static float PartScale(Rig r, float ppu) => r.draw_scale / Mathf.Max(0.01f, r.space_ppu) * ppu;
        /// <summary>The corona's transform scale: its wash spans 2 × radius_r × R (the sprite's width in units at scale 1 given). Pure.</summary>
        public static float CoronaScale(Rig r, float radiusU, float spriteWidthUnits) => 2f * r.corona.radius_r * radiusU / Mathf.Max(0.01f, spriteWidthUnits);
        /// <summary>The clock quantised to `hz` steps (the contract's 12 Hz; hz ≤ 0 = continuous). Pure.</summary>
        public static float Step(float t, float hz) => hz > 0f ? Mathf.Floor(t * hz) / hz : t;
        /// <summary>Tongue i's angle round the rim: evenly spaced, spinning at spinDegPerS. Pure.</summary>
        public static float TongueAngle(int i, int count, float spinDegPerS, float t) => i * 360f / Mathf.Max(1, count) + spinDegPerS * t;
        /// <summary>1 ± pulse on the beat (a sine at beat_bpm). Pure.</summary>
        public static float Pulse(float t, float bpm, float pulse) => 1f + pulse * Mathf.Sin(2f * Mathf.PI * t * bpm / 60f);
        /// <summary>The corona breathes once per four beats. Pure.</summary>
        public static float Breathe(float t, float bpm, float breathe) => 1f + breathe * Mathf.Sin(2f * Mathf.PI * t * bpm / 240f);
        /// <summary>A prominence's slow wobble in degrees (±3° over ~8 s, each at its own phase). Pure.</summary>
        public static float ProminenceWobble(float t, int index) => 3f * Mathf.Sin(2f * Mathf.PI * t * 0.12f + index * 2.1f);
        public static Vector3 Polar(float angleDeg, float r) { float a = angleDeg * Mathf.Deg2Rad; return new Vector3(Mathf.Cos(a) * r, Mathf.Sin(a) * r, 0f); }

        // ---------- the live rig ----------

        public Rig Json { get; private set; }
        public float Radius { get; private set; }
        public bool Built => body != null;
        public SpriteRenderer Body => body;
        public SpriteRenderer CoronaRenderer => corona;
        public IReadOnlyList<Transform> Tongues => tongues;
        public IReadOnlyList<Transform> Prominences => prominences;
        /// <summary>The last stepped clock the pose was written for (tests read it).</summary>
        public float LastStep { get; private set; } = -1f;

        SpriteRenderer body, corona;
        readonly List<Transform> tongues = new List<Transform>();
        readonly List<Transform> prominences = new List<Transform>();
        Dictionary<string, Sprite> sprites;
        int order;
        float partScale, coronaScale;
        Material material;
        AsyncOperationHandle<IList<Sprite>> sheet;
        AsyncOperationHandle<TextAsset> json;

        public void Load(string key, float radius, int sortingOrder)
        {
            Radius = radius;
            order = sortingOrder;
            var reg = ArtMaterials.Active;
            material = reg != null && reg.unlit != null ? reg.unlit : ArtMaterials.MaterialFor(key);
            sheet = ArtLoad.Asset<IList<Sprite>>(key);
            sheet.Completed += op =>
            {
                if (this == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                sprites = Meridian.Flora.RigBuild.ByName(op.Result);
                TryBuild();
            };
            json = ArtLoad.Asset<TextAsset>(key + "/json");
            json.Completed += op =>
            {
                if (this == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null) return;
                Json = Parse(op.Result.text);
                TryBuild();
            };
        }

        SpriteRenderer Part(string name, string partName, int orderOffset)
        {
            if (!sprites.TryGetValue(partName, out var sprite) || sprite == null) return null;
            var go = new GameObject(name);
            go.transform.SetParent(transform, false);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = sprite;
            sr.sortingOrder = order + orderOffset;
            if (material != null) sr.sharedMaterial = material;
            return sr;
        }

        void TryBuild()
        {
            if (Built || Json == null || sprites == null) return;
            if (!sprites.TryGetValue("body", out var bodySprite) || bodySprite == null) { Debug.LogWarning($"[MERIDIAN] SunView: {Key} has no 'body' part; the spheroid stays."); return; }
            partScale = PartScale(Json, bodySprite.pixelsPerUnit);
            // Orders: corona 0 (the wash behind), tongues 1, prominences 2, body 3 — the json's part orders.
            corona = Part("Corona", Json.corona.part, 0);
            if (corona != null) coronaScale = CoronaScale(Json, Radius, corona.sprite.rect.width / corona.sprite.pixelsPerUnit);
            for (int i = 0; i < Mathf.Max(0, Json.ring.count); i++)
            {
                var t = Part("Tongue" + i, Json.ring.part, 1);
                if (t == null) break;
                tongues.Add(t.transform);
            }
            for (int i = 0; i < Json.prominences.Length; i++)
            {
                var p = Part("Prominence" + i, Json.prominences[i].part, 2);
                if (p != null) prominences.Add(p.transform);
            }
            body = Part("Body", "body", 3);
            body.transform.localScale = Vector3.one * partScale;
            Pose(Step(Time.time, Json.ring.stepped_hz));
        }

        void LateUpdate()
        {
            if (!Built) return;
            float t = Step(Time.time, Json.ring.stepped_hz);
            if (t == LastStep) return;
            Pose(t);
        }

        /// <summary>Writes the rig's pose for clock `t`: 17 transforms, at most 12 times a second.</summary>
        void Pose(float t)
        {
            LastStep = t;
            var ring = Json.ring;
            float pulse = Pulse(t, ring.beat_bpm, ring.pulse);
            for (int i = 0; i < tongues.Count; i++)
            {
                float a = TongueAngle(i, tongues.Count, ring.spin_deg_per_s, t);
                var tr = tongues[i];
                tr.localPosition = Polar(a, ring.base_r * Radius);
                tr.localRotation = Quaternion.Euler(0f, 0f, a - 90f); // the part points up from its base pivot: up = outward
                tr.localScale = Vector3.one * (partScale * ring.alt_scale[i % ring.alt_scale.Length] * pulse);
            }
            for (int i = 0; i < prominences.Count; i++)
            {
                float a = Json.prominences[i].angle_deg;
                var tr = prominences[i];
                tr.localPosition = Polar(a, Radius);
                tr.localRotation = Quaternion.Euler(0f, 0f, a - 90f + ProminenceWobble(t, i));
                tr.localScale = Vector3.one * partScale;
            }
            if (corona != null) corona.transform.localScale = Vector3.one * (coronaScale * Breathe(t, ring.beat_bpm, Json.corona.breathe));
        }

        void OnDestroy()
        {
            if (sheet.IsValid()) ArtLoad.Release(sheet);
            if (json.IsValid()) ArtLoad.Release(json);
        }
    }
}
