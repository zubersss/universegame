using System.Collections.Generic;
using Meridian.Art;
using Meridian.Rendering;
using Meridian.Rig;
using UnityEngine;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Player
{
    /// <summary>
    /// U-183 (B-205): the jetpack upgrades on the surveyor's back. Mk1 is the float pack as drawn; Mk2 (asc_jet_2) / Mk3 (asc_jet_3) draw
    /// props/rig/jetpack_mk&lt;n&gt; over the drawn surveyor at the frame's back socket (the json's back_socket per sheet frame: [x, z] m from
    /// the feet, the pack's swing, the body's squash; null hides it), mirrored when the surveyor faces left. A child of the cartoon surveyor's
    /// squash root, so its runtime squash carries the pack too. Nothing per frame but a transform write when the drawn frame changes.
    /// </summary>
    public sealed class JetpackOverlay : MonoBehaviour
    {
        public Meridian.View2D.SpriteCharacterView view;
        public SpriteRenderer Overlay { get; private set; }
        public int Mk { get; private set; } = 1;
        /// <summary>The surveyor's sheet frame the pack sits on now (-1: none).</summary>
        public int FrameIndex { get; private set; } = -1;
        int version = -1, loadingMk;
        AsyncOperationHandle<IList<Sprite>> handle;
        Sprite lastSprite;
        bool lastFlip;
        static readonly Dictionary<Sprite, int> frameOf = new Dictionary<Sprite, int>(128);

        /// <summary>The sheet's frame index of a drawn sprite (its name ends _&lt;n&gt;), or -1.</summary>
        public static int FrameOf(Sprite s)
        {
            if (s == null) return -1;
            if (frameOf.TryGetValue(s, out int n)) return n;
            n = -1;
            int u = s.name.LastIndexOf('_');
            if (u >= 0 && int.TryParse(s.name.Substring(u + 1), out int k)) n = k;
            frameOf[s] = n;
            return n;
        }

        static readonly Dictionary<Sprite, bool> sheetB = new Dictionary<Sprite, bool>(128);

        /// <summary>U-176: whether a drawn frame is side_b's (D-121: side_b's clips play in the side sheet's controller, so the view's key stays
        /// the side sheet's; the frame's sprite names its sheet: side_b_&lt;i&gt;).</summary>
        public static bool SheetB(Sprite s)
        {
            if (s == null) return false;
            if (sheetB.TryGetValue(s, out bool b)) return b;
            b = s.name.StartsWith("side_b_", System.StringComparison.Ordinal);
            sheetB[s] = b;
            return b;
        }

        /// <summary>The socket table for the drawn frame's sheet: back_socket for the side sheet, back_socket_b for side_b (from the Mk2 json:
        /// the socket is the surveyor's, the same for every pack).</summary>
        public static ArtMaterials.ArtSocket SocketTable(Sprite drawn) =>
            ArtMaterials.SocketFor("props/rig/jetpack_mk2", SheetB(drawn) ? "back_socket_b" : "back_socket");

        /// <summary>Where the pack sits now in the world (the Beam's cable runs there): the drawn frame's back socket, else 0.33 m behind and
        /// 0.93 m up from the feet.</summary>
        public static Vector2 PackWorld(Meridian.View2D.SpriteCharacterView v, Transform feet, bool left)
        {
            if (v != null && v.Renderer != null)
            {
                var table = SocketTable(v.Renderer.sprite);
                int i = FrameOf(v.Renderer.sprite);
                if (table != null && table.Has(i))
                {
                    bool flip = v.Renderer.flipX;
                    var local = new Vector3(flip ? -table[i, 0] : table[i, 0], table[i, 1], 0f);
                    return v.SquashRoot.TransformPoint(local);
                }
            }
            var p = (Vector2)feet.position;
            return p + new Vector2(left ? 0.33f : -0.33f, 0.93f);
        }

        void Awake()
        {
            var go = new GameObject("JetpackMk");
            Overlay = go.AddComponent<SpriteRenderer>();
            Overlay.enabled = false;
        }

        void Start()
        {
            if (view != null && view.SquashRoot != null)
            {
                Overlay.transform.SetParent(view.SquashRoot, false);
                Overlay.sortingOrder = view.sortingOrder + 1; // over the drawn surveyor, its float pack under it
            }
        }

        void OnDestroy() { if (handle.IsValid()) ArtLoad.Release(handle); }

        void LateUpdate()
        {
            if (view == null || view.Renderer == null) return;
            if (version != Meridian.Progress.SkillStats.Version)
            {
                version = Meridian.Progress.SkillStats.Version;
                int want = RigLooks.JetpackMk(RigLooks.Bought);
                if (want != Mk) Load(want);
            }
            var sprite = view.Renderer.sprite;
            bool flip = view.Renderer.flipX;
            if (Mk < 2 || Overlay.sprite == null || !view.Renderer.enabled) { Show(false); return; }
            if (sprite == lastSprite && flip == lastFlip && Overlay.enabled) return;
            lastSprite = sprite; lastFlip = flip;
            var table = SocketTable(view.Renderer.sprite);
            FrameIndex = FrameOf(sprite);
            if (table == null || !table.Has(FrameIndex)) { Show(false); return; }
            int i = FrameIndex;
            float x = table[i, 0], z = table[i, 1], swing = table[i, 2] * Mathf.Rad2Deg;
            var t = Overlay.transform;
            t.localPosition = new Vector3(flip ? -x : x, z, -0.001f);
            t.localRotation = Quaternion.Euler(0f, 0f, flip ? -swing : swing);
            t.localScale = new Vector3(table.stride > 3 ? table[i, 3] : 1f, table.stride > 4 ? table[i, 4] : 1f, 1f);
            Overlay.flipX = flip;
            Show(true);
        }

        void Show(bool on) { if (Overlay.enabled != on) Overlay.enabled = on; }

        void Load(int mk)
        {
            Mk = mk;
            if (handle.IsValid()) ArtLoad.Release(handle);
            Overlay.sprite = null;
            lastSprite = null;
            var key = RigLooks.JetpackKey(mk);
            if (key == null) { handle = default; return; }
            loadingMk = mk;
            handle = ArtLoad.Asset<IList<Sprite>>(key);
            handle.Completed += op =>
            {
                if (this == null || loadingMk != mk || op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                Overlay.sprite = op.Result[0];
                var mat = ArtMaterials.MaterialFor(key);
                if (mat != null) Overlay.sharedMaterial = mat;
                lastSprite = null;
            };
        }
    }
}
