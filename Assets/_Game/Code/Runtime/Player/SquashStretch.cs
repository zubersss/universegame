using UnityEngine;

namespace Meridian.Player
{
    /// <summary>
    /// U-089 (Bible §4.2 Feel): squash and stretch on a visual root only, volume-preserving (width = 1/√height; the
    /// dash stretches along x instead). One curve at a time, the newest event wins; pure C#, no allocation.
    /// Curves: take-off (crouch 0.8 for 0.06 s, then 1.25 for 0.08 s), landing (0.7 at ≥ 6 m/s scaled from 1.0 at
    /// 2 m/s, recovering in 0.18 s with one overshoot to 1.05), dash (1.3 along the dash), hit (0.85 for 0.12 s).
    /// </summary>
    public sealed class SquashStretch
    {
        public const float CrouchScale = 0.8f, CrouchTime = 0.06f, TakeOffScale = 1.25f, TakeOffTime = 0.08f;
        public const float LandSoftSpeed = 2f, LandHardSpeed = 6f, LandScale = 0.7f, LandRecover = 0.18f, LandOvershoot = 1.05f, LandOvershootAt = 0.12f;
        public const float DashScale = 1.3f, HitScale = 0.85f, HitTime = 0.12f, Settle = 0.08f;

        struct Key { public float t, v; }
        readonly Key[] keys = new Key[6];
        int count;
        float t;

        public Vector3 Scale { get; private set; } = Vector3.one;
        /// <summary>The height factor (or the length factor along x while dashing).</summary>
        public float Factor { get; private set; } = 1f;
        public bool Active => count > 0;
        public bool Dashing { get; private set; }

        void Begin(bool alongX)
        {
            Dashing = alongX;
            t = 0f;
            count = 0;
        }

        void Add(float at, float value) { keys[count].t = at; keys[count].v = value; count++; }

        /// <summary>At the jump: the crouch anticipation, then the take-off stretch.</summary>
        public void TakeOff()
        {
            Begin(false);
            Add(0f, CrouchScale); Add(CrouchTime, CrouchScale);
            Add(CrouchTime + 0.03f, TakeOffScale); Add(CrouchTime + 0.03f + TakeOffTime, TakeOffScale);
            Add(CrouchTime + 0.03f + TakeOffTime + Settle, 1f);
        }

        /// <summary>Touchdown at `impactSpeed` m/s: nothing below 2 m/s, 0.7 from 6 m/s up.</summary>
        public void Land(float impactSpeed)
        {
            float s = Mathf.Lerp(1f, LandScale, Mathf.InverseLerp(LandSoftSpeed, LandHardSpeed, impactSpeed));
            if (s > 0.999f) return;
            Begin(false);
            Add(0f, s); Add(LandOvershootAt, LandOvershoot); Add(LandRecover, 1f);
        }

        /// <summary>The air dash: stretched along x for its `seconds`, settling after.</summary>
        public void Dash(float seconds)
        {
            Begin(true);
            Add(0f, DashScale); Add(seconds, DashScale); Add(seconds + Settle, 1f);
        }

        public void Hit()
        {
            Begin(false);
            Add(0f, HitScale); Add(HitTime, HitScale); Add(HitTime + Settle, 1f);
        }

        /// <summary>Advances by `dt` and returns the visual scale (sx·sy·sz = 1).</summary>
        public Vector3 Step(float dt)
        {
            if (count == 0) { Factor = 1f; Scale = Vector3.one; Dashing = false; return Scale; }
            t += dt;
            float f = keys[count - 1].v;
            if (t >= keys[count - 1].t) { count = 0; Dashing = false; f = 1f; }
            else
            {
                for (int i = 1; i < count; i++)
                {
                    if (t > keys[i].t) continue;
                    float span = keys[i].t - keys[i - 1].t;
                    float u = span > 1e-6f ? (t - keys[i - 1].t) / span : 1f;
                    f = Mathf.Lerp(keys[i - 1].v, keys[i].v, u);
                    break;
                }
            }
            Factor = f;
            float side = 1f / Mathf.Sqrt(Mathf.Max(0.01f, f));
            Scale = Dashing && count > 0 ? new Vector3(f, side, side) : new Vector3(side, f, side);
            return Scale;
        }
    }
}
