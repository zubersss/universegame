using System.Collections.Generic;
using Meridian.Art;
using Meridian.Player;
using Meridian.Progress;
using Meridian.Rig;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.InputSystem;
using UnityEngine.ResourceManagement.AsyncOperations;
using UnityEngine.ResourceManagement.ResourceLocations;
using UnityEngine.UI;

namespace Meridian.UI
{
    /// <summary>
    /// U-193 (LEAD 11:3x, D-182): the held tool on the HUD. A small paper slot under the Rank medallion shows the current Rig module's icon
    /// (icons/tools/shovel | beam | grapple | survey | builder; until B-227 draws the last four, the Skill Tree's node icon stands in), its
    /// name in ink under it (SHOVEL, BEAM MK2, GRAPPLE, SURVEY, BUILDER) and the switch keys on caps either side ("&lt; Q" / "E &gt;", as bound).
    /// It changes on a module switch and on The Beam's purchase (SkillStats.Version); hidden aboard the ship. Nothing allocates between changes.
    /// Missing keys are probed quietly (no error in the console) and remembered.
    /// </summary>
    public sealed class HudToolSlot : MonoBehaviour
    {
        public const float SlotPx = 64f, IconPx = 48f, NameW = 150f, NameH = 26f, CapW = 44f, CapH = 26f, Gap = 6f;
        /// <summary>The slot's top-left (HUD units from the top-left): under the Rank medallion (688..760, −10..−82), clear of the gust tag.</summary>
        public static readonly Vector2 SlotAt = new Vector2(692f, -92f);

        public SideHud hud;
        public RectTransform Root { get; private set; }
        public Image Slot { get; private set; }
        public Image Icon { get; private set; }
        public Text Name { get; private set; }
        public Image NameTag { get; private set; }
        public Text PrevKey { get; private set; }
        public Text NextKey { get; private set; }
        /// <summary>What the slot shows now (tests): the module, the dig tool, the icon's key (null while none is loaded).</summary>
        public RigModule ShownModule { get; private set; }
        public DigTool ShownTool { get; private set; }
        public string IconKey { get; private set; }

        PlayerRigInput input;
        int shownVersion = int.MinValue;
        string wantKey, wantStandIn;
        readonly Dictionary<string, Sprite> icons = new Dictionary<string, Sprite>();
        readonly HashSet<string> asked = new HashSet<string>(), missing = new HashSet<string>();
        readonly List<AsyncOperationHandle<IList<Sprite>>> handles = new List<AsyncOperationHandle<IList<Sprite>>>();
        // In flight: polled each frame (never a Completed callback: a load started inside another operation's callback, done at once from
        // an atlas already in memory, never reported completion to the slot, 13:05 run).
        readonly List<string> probeKeys = new List<string>(), loadKeys = new List<string>();
        readonly List<AsyncOperationHandle<IList<IResourceLocation>>> probes = new List<AsyncOperationHandle<IList<IResourceLocation>>>();
        readonly List<AsyncOperationHandle<IList<Sprite>>> loads = new List<AsyncOperationHandle<IList<Sprite>>>();

        static readonly string[] BeamNames = { "BEAM MK1", "BEAM MK2", "BEAM MK3", "BEAM MK4", "BEAM MK5" };
        static readonly string[] GrappleNames = { "GRAPPLE", "GRAPPLE MK2", "GRAPPLE MK3" };

        /// <summary>The slot's name for a module, the dig tool and the module's Mk (pure; constant strings).</summary>
        public static string NameOf(RigModule m, DigTool tool, int mk) => m switch
        {
            RigModule.Beam => tool == DigTool.Shovel ? "SHOVEL" : BeamNames[Mathf.Clamp(mk, 1, 5) - 1],
            RigModule.Grapple => GrappleNames[Mathf.Clamp(mk, 1, 3) - 1],
            RigModule.Survey => "SURVEY",
            _ => "BUILDER",
        };

        /// <summary>The tool's own icon key (B-226's shovel; B-227's four).</summary>
        public static string IconKeyOf(RigModule m, DigTool tool) => m switch
        {
            RigModule.Beam => tool == DigTool.Shovel ? "icons/tools/shovel" : "icons/tools/beam",
            RigModule.Grapple => "icons/tools/grapple",
            RigModule.Survey => "icons/tools/survey",
            _ => "icons/tools/builder",
        };

        /// <summary>The icon shown until the tool's own is drawn: the Skill Tree node that reads as it (null: none).</summary>
        public static string StandInOf(RigModule m, DigTool tool) => m switch
        {
            RigModule.Beam => tool == DigTool.Shovel ? null : "icons/nodes/dig_power_1",
            RigModule.Grapple => "icons/nodes/asc_grapple_1",
            RigModule.Survey => "icons/nodes/sur_scan_1",
            _ => "icons/nodes/asc_ladder_1",
        };

        public void Build(Transform root)
        {
            var tl = new Vector2(0f, 1f);
            Root = UiKit.Rect(root, "ToolSlot", tl, Vector2.zero, Vector2.zero);
            Slot = hud.Tag(Root, "ToolSlotPaper", tl, SlotAt, new Vector2(SlotPx, SlotPx), tl);
            Icon = UiKit.Panel(Slot.transform, "ToolIcon", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(IconPx, IconPx), Color.clear);
            Icon.preserveAspect = true;
            var top = new Vector2(0.5f, 1f);
            var namePos = SlotAt + new Vector2(SlotPx * 0.5f, -SlotPx - Gap);
            Name = UiKit.Text(Root, "ToolName", tl, namePos, new Vector2(NameW - 12f, NameH - 4f), 15, true, TextAnchor.MiddleCenter, UiKit.Ink);
            Name.rectTransform.pivot = top;
            Name.rectTransform.anchoredPosition = namePos + new Vector2(0f, -2f);
            Name.text = "";
            NameTag = hud.Tag(Root, "ToolNameTag", tl, namePos, new Vector2(NameW, NameH), top, Name);
            PrevKey = Cap("ToolPrevKey", SlotAt + new Vector2(-Gap, -SlotPx * 0.5f), new Vector2(1f, 0.5f));
            NextKey = Cap("ToolNextKey", SlotAt + new Vector2(SlotPx + Gap, -SlotPx * 0.5f), new Vector2(0f, 0.5f));
            PrevKey.text = "< Q"; NextKey.text = "E >";
            Root.gameObject.SetActive(false);
            foreach (var k in ToolKeys) Ask(k); // preloaded: a switch or The Beam's purchase shows its icon at once (89 frames late when asked then)
        }

        /// <summary>Every tool's own icon (asked at build) and its stand-in (asked once the own is known missing).</summary>
        static readonly string[] ToolKeys = { "icons/tools/shovel", "icons/tools/beam", "icons/tools/grapple", "icons/tools/survey", "icons/tools/builder" };
        static readonly string[] StandIns = { null, "icons/nodes/dig_power_1", "icons/nodes/asc_grapple_1", "icons/nodes/sur_scan_1", "icons/nodes/asc_ladder_1" };

        Text Cap(string name, Vector2 pos, Vector2 pivot)
        {
            var t = UiKit.Text(Root, name, new Vector2(0f, 1f), pos, new Vector2(CapW - 6f, CapH - 4f), 15, true, TextAnchor.MiddleCenter, UiKit.Ink);
            t.rectTransform.pivot = pivot;
            t.rectTransform.anchoredPosition = pos + new Vector2(pivot.x < 0.5f ? 3f : -3f, 0f);
            hud.Tag(Root, name + "Cap", new Vector2(0f, 1f), pos, new Vector2(CapW, CapH), pivot, t);
            return t;
        }

        /// <summary>The switch keys as bound (ModulePrev / ModuleNext), read once the player is known.</summary>
        void ReadKeys(PlayerController player)
        {
            if (player == null || player.actions == null) return;
            var foot = player.actions.FindActionMap(MeridianInput.OnFoot, false);
            if (foot == null) return;
            string prev = KeyOf(foot.FindAction("ModulePrev", false)), next = KeyOf(foot.FindAction("ModuleNext", false));
            if (prev != null) PrevKey.text = "< " + prev;
            if (next != null) NextKey.text = next + " >";
        }

        static string KeyOf(InputAction a)
        {
            string k = a != null ? a.GetBindingDisplayString(0) : null;
            return string.IsNullOrEmpty(k) ? null : HintCards.CapText(k.ToUpperInvariant());
        }

        void LateUpdate()
        {
            if (Root == null || hud == null) return;
            if (probes.Count > 0 || loads.Count > 0) Pump();
            var player = hud.player;
            if (input == null && player != null)
            {
                input = player.GetComponent<PlayerRigInput>();
                if (input != null) ReadKeys(player);
            }
            bool show = input != null && player != null && player.isActiveAndEnabled && !(hud.boarding != null && hud.boarding.Aboard);
            if (Root.gameObject.activeSelf != show) Root.gameObject.SetActive(show);
            if (!show) return;
            var tool = SkillStats.DigTool;
            if (input.module != ShownModule || tool != ShownTool || SkillStats.Version != shownVersion) Show(input.module, tool);
        }

        void Show(RigModule m, DigTool tool)
        {
            ShownModule = m; ShownTool = tool; shownVersion = SkillStats.Version;
            var bought = RigLooks.Bought;
            int mk = m == RigModule.Beam ? RigLooks.DigMk(tool, bought) : RigLooks.MkOf(m, bought);
            string n = NameOf(m, tool, mk);
            if (!ReferenceEquals(Name.text, n)) Name.text = n;
            string key = IconKeyOf(m, tool);
            if (key == wantKey && IconKey != null) return;
            wantKey = key; wantStandIn = StandInOf(m, tool);
            Icon.sprite = null; Icon.color = Color.clear; IconKey = null; // never the last tool's icon on the new one
            Refresh();
        }

        /// <summary>The wanted icon if loaded, else its stand-in once the tool's own is known missing; asks for what isn't known yet.</summary>
        void Refresh()
        {
            if (wantKey == null) return;
            if (icons.TryGetValue(wantKey, out var s)) { Set(wantKey, s); return; }
            if (!missing.Contains(wantKey)) { Ask(wantKey); return; }
            if (wantStandIn == null) return;
            if (icons.TryGetValue(wantStandIn, out s)) { Set(wantStandIn, s); return; }
            if (!missing.Contains(wantStandIn)) Ask(wantStandIn);
        }

        /// <summary>Tests: the icon bookkeeping (wanted, stand-in, asked, missing, loaded), built on request only.</summary>
        public string Describe() =>
            $"want {wantKey ?? "-"} / {wantStandIn ?? "-"}; asked [{string.Join(",", asked)}]; missing [{string.Join(",", missing)}]; loaded [{string.Join(",", icons.Keys)}]; handles {handles.Count}";

        void Set(string key, Sprite s)
        {
            Icon.sprite = s; Icon.color = Color.white; IconKey = key;
        }

        /// <summary>Starts a quiet probe for the key (untyped: a missing key logs nothing, UiPaper's probe); Pump picks it up.</summary>
        void Ask(string key)
        {
            if (!asked.Add(key)) return; // already on its way
            probeKeys.Add(key);
            probes.Add(Addressables.LoadResourceLocationsAsync(key));
        }

        /// <summary>Each frame while anything is in flight: a finished probe starts its load (or marks the key missing); a finished load
        /// keeps its sprite (or marks it missing); then the slot shows what it can. Index loops, no allocation.</summary>
        void Pump()
        {
            bool changed = false;
            for (int i = probes.Count - 1; i >= 0; i--)
            {
                var p = probes[i];
                if (p.IsValid() && !p.IsDone) continue;
                string key = probeKeys[i];
                bool exists = p.IsValid() && p.Status == AsyncOperationStatus.Succeeded && p.Result != null && p.Result.Count > 0;
                ArtLoad.Release(p);
                probes.RemoveAt(i); probeKeys.RemoveAt(i);
                if (!exists)
                {
                    missing.Add(key); changed = true;
                    int t = System.Array.IndexOf(ToolKeys, key);
                    if (t >= 0 && StandIns[t] != null) Ask(StandIns[t]); // appended past i: picked up next frame
                    continue;
                }
                var h = ArtLoad.Asset<IList<Sprite>>(key);
                handles.Add(h);
                loads.Add(h); loadKeys.Add(key);
            }
            for (int i = loads.Count - 1; i >= 0; i--)
            {
                var h = loads[i];
                if (h.IsValid() && !h.IsDone) continue;
                string key = loadKeys[i];
                loads.RemoveAt(i); loadKeys.RemoveAt(i);
                if (h.IsValid() && h.Status == AsyncOperationStatus.Succeeded && h.Result != null && h.Result.Count > 0 && h.Result[0] != null) icons[key] = h.Result[0];
                else missing.Add(key);
                changed = true;
            }
            if (changed) Refresh();
        }

        void OnDestroy()
        {
            foreach (var p in probes) ArtLoad.Release(p);
            probes.Clear(); probeKeys.Clear(); loads.Clear(); loadKeys.Clear();
            foreach (var h in handles) if (h.IsValid()) ArtLoad.Release(h);
            handles.Clear();
        }
    }
}
