using UnityEngine;
using UnityEngine.UI;

namespace Meridian.UI
{
    /// <summary>
    /// U-195 (D-183, the owner's 0.6.0 playtest: "the stroke feels like something"): a dug material's icon pops where the pack took it and
    /// flies to the PACK readout in 0.35 s; as it lands the readout bumps 10 % (SideHud.BumpPack) and Arrived is raised (the tick sound).
    /// Eight pooled Images on the HUD canvas, positions in the HUD's top-centre units (as the readout's own); when all are flying the oldest
    /// lands at once. Nothing allocates per flight or per frame.
    /// </summary>
    public sealed class HudPackFlight : MonoBehaviour
    {
        public const int Slots = 8;
        /// <summary>The flight's length (s), the icon's size (HUD units), its pop at the start, its size on landing, the rise at mid-flight.</summary>
        public const float Seconds = 0.35f, IconPx = 44f, PopScale = 1.3f, EndScale = 0.6f, RisePx = 28f;

        public SideHud hud;
        /// <summary>Icons in the air now; flights landed since load.</summary>
        public int InFlight { get; private set; }
        public int Landed { get; private set; }
        /// <summary>The last flight's start (HUD top-centre units) and where its icon was drawn on landing (the same units, and world).</summary>
        public Vector2 LastFrom { get; private set; }
        public Vector2 LastEnd { get; private set; }
        public Vector3 LastEndWorld { get; private set; }
        /// <summary>Raised as an icon lands in the readout.</summary>
        public event System.Action Arrived;

        readonly Image[] icons = new Image[Slots];
        readonly float[] started = new float[Slots];
        readonly Vector2[] from = new Vector2[Slots];
        readonly bool[] busy = new bool[Slots];
        RectTransform canvasRect;

        public void Build(Transform root)
        {
            canvasRect = root as RectTransform;
            var top = new Vector2(0.5f, 1f);
            for (int i = 0; i < Slots; i++)
            {
                var img = UiKit.Panel(root, "PackFlight" + i, top, Vector2.zero, new Vector2(IconPx, IconPx), Color.white);
                img.rectTransform.pivot = new Vector2(0.5f, 0.5f);
                img.preserveAspect = true;
                img.enabled = false;
                icons[i] = img;
            }
        }

        /// <summary>A screen point (pixels) in the HUD's top-centre units.</summary>
        public Vector2 FromScreen(Vector2 screen)
        {
            if (canvasRect == null) return Vector2.zero;
            RectTransformUtility.ScreenPointToLocalPointInRectangle(canvasRect, screen, null, out var local);
            var r = canvasRect.rect; // local is measured from the canvas's pivot; the top-centre anchor sits at (centre x, top y)
            return new Vector2(local.x - r.center.x, local.y - r.yMax);
        }

        /// <summary>Starts `icon` from `screen` (pixels) toward the PACK readout. False with no icon or before Build.</summary>
        public bool Fly(Sprite icon, Vector2 screen)
        {
            if (icon == null || canvasRect == null) return false;
            int pick = 0;
            float oldest = float.MaxValue;
            for (int i = 0; i < Slots; i++)
            {
                if (!busy[i]) { pick = i; oldest = float.MinValue; break; }
                if (started[i] < oldest) { oldest = started[i]; pick = i; }
            }
            if (busy[pick]) { Place(pick, 1f); Land(pick); } // all eight in the air: the oldest lands now, its bump and tick with it
            busy[pick] = true;
            InFlight++;
            started[pick] = Time.time;
            from[pick] = LastFrom = FromScreen(screen);
            icons[pick].sprite = icon;
            icons[pick].enabled = true;
            Place(pick, 0f);
            return true;
        }

        /// <summary>The icon at k of its flight (0..1): eased from its start to the readout's centre with a small rise, popping then shrinking.</summary>
        void Place(int i, float k)
        {
            float e = k * k * (3f - 2f * k);
            var p = Vector2.Lerp(from[i], SideHud.PackCentre, e);
            p.y += RisePx * Mathf.Sin(k * Mathf.PI);
            float s = k < 0.2f ? Mathf.Lerp(PopScale, 1f, k / 0.2f) : Mathf.Lerp(1f, EndScale, (k - 0.2f) / 0.8f);
            var rt = icons[i].rectTransform;
            rt.anchoredPosition = p;
            rt.localScale = new Vector3(s, s, 1f);
        }

        void Land(int i)
        {
            busy[i] = false;
            InFlight--;
            LastEnd = icons[i].rectTransform.anchoredPosition;
            LastEndWorld = icons[i].rectTransform.position;
            icons[i].enabled = false;
            Landed++;
            if (hud != null) hud.BumpPack();
            Arrived?.Invoke();
        }

        void Update()
        {
            if (InFlight == 0) return;
            float now = Time.time;
            for (int i = 0; i < Slots; i++)
            {
                if (!busy[i]) continue;
                float k = (now - started[i]) / Seconds;
                if (k >= 1f) { Place(i, 1f); Land(i); }
                else Place(i, k);
            }
        }
    }
}
