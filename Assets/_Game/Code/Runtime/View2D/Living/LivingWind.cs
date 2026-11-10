using UnityEngine;

namespace Meridian.View2D.Living
{
    /// <summary>
    /// U-216 (D-205, STYLE_V7 §3 "Alive"; the piece format of contract §12): the living stage's wind field. One direction and one
    /// strength for the whole stage, and slow gusts that cross it: two travelling waves of unlike length and speed, so the gusts do
    /// not repeat for minutes. A plant leans with the gust at its root and flutters on its own beat. The same sums run in
    /// Shaders/LivingStage.shader for every vertex of the stage's meshes (one draw call a layer, no script per plant); this class
    /// is the clock, the shader's constants, and the same field for what moves on the CPU (the vine chain, the motes, the
    /// tests). Pure but for Push(): the same seed and the same steps give the same field. No allocation.
    /// </summary>
    public sealed class LivingWind
    {
        public const float TwoPi = Mathf.PI * 2f;
        /// <summary>The gusts: a long slow wave and a short quicker one (m, m/s), and their shares of the lean (the base is the steady wind).</summary>
        public const float GustLengthA = 23f, GustSpeedA = 3.1f, GustLengthB = 7.3f, GustSpeedB = 4.7f;
        public const float LeanBase = 0.55f, LeanA = 0.30f, LeanB = 0.15f;
        /// <summary>A plant's own flutter: its share of the piece's give, its beat (Hz, by the plant's phase), how much of it is there in a lull.</summary>
        public const float FlutterShare = 0.18f, FlutterHzMin = 0.7f, FlutterHzSpan = 0.5f, FlutterInLull = 0.35f, FlutterAcross = 0.9f;
        /// <summary>The tip dips by this share of its sideways travel (a bent stem is no longer than a straight one).</summary>
        public const float DipShare = 0.25f;
        /// <summary>The surveyor passing: plants rooted within PushRadiusM of the feet (and between PushBelowM under and PushAboveM over
        /// them) part to either side, at most PushGiveM at the tip of a soft plant (a stiff one by its give).</summary>
        public const float PushRadiusM = 1.4f, PushGiveM = 0.28f, PushBelowM = 0.6f, PushAboveM = 1.6f, PushSoftGiveM = 0.25f;

        /// <summary>Shader constants (set by Push): (direction x, direction y, strength, clock), (phase A, phase B, 0, 0), (the pusher's
        /// feet x, y, 1 when someone pushes, 0).</summary>
        public static readonly int WindId = Shader.PropertyToID("_LivingWind"), PhaseId = Shader.PropertyToID("_LivingWindPhase"), PushId = Shader.PropertyToID("_LivingPush");

        public int Seed { get; }
        /// <summary>The wind's own clock (s): it stands still when the game does.</summary>
        public float Clock { get; private set; }
        /// <summary>Which way the wind blows (a unit vector; the gusts travel along its x) and how hard (0 still, 1 a full gust's worth).</summary>
        public Vector2 Direction { get; private set; } = Vector2.right;
        public float Strength { get; private set; } = 0.6f;
        public float PhaseA { get; }
        public float PhaseB { get; }
        /// <summary>The surveyor's feet while they push plants aside (Pushing false: nobody on the stage).</summary>
        public Vector2 Pusher { get; private set; }
        public bool Pushing { get; private set; }

        public LivingWind(int seed)
        {
            Seed = seed;
            PhaseA = Meridian.Mining.DigRun.Hash01(seed, 11, 4201) * TwoPi;
            PhaseB = Meridian.Mining.DigRun.Hash01(seed, 12, 4202) * TwoPi;
        }

        public void Set(Vector2 direction, float strength)
        {
            Direction = direction.sqrMagnitude > 1e-8f ? direction.normalized : Vector2.right;
            Strength = Mathf.Clamp01(strength);
        }

        public void SetPusher(Vector2 feet, bool pushing) { Pusher = feet; Pushing = pushing; }

        /// <summary>One frame of the wind's clock.</summary>
        public void Step(float dt) { if (dt > 0f) Clock += dt; }

        float Along => Direction.x >= 0f ? 1f : -1f;

        /// <summary>The gust at x now: about 0.1 in a lull to 1.0 in a gust's crest. Pure.</summary>
        public float Gust(float x) => Gust(x * Along, Clock, PhaseA, PhaseB);

        /// <summary>The gust at a place `s` along the wind at time t. Pure.</summary>
        public static float Gust(float s, float t, float phaseA, float phaseB) =>
            LeanBase + LeanA * Mathf.Sin(TwoPi * (s - GustSpeedA * t) / GustLengthA + phaseA) + LeanB * Mathf.Sin(TwoPi * (s - GustSpeedB * t) / GustLengthB + phaseB);

        /// <summary>
        /// Where a point of a rooted piece is moved to, from its rest: `root` the piece's root in the world, `weight` the point's bend
        /// weight (0 at the root, 1 at the farthest tip), `giveM` the tip's travel in a full gust, `phase` the plant's own (0..1).
        /// The lean with the gust, the plant's flutter, the tip's dip, and the surveyor's push. The shader's vertex stage is this sum.
        /// </summary>
        public Vector2 Offset(Vector2 root, float weight, float giveM, float phase)
        {
            if (weight <= 0f || giveM <= 0f) return Vector2.zero;
            float gust = Gust(root.x);
            float hz = FlutterHzMin + FlutterHzSpan * phase;
            float flutter = (FlutterInLull + (1f - FlutterInLull) * gust) * FlutterShare * Mathf.Sin(TwoPi * (hz * Clock + phase) + root.x * FlutterAcross);
            float along = giveM * weight * Strength * (gust + flutter);
            var offset = Direction * along;
            offset.y -= Mathf.Abs(along) * DipShare * weight;
            if (Pushing)
            {
                float dx = root.x - Pusher.x, up = Pusher.y - root.y;
                float ax = Mathf.Abs(dx);
                if (ax < PushRadiusM && up > -PushBelowM && up < PushAboveM)
                {
                    float k = 1f - ax / PushRadiusM;
                    offset.x += (dx >= 0f ? 1f : -1f) * PushGiveM * k * k * weight * Mathf.Clamp01(giveM / PushSoftGiveM);
                }
            }
            return offset;
        }

        /// <summary>Hands the field to the shader (once a frame, by the stage). Not pure: global shader state.</summary>
        public void Push()
        {
            Shader.SetGlobalVector(WindId, new Vector4(Direction.x, Direction.y, Strength, Clock));
            Shader.SetGlobalVector(PhaseId, new Vector4(PhaseA, PhaseB, 0f, 0f));
            Shader.SetGlobalVector(PushId, new Vector4(Pusher.x, Pusher.y, Pushing ? 1f : 0f, 0f));
        }

        /// <summary>A still field for the shader (the stage is off or gone: nothing a leftover material could move by).</summary>
        public static void PushStill()
        {
            Shader.SetGlobalVector(WindId, new Vector4(1f, 0f, 0f, 0f));
            Shader.SetGlobalVector(PhaseId, Vector4.zero);
            Shader.SetGlobalVector(PushId, Vector4.zero);
        }
    }
}
