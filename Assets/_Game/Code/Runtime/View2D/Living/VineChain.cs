using UnityEngine;

namespace Meridian.View2D.Living
{
    /// <summary>
    /// U-216 (3): a hanging vine as a jointed chain (a "hangs" piece of contract §12: its pivot is its attachment, its spine
    /// runs from there to the free end). Position-based: every node but the attachment falls, is carried by the wind's
    /// gust where it hangs, keeps its link's length to its neighbour, and is brushed aside by the surveyor's body. Stepped at
    /// a fixed 60 Hz inside (the frame's time is carried over), so the same wind and the same frames give the same swing.
    /// It only draws: nothing of the stage ever stops, slows or lifts the surveyor (LEAD, D-206). No allocation after the
    /// constructor.
    /// </summary>
    public sealed class VineChain
    {
        public const float StepSeconds = 1f / 60f;
        public const int Iterations = 4, MaxStepsAFrame = 4;
        /// <summary>The fall (m/s²), the share of its speed a node keeps a step, the wind's pull on a node in a full gust (m/s²; more toward
        /// the free end), and the flutter riding on it.</summary>
        public const float Gravity = 9.81f, Keep = 0.985f, WindPull = 5.5f, WindAtTop = 0.5f, FlutterPull = 1.4f;
        /// <summary>How near the surveyor's body a node may hang (m beside the body's box) and how much of the way out a step moves it.</summary>
        public const float BrushGapM = 0.12f, BrushShare = 0.5f;

        readonly Vector2[] now, before;
        public int Count => now.Length;
        public float LinkM { get; }
        public Vector2 Anchor { get; private set; }
        /// <summary>Fixed at both ends (a liana): the last node hangs on EndAnchor.</summary>
        public bool BothEnds { get; private set; }
        public Vector2 EndAnchor { get; private set; }
        public Vector2 this[int i] => now[i];
        /// <summary>Fixed steps taken since it was made (tests).</summary>
        public int Steps { get; private set; }
        float carried;

        /// <summary>A chain of `links` links of `linkM` hanging straight down from `anchor`, at rest.</summary>
        public VineChain(Vector2 anchor, int links, float linkM)
        {
            links = Mathf.Max(1, links);
            LinkM = Mathf.Max(0.02f, linkM);
            now = new Vector2[links + 1];
            before = new Vector2[links + 1];
            Anchor = anchor;
            for (int i = 0; i <= links; i++) now[i] = before[i] = anchor + Vector2.down * (LinkM * i);
        }

        /// <summary>The free end made fast at `end` (a liana between two holds); its length is the chain's own, so it sags.</summary>
        public void HoldEnd(Vector2 end) { BothEnds = true; EndAnchor = end; }

        public void MoveAnchor(Vector2 anchor) { Anchor = anchor; }

        /// <summary>The body's box the vine is brushed by: its centre and half size; `brushing` false: nobody near.</summary>
        public void Step(float dt, LivingWind wind, Vector2 bodyCentre, Vector2 bodyHalf, bool brushing)
        {
            if (dt <= 0f) return;
            carried += dt;
            int taken = 0;
            while (carried >= StepSeconds && taken < MaxStepsAFrame)
            {
                carried -= StepSeconds;
                taken++;
                Fixed(wind, bodyCentre, bodyHalf, brushing);
            }
            if (taken == MaxStepsAFrame && carried > StepSeconds) carried = 0f; // a very long frame: the time is dropped, not caught up
        }

        void Fixed(LivingWind wind, Vector2 bodyCentre, Vector2 bodyHalf, bool brushing)
        {
            Steps++;
            int last = now.Length - 1;
            float h2 = StepSeconds * StepSeconds;
            float t = Steps * StepSeconds;
            for (int i = 1; i <= last; i++)
            {
                if (BothEnds && i == last) break;
                var p = now[i];
                var v = (p - before[i]) * Keep;
                before[i] = p;
                var a = new Vector2(0f, -Gravity);
                if (wind != null)
                {
                    float down = (float)i / last; // 0 at the attachment, 1 at the free end
                    float pull = WindPull * wind.Strength * wind.Gust(p.x) * (WindAtTop + (1f - WindAtTop) * down);
                    pull += FlutterPull * wind.Strength * down * Mathf.Sin(LivingWind.TwoPi * (0.8f * t + 0.31f * i));
                    a += wind.Direction * pull;
                }
                now[i] = p + v + a * h2;
            }
            if (brushing)
            {
                float hx = bodyHalf.x + BrushGapM, hy = bodyHalf.y + BrushGapM;
                for (int i = 1; i <= last; i++)
                {
                    if (BothEnds && i == last) break;
                    var d = now[i] - bodyCentre;
                    if (Mathf.Abs(d.x) >= hx || Mathf.Abs(d.y) >= hy) continue;
                    float out_ = (d.x >= 0f ? hx : -hx) - d.x; // sideways out of the body, the nearer way
                    now[i].x += out_ * BrushShare;
                }
            }
            for (int k = 0; k < Iterations; k++)
            {
                now[0] = Anchor;
                if (BothEnds) now[last] = EndAnchor;
                for (int i = 0; i < last; i++)
                {
                    var d = now[i + 1] - now[i];
                    float len = d.magnitude;
                    if (len < 1e-6f) continue;
                    var fix = d * ((len - LinkM) / len);
                    bool aFixed = i == 0, bFixed = BothEnds && i + 1 == last;
                    if (aFixed && bFixed) continue;
                    if (aFixed) now[i + 1] -= fix;
                    else if (bFixed) now[i] += fix;
                    else { now[i] += fix * 0.5f; now[i + 1] -= fix * 0.5f; }
                }
            }
            now[0] = Anchor;
            if (BothEnds) now[last] = EndAnchor;
        }

        /// <summary>The chain's length along its nodes now (tests: it keeps its links).</summary>
        public float Length()
        {
            float sum = 0f;
            for (int i = 0; i + 1 < now.Length; i++) sum += (now[i + 1] - now[i]).magnitude;
            return sum;
        }

        /// <summary>How far the free end hangs off the plumb line under the attachment (m, signed along x).</summary>
        public float Swing => now[now.Length - 1].x - Anchor.x;
    }
}
