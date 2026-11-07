using System.Collections.Generic;
using System.Text.RegularExpressions;
using UnityEngine;
using UnityEngine.UI;

namespace Meridian.UI
{
    /// <summary>U-104 (B-121): one needle's sweep from `ui/hud/gauges.json` (`needles.<name>`): its dial and needle parts, the hub as a fraction of the dial, the degrees at 0 and 1, and the danger line.</summary>
    public sealed class GaugeSpec
    {
        public string name, dial, needle;
        public Vector2 hub = new Vector2(0.5f, 0.5f);
        public float minDeg = 125f, maxDeg = -125f, dangerBelow = 0.25f;

        /// <summary>The needle's z rotation for a value in 0..1 (125° → −125° on B-121's dials: a clockwise sweep).</summary>
        public float Angle(float value01) => Mathf.Lerp(minDeg, maxDeg, Mathf.Clamp01(value01));
        public bool InDanger(float value01) => dangerBelow > 0f && value01 < dangerBelow;
        /// <summary>+1 when the sweep runs counter-clockwise in degrees, −1 clockwise (B-121).</summary>
        public float SweepSign => Mathf.Sign(maxDeg - minDeg);
    }

    /// <summary>Reads the `needles` map of a gauge sheet json (JsonUtility has no maps; braces are matched, nothing else is assumed).</summary>
    public static class GaugeSheet
    {
        public static Dictionary<string, GaugeSpec> Parse(string json)
        {
            var result = new Dictionary<string, GaugeSpec>();
            if (string.IsNullOrEmpty(json)) return result;
            int at = json.IndexOf("\"needles\"", System.StringComparison.Ordinal);
            if (at < 0) return result;
            int open = json.IndexOf('{', at);
            int close = Matching(json, open);
            if (open < 0 || close < 0) return result;
            int i = open + 1;
            while (i < close)
            {
                var m = Regex.Match(json.Substring(i, close - i), "\"([^\"]+)\"\\s*:\\s*\\{");
                if (!m.Success) break;
                int o = i + m.Index + m.Length - 1;
                int c = Matching(json, o);
                if (c < 0) break;
                var body = json.Substring(o + 1, c - o - 1);
                var spec = new GaugeSpec
                {
                    name = m.Groups[1].Value,
                    dial = Str(body, "dial"),
                    needle = Str(body, "needle"),
                    minDeg = Num(body, "min_deg", 125f),
                    maxDeg = Num(body, "max_deg", -125f),
                    dangerBelow = Num(body, "danger_below", 0f),
                };
                var hub = Regex.Match(body, "\"hub\"\\s*:\\s*\\[\\s*([-0-9.eE+]+)\\s*,\\s*([-0-9.eE+]+)");
                if (hub.Success) spec.hub = new Vector2(F(hub.Groups[1].Value), F(hub.Groups[2].Value));
                result[spec.name] = spec;
                i = c + 1;
            }
            return result;
        }

        static string Str(string body, string key)
        {
            var m = Regex.Match(body, "\"" + key + "\"\\s*:\\s*\"([^\"]*)\"");
            return m.Success ? m.Groups[1].Value : null;
        }

        static float Num(string body, string key, float fallback)
        {
            var m = Regex.Match(body, "\"" + key + "\"\\s*:\\s*([-0-9.eE+]+)");
            return m.Success ? F(m.Groups[1].Value) : fallback;
        }

        static float F(string s) => float.Parse(s, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture);

        static int Matching(string s, int at)
        {
            if (at < 0 || at >= s.Length || s[at] != '{') return -1;
            int depth = 0;
            for (int i = at; i < s.Length; i++)
            {
                if (s[i] == '{') depth++;
                else if (s[i] == '}' && --depth == 0) return i;
            }
            return -1;
        }
    }

    /// <summary>
    /// U-104, pure: a needle on twos. The shown value changes only on 12 Hz ticks, where it snaps to the meter (so it is
    /// never more than one tick behind, and exact at the tick); a change starts a small overshoot wobble along the sweep
    /// that decays over WobbleSeconds, itself stepped at the same ticks.
    /// </summary>
    public sealed class GaugeNeedle
    {
        public const float Hz = 12f, WobbleDeg = 6f, WobbleSeconds = 0.35f;

        /// <summary>The value the needle shows (−1 before the first tick).</summary>
        public float Shown { get; private set; } = -1f;
        /// <summary>Degrees of wobble along the sweep direction (+ = toward higher values).</summary>
        public float Wobble { get; private set; }
        public bool HasShown => Shown >= 0f;

        int lastTick = int.MinValue;
        float wobbleAge = float.MaxValue, wobbleSign;

        /// <summary>Advances to `time`; true on a tick (the caller redraws the needle then).</summary>
        public bool Step(float target, float time)
        {
            int tick = Mathf.FloorToInt(time * Hz);
            if (tick == lastTick) return false;
            int ticks = lastTick == int.MinValue ? 1 : Mathf.Max(1, tick - lastTick); // the ticks that passed since the last redraw (a hitch skips some)
            lastTick = tick;
            target = Mathf.Clamp01(target);
            if (HasShown && Mathf.Abs(target - Shown) > 0.002f) { wobbleAge = 0f; wobbleSign = target > Shown ? 1f : -1f; }
            else if (wobbleAge < WobbleSeconds) wobbleAge += ticks / Hz;
            Shown = target;
            float k = wobbleAge / WobbleSeconds;
            Wobble = k < 1f ? wobbleSign * WobbleDeg * (1f - k) * Mathf.Sin((k + 0.125f) * 2f * Mathf.PI) : 0f;
            return true;
        }

        public void Reset() { Shown = -1f; Wobble = 0f; lastTick = int.MinValue; wobbleAge = float.MaxValue; }
    }

    /// <summary>
    /// U-104: one HUD gauge in UGUI: the dial Image with the needle Image on its hub (the needle's pivot = the sprite's),
    /// a caption under it in the HUD face. Hidden until Arm gives it B-121's sprites and spec; Step moves it on the 12 Hz
    /// ticks and tints the needle on the danger arc. Nothing allocates per frame.
    /// </summary>
    public sealed class HudGauge
    {
        public readonly string Name;
        public readonly Image Dial, Needle;
        public readonly Text Caption;
        public readonly GaugeNeedle Motion = new GaugeNeedle();
        public GaugeSpec Spec { get; private set; }
        /// <summary>The meter in 0..1 the needle tracks.</summary>
        public float Target;
        /// <summary>False for a readout whose low end is not a danger (the gravity dial).</summary>
        public bool DangerTint = true;
        public bool Ready => Spec != null && Dial.sprite != null && Needle.sprite != null;
        public float Size { get; private set; }

        Color needleColor = Color.white;
        bool danger;

        public HudGauge(Transform parent, string name, Vector2 topLeft, float size, string caption)
        {
            Name = name;
            Size = size;
            var tl = new Vector2(0f, 1f);
            Dial = UiKit.Panel(parent, "Gauge_" + name, tl, topLeft, new Vector2(size, size), Color.white);
            Dial.enabled = false;
            Needle = UiKit.Panel(Dial.transform, "Needle", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(size * 0.15f, size * 0.47f), Color.white);
            Needle.enabled = false;
            Caption = UiKit.Text(parent, "GaugeLabel_" + name, tl, topLeft + new Vector2(0f, -size - 2f), new Vector2(size, 20f), 15, false, TextAnchor.MiddleCenter, UiTheme.Active.label);
            Caption.text = caption;
            Caption.enabled = false;
        }

        /// <summary>Gives the gauge its art: dial and needle sprites at `scale` × their pixel size, the needle pivoted on its hub.</summary>
        public void Arm(GaugeSpec spec, IReadOnlyDictionary<string, Sprite> sprites, float scale)
        {
            Spec = spec;
            if (spec == null) return;
            if (!string.IsNullOrEmpty(spec.dial) && sprites.TryGetValue(spec.dial, out var d))
            {
                Dial.sprite = d;
                Dial.rectTransform.sizeDelta = d.rect.size * scale;
                Dial.enabled = true;
                Size = d.rect.height * scale;
            }
            if (!string.IsNullOrEmpty(spec.needle) && sprites.TryGetValue(spec.needle, out var n))
            {
                Needle.sprite = n;
                var rt = Needle.rectTransform;
                rt.sizeDelta = n.rect.size * scale;
                rt.pivot = new Vector2(n.rect.width > 0f ? n.pivot.x / n.rect.width : 0.5f, n.rect.height > 0f ? n.pivot.y / n.rect.height : 0.5f);
                rt.anchorMin = rt.anchorMax = spec.hub;
                rt.anchoredPosition = Vector2.zero;
                Needle.enabled = true;
            }
            Caption.rectTransform.anchoredPosition = Dial.rectTransform.anchoredPosition + new Vector2(0f, -Size - 2f);
            Caption.rectTransform.sizeDelta = new Vector2(Dial.rectTransform.sizeDelta.x, 20f);
            Caption.enabled = Ready;
            needleColor = Needle.color;
            Motion.Reset();
        }

        /// <summary>One frame: true on a 12 Hz tick, when the needle was redrawn.</summary>
        public bool Step(float time, Color dangerColor)
        {
            if (!Motion.Step(Target, time)) return false;
            if (Spec == null) return true;
            float a = Spec.Angle(Motion.Shown) + Motion.Wobble * Spec.SweepSign;
            Needle.rectTransform.localEulerAngles = new Vector3(0f, 0f, a);
            bool d = DangerTint && Spec.InDanger(Motion.Shown);
            if (d != danger) { danger = d; Needle.color = d ? dangerColor : needleColor; }
            return true;
        }
    }
}
