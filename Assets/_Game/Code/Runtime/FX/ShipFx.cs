using Meridian.Art;
using Meridian.Ship;
using Meridian.Space;
using UnityEngine;

namespace Meridian.FX
{
    /// <summary>
    /// U-033 ship effects. Side view (SideShip): main engine flame aft and two belly-pod flames while
    /// thrusting; heat shimmer under the hull while it comes down fast high above the ground (entry).
    /// Top-down (SpaceShip): the engine flame behind the hull while thrusting.
    /// U-150 (D-158 (4)): accelerating reads differently from cruising: while the hull boosts the flame is the long boost flame
    /// (B-171's puff_boost, the puff drawn 1.6× longer until it lands) and speed lines stream along the frame's edges, scaled by speed;
    /// at cruise both ease off. Breaking the sound barrier puts a vapor cone round the hull for 0.5 s and a shock ring expanding from
    /// where it broke. B-171's sheets draw them once they load; flat white shapes until then. No allocation per frame.
    /// </summary>
    public sealed class ShipFx : MonoBehaviour
    {
        public SideShip side;
        public SpaceShip top;
        /// <summary>U-150: the side camera the speed lines frame (found once when unset).</summary>
        public Camera view;

        /// <summary>Entry shimmer: descending faster than this (m/s) and higher than ShimmerAltitude above ground.</summary>
        public const float ShimmerSpeed = 8f, ShimmerAltitude = 30f;
        /// <summary>U-150: the puff's y stretch at full boost while B-171's boost flame is not in.</summary>
        public const float BoostStretch = 1.6f;
        /// <summary>U-150: speed lines (count; shown from LinesFrom m/s, full at LinesFull; their top alpha), the vapor cone and the shock ring.</summary>
        public const int SpeedLineCount = 10;
        public const float LinesFrom = 8f, LinesFull = 40f, LinesAlpha = 0.55f;
        public const float VaporSeconds = 0.5f, RingSeconds = 0.6f, RingStart = 3f, RingEnd = 28f;
        /// <summary>U-150 (B-171): the hull's centre of mass above the ship's pivot, where the vapor cone and the shock ring are pivoted.</summary>
        public const float CentreOfMass = 6.2f;
        /// <summary>U-150 (B-171): fx/ship/speed_lines tiles (128 × 360 px), three per edge stacked over the frame's height.</summary>
        public const int LineTilesPerEdge = 3;

        public FxLoop Main { get; private set; }
        public FxLoop PodFore { get; private set; }
        public FxLoop PodAft { get; private set; }
        public FxLoop Shimmer { get; private set; }
        /// <summary>U-103 (B-122): true once the loops sit on the drawn rig's sockets (tail_exhaust, attitude_l / attitude_r) with the puff sheet.</summary>
        public bool OnRig { get; private set; }
        /// <summary>U-150: the speed lines' alpha this frame (0 at cruise).</summary>
        public float SpeedLineAlpha { get; private set; }
        /// <summary>U-150: true while the vapor cone / the shock ring shows.</summary>
        public bool VaporShown => vaporT >= 0f;
        public bool RingShown => ringT >= 0f;
        /// <summary>U-150: the flame's key now (the puff, or B-171's boost flame while boosting once it is in).</summary>
        public string FlameKey => Main != null ? Main.key : null;
        Meridian.Ship.ShipLegsView legsView;

        SpriteRenderer[] lines;
        float[] linePhase, lineLane;
        SpriteRenderer vapor, ring;
        float vaporT = -1f, ringT = -1f;
        Vector3 ringAt;
        bool lookedForView;
        float linesT;
        FxSheet boostSheet, linesSheet, coneSheet, ringSheet;
        static Sprite white, cone, ringShape;
        const int LinesOrder = 400;

        void Awake()
        {
            if (side != null)
            {
                // U-107 (D-102): the rocket stands upright on its tail: the main nozzle points down out of the tail (below the
                // pivot by SkidDrop), two small vents at the leg roots. Children of the ship, so they tilt with it.
                Main = Make("Main", ArtKeys.Fx.Thruster, new Vector2(0f, -SideShip.SkidDrop - 0.9f), 0f, new Vector2(2.2f, 2.4f));
                PodAft = Make("PodAft", ArtKeys.Fx.Thruster, new Vector2(-1.5f, -SideShip.SkidDrop + 0.4f), 0f, new Vector2(1.0f, 1.2f));
                PodFore = Make("PodFore", ArtKeys.Fx.Thruster, new Vector2(1.5f, -SideShip.SkidDrop + 0.4f), 0f, new Vector2(1.0f, 1.2f));
                // B-030 entry heat: a 1 m square frame (ppu 128) with the bow-shock arc low in it and the plasma
                // trailing up. At 13 m the arc (~85% of the width) spans the 11.4 m hull and sits ~0.7 m under
                // the belly. Its emission map makes it glow through night and dust (Sprite_LitEmissive).
                Shimmer = Make("Shimmer", ArtKeys.Fx.HeatShimmer, new Vector2(0f, -SideShip.SkidDrop + 1.2f), 0f, new Vector2(7f, 7f)); // the tail leads on the way down
                Shimmer.flicker = 0f;
                MakeBoostFx();
            }
            else if (top != null)
            {
                Main = Make("Main", ArtKeys.Fx.Thruster, new Vector2(-2.1f, 0f), -90f, new Vector2(1.2f, 1.6f)); // ship drawn 4 u wide
            }
        }

        void OnEnable() { if (side != null) side.SoundBarrierBroken += OnBoom; }
        void OnDisable() { if (side != null) side.SoundBarrierBroken -= OnBoom; }

        void OnDestroy() { if (ring != null) Destroy(ring.gameObject); }

        FxLoop Make(string name, string key, Vector2 local, float rot, Vector2 scale)
        {
            var go = new GameObject("Fx" + name);
            go.transform.SetParent(transform, false);
            go.transform.localPosition = local;
            go.transform.localRotation = Quaternion.Euler(0f, 0f, rot);
            go.transform.localScale = new Vector3(scale.x, scale.y, 1f);
            var loop = go.AddComponent<FxLoop>(); // its Awake adds the SpriteRenderer
            loop.key = key;
            loop.target.sortingOrder = name == "Shimmer" ? -2 : -1; // all behind the hull: the shimmer's plasma trails around it, its bow shock glows below the belly
            loop.flicker = 0.18f;
            return loop;
        }

        /// <summary>U-150: the speed lines (world sprites placed along the frame's edges every frame), the vapor cone on the hull and the
        /// shock ring (left in the world where the barrier broke). Built once; B-171's sheets are asked for now and draw once they load.</summary>
        void MakeBoostFx()
        {
            Shapes();
            boostSheet = FxSheet.Get(ArtKeys.Ships.PilgrimPuffBoost);
            linesSheet = FxSheet.Get(ArtKeys.Fx.SpeedLines);
            coneSheet = FxSheet.Get(ArtKeys.Fx.VaporCone);
            ringSheet = FxSheet.Get(ArtKeys.Fx.ShockRing);
            lines = new SpriteRenderer[SpeedLineCount];
            linePhase = new float[SpeedLineCount];
            lineLane = new float[SpeedLineCount];
            var rng = new System.Random(150);
            for (int i = 0; i < SpeedLineCount; i++)
            {
                var go = new GameObject("FxSpeedLine" + i);
                go.transform.SetParent(transform, false);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sprite = white;
                sr.sortingOrder = LinesOrder;
                sr.enabled = false;
                lines[i] = sr;
                linePhase[i] = (float)rng.NextDouble();
                lineLane[i] = (i % 2 == 0 ? -1f : 1f) * (0.78f + 0.18f * (float)rng.NextDouble()); // the left and right edges of the frame
            }
            var vgo = new GameObject("FxVaporCone");
            vgo.transform.SetParent(transform, false);
            vgo.transform.localPosition = new Vector3(0f, CentreOfMass, 0f); // B-171: pivoted at the hull's centre of mass
            vapor = vgo.AddComponent<SpriteRenderer>();
            vapor.sprite = cone;
            vapor.sortingOrder = 2; // B-171: in front of the hull (re-set from the rig's order in PlaceOnRig)
            vapor.enabled = false;
            var rgo = new GameObject("FxShockRing");
            rgo.transform.SetParent(transform.parent != null ? transform.parent : null, false); // the side root: it stays where the barrier broke
            ring = rgo.AddComponent<SpriteRenderer>();
            ring.sprite = ringShape;
            ring.sortingOrder = -3; // B-171: behind the hull
            ring.enabled = false;
        }

        /// <summary>The flat white placeholder shapes (built once, shared): a quad, a cone opening toward the tail, a ring.</summary>
        static void Shapes()
        {
            if (white == null)
            {
                var tex = Texture2D.whiteTexture;
                white = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0.5f), tex.width, 0, SpriteMeshType.FullRect);
                white.name = "FxWhite";
            }
            if (cone == null)
            {
                const int n = 64;
                var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { name = "FxConePlaceholder", wrapMode = TextureWrapMode.Clamp };
                var px = new Color32[n * n];
                for (int y = 0; y < n; y++)
                    for (int x = 0; x < n; x++)
                    {
                        float v = y / (n - 1f);                    // 1 at the nose (top), 0 at the open end
                        float half = 0.5f * (1f - v);              // the cone widens toward the tail
                        float d = Mathf.Abs(x / (n - 1f) - 0.5f);
                        float a = Mathf.Clamp01((half - d) * 12f) * Mathf.Clamp01(v * 3f) * 0.85f;
                        px[y * n + x] = new Color32(255, 255, 255, (byte)(a * 255f));
                    }
                tex.SetPixels32(px); tex.Apply(false, true);
                cone = Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f), n, 0, SpriteMeshType.FullRect);
            }
            if (ringShape == null)
            {
                const int n = 128;
                var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { name = "FxRingPlaceholder", wrapMode = TextureWrapMode.Clamp };
                var px = new Color32[n * n];
                for (int y = 0; y < n; y++)
                    for (int x = 0; x < n; x++)
                    {
                        float r = new Vector2(x / (n - 1f) - 0.5f, y / (n - 1f) - 0.5f).magnitude * 2f; // 0 at the centre, 1 at the edge
                        float a = Mathf.Clamp01(1f - Mathf.Abs(r - 0.9f) * 14f);
                        px[y * n + x] = new Color32(255, 255, 255, (byte)(a * 255f));
                    }
                tex.SetPixels32(px); tex.Apply(false, true);
                ringShape = Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f), n, 0, SpriteMeshType.FullRect);
            }
        }

        void OnBoom()
        {
            vaporT = 0f;
            ringT = 0f;
            var st = side.transform;
            ringAt = st.position + st.up * CentreOfMass;
        }

        /// <summary>
        /// U-103 (B-122, D-111): with the drawn rig the main flame becomes the puff loop hanging from the tail_exhaust socket
        /// (the puff's pivot is its top centre) and the attitude puffs sit at attitude_l / attitude_r blowing outward, all under
        /// the squash root so they stretch with the hull; sockets are metres from the rig origin on the skid line and never move
        /// with the clips. The entry shimmer stays where it was.
        /// </summary>
        void PlaceOnRig()
        {
            if (legsView == null) legsView = side.GetComponentInChildren<Meridian.Ship.ShipLegsView>();
            if (legsView == null || !legsView.RigReady) return;
            OnRig = true;
            var rig = legsView.Rig;
            var origin = new Vector2(0f, -SideShip.SkidDrop);
            int layer = legsView.target != null ? legsView.target.sortingLayerID : 0;
            int behind = (legsView.target != null ? legsView.target.sortingOrder : 0) - 1;
            Move(Main, ArtKeys.Ships.PilgrimPuff, origin + rig.Socket("tail_exhaust", new Vector2(0f, 0.85f)), 0f, new Vector2(1.3f, 1.3f), legsView.SquashRoot, layer, behind);
            Move(PodAft, ArtKeys.Ships.PilgrimPuff, origin + rig.Socket("attitude_l", new Vector2(-1.5f, 2.6f)), -90f, new Vector2(0.45f, 0.45f), legsView.SquashRoot, layer, behind);
            Move(PodFore, ArtKeys.Ships.PilgrimPuff, origin + rig.Socket("attitude_r", new Vector2(1.5f, 2.6f)), 90f, new Vector2(0.45f, 0.45f), legsView.SquashRoot, layer, behind);
            // U-150 (B-171): the vapor cone in front of the hull, the shock ring behind it (and behind the puffs).
            if (vapor != null) { vapor.sortingLayerID = layer; vapor.sortingOrder = behind + 2; }
            if (ring != null) { ring.sortingLayerID = layer; ring.sortingOrder = behind - 1; }
        }

        static void Move(FxLoop loop, string key, Vector2 local, float rot, Vector2 scale, Transform parent, int layer, int order)
        {
            if (parent != null) loop.transform.SetParent(parent, false);
            loop.transform.localPosition = local;
            loop.transform.localRotation = Quaternion.Euler(0f, 0f, rot);
            loop.transform.localScale = new Vector3(scale.x, scale.y, 1f);
            loop.target.sortingLayerID = layer;
            loop.target.sortingOrder = order;
            loop.SetKey(key);
        }

        void LateUpdate()
        {
            if (side != null)
            {
                if (!OnRig) PlaceOnRig();
                bool flying = side.piloted && !side.Grounded;
                bool lift = side.piloted && side.intent.thrust > 0.05f;
                Main.active = lift;
                PodAft.active = PodFore.active = flying && Mathf.Abs(side.intent.lateral) > 0.05f; // attitude puffs while tilting
                var v = side.Body != null ? side.Body.linearVelocity : Vector2.zero;
                Shimmer.active = v.y < -ShimmerSpeed && side.AltitudeAboveGround > ShimmerAltitude;
                StepBoostFx(v);
            }
            else if (top != null)
            {
                Main.active = !top.Destroyed && top.intent.thrust > 0.05f;
            }
        }

        /// <summary>U-150: the boost flame, the speed lines, the vapor cone and the shock ring for this frame.</summary>
        void StepBoostFx(Vector2 v)
        {
            float boost = side.piloted ? side.Boost : 0f;
            // The flame: B-171's boost flame while boosting once it is in, else the puff drawn longer with the boost.
            if (OnRig)
            {
                bool longFlame = boostSheet != null && boostSheet.Ready && boost > 0.5f;
                Main.SwapKey(longFlame ? ArtKeys.Ships.PilgrimPuffBoost : ArtKeys.Ships.PilgrimPuff);
                Main.stretchY = longFlame ? 1f : 1f + (BoostStretch - 1f) * boost;
            }
            else Main.stretchY = 1f + (BoostStretch - 1f) * boost;

            // The speed lines along the frame's edges, streaming against the hull's motion.
            if (view == null && (!lookedForView || Time.frameCount % 60 == 0))
            {
                lookedForView = true; // then once a second: test scenes without a side camera draw no lines
                var follow = FindAnyObjectByType<Meridian.Player.CameraFollow>();
                if (follow != null) view = follow.GetComponent<Camera>();
            }
            float speed = v.magnitude;
            SpeedLineAlpha = boost * Mathf.Clamp01((speed - LinesFrom) / (LinesFull - LinesFrom)) * LinesAlpha;
            bool show = SpeedLineAlpha > 0.01f && view != null && view.orthographic;
            bool sheetLines = linesSheet != null && linesSheet.Ready;
            float halfH = show ? view.orthographicSize : 0f, halfW = halfH * (show ? view.aspect : 0f);
            var dir = speed > 0.1f ? v / speed : Vector2.up;
            float angle = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg - 90f;
            var c = show ? (Vector2)view.transform.position : Vector2.zero;
            float len = halfH * (0.12f + 0.18f * Mathf.Clamp01(speed / LinesFull)), width = halfH * 0.006f;
            if (show && sheetLines) linesT += Time.deltaTime;
            for (int i = 0; i < lines.Length; i++)
            {
                var sr = lines[i];
                bool on = show && (!sheetLines || i < 2 * LineTilesPerEdge);
                if (sr.enabled != on) sr.enabled = on;
                if (!on) continue;
                if (sheetLines)
                {
                    // B-171: three 128 × 360 tiles stacked on each edge over the frame's height, the 4-frame loop drawn for the left edge and
                    // flipped in x for the right; the speed sets their alpha.
                    int f = linesSheet.FrameAt(linesT);
                    if (f >= 0) sr.sprite = linesSheet.frames[f];
                    bool right = i >= LineTilesPerEdge;
                    int row = i % LineTilesPerEdge;
                    var size = sr.sprite.bounds.size;
                    float s = 2f * halfH / LineTilesPerEdge / Mathf.Max(0.01f, size.y);
                    var rect = sr.sprite.rect;
                    float offX = rect.width > 0f ? (0.5f - sr.sprite.pivot.x / rect.width) * size.x * s : 0f; // pivot → centre
                    float offY = rect.height > 0f ? (0.5f - sr.sprite.pivot.y / rect.height) * size.y * s : 0f;
                    float w = size.x * s;
                    float cxTile = right ? c.x + halfW - w * 0.5f : c.x - halfW + w * 0.5f;
                    float cyTile = c.y - halfH + (row + 0.5f) * 2f * halfH / LineTilesPerEdge;
                    sr.flipX = right;
                    sr.transform.SetPositionAndRotation(new Vector3(cxTile - (right ? -offX : offX), cyTile - offY, 0f), Quaternion.identity);
                    sr.transform.localScale = new Vector3(s, s, 1f);
                    sr.color = new Color(1f, 1f, 1f, Mathf.Clamp01(SpeedLineAlpha / LinesAlpha));
                    continue;
                }
                // The placeholder: thin white lines streaming along the frame's edges against the hull's motion.
                linePhase[i] = Mathf.Repeat(linePhase[i] + Time.deltaTime * speed / (2f * halfH) * 1.6f, 1f);
                float along = (0.5f - linePhase[i]) * 2f * halfH; // from the leading edge back past the trailing one
                var p = c + new Vector2(lineLane[i] * halfW, 0f) + dir * along;
                sr.transform.SetPositionAndRotation(new Vector3(p.x, p.y, 0f), Quaternion.Euler(0f, 0f, angle));
                sr.transform.localScale = new Vector3(width, len, 1f);
                sr.color = new Color(1f, 1f, 1f, SpeedLineAlpha);
            }

            // The vapor cone round the hull (0.5 s) and the shock ring from where the barrier broke (0.6 s).
            if (vaporT >= 0f)
            {
                vaporT += Time.deltaTime;
                if (coneSheet != null && coneSheet.Ready)
                {
                    // B-171: the one-shot cone (10 frames) drawn 1:1 at the centre of mass; it ends with its clip.
                    int f = coneSheet.FrameAt(vaporT);
                    if (f < 0) { vaporT = -1f; vapor.enabled = false; }
                    else { vapor.sprite = coneSheet.frames[f]; vapor.enabled = true; vapor.transform.localScale = Vector3.one; vapor.color = Color.white; }
                }
                else
                {
                    float k = vaporT / VaporSeconds;
                    if (k >= 1f) { vaporT = -1f; vapor.enabled = false; }
                    else
                    {
                        vapor.enabled = true;
                        float w = SideShip.BodyWidth * (2.2f + 0.6f * k);
                        vapor.transform.localScale = new Vector3(w, SideShip.Height * 0.55f, 1f);
                        vapor.color = new Color(1f, 1f, 1f, 0.85f * (1f - k * k));
                    }
                }
            }
            if (ringT >= 0f)
            {
                ringT += Time.deltaTime;
                ring.transform.SetPositionAndRotation(ringAt, Quaternion.identity);
                if (ringSheet != null && ringSheet.Ready)
                {
                    // B-171: the one-shot ring (8 frames) drawn 1:1 where the barrier broke; it ends with its clip.
                    int f = ringSheet.FrameAt(ringT);
                    if (f < 0) { ringT = -1f; ring.enabled = false; }
                    else { ring.sprite = ringSheet.frames[f]; ring.enabled = true; ring.transform.localScale = Vector3.one; ring.color = Color.white; }
                }
                else
                {
                    float k = ringT / RingSeconds;
                    if (k >= 1f) { ringT = -1f; ring.enabled = false; }
                    else
                    {
                        ring.enabled = true;
                        float d = Mathf.Lerp(RingStart, RingEnd, 1f - (1f - k) * (1f - k)); // fast out, slowing
                        float s = d / Mathf.Max(0.01f, ring.sprite.bounds.size.x);
                        ring.transform.localScale = new Vector3(s, s, 1f);
                        ring.color = new Color(1f, 1f, 1f, 0.9f * (1f - k));
                    }
                }
            }
        }
    }
}
