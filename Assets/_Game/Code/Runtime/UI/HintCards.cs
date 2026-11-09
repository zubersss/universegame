using System.Collections.Generic;
using Meridian.Core;
using Meridian.Mining;
using Meridian.Player;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace Meridian.UI
{
    /// <summary>
    /// U-185 (D1; B-213's cards): the first hour's hints, each shown once, in context, then never again (GameState.hintsSeen, saved):
    /// DIG DOWN on landing at Earth's camp; THE SURFACE LINE the first time the feet cross below it; PACK FULL on the first refused
    /// pickup and CLIMB BACK UP right after it; SELL the first time topside with something sellable in the pack; THE SKILL TREE after the
    /// first sale. A card sits clear of the surveyor (up under the depth readout, else the lower centre) for ShowSeconds or until its action is done (the first dig, topside, the Sell
    /// panel, the tree), B-213's paper arrow aimed at the HUD element it names, the current key lettered on its key cap. Nothing shows
    /// during a transition, a menu or a panel (a trigger waits for them); Settings' "Show hints" off shows none. Lives beside SideHud on
    /// its canvas (hidden with the HUD); a few comparisons a frame.
    /// </summary>
    public sealed class HintCards : MonoBehaviour
    {
        public const float ShowSeconds = 6f, Scale = 1.25f;
        /// <summary>LEAD (u185 review): the card stays clear of the surveyor. Up top, under the depth readout and the PACK FULL cue (clear of
        /// the gauges left and the site list right); down at the lower centre only while the surveyor is up there. Canvas px from the edge.</summary>
        public const float TopY = -96f, BottomY = 150f;
        /// <summary>The surveyor's box for the overlap test: the capsule plus the pack and the held tool (m).</summary>
        public const float BodyHalfWidth = 0.7f, BodyHeight = 2.1f;
        /// <summary>The card is in the upper band (false: the lower centre).</summary>
        public bool AtTop { get; private set; } = true;
        /// <summary>B-213's card: 320 × 200 at 1:1, the title and body rects (bottom-left px), the key cap; drawn here 440 px wide.</summary>
        public const float CardW = 440f, CardH = 200f, BaseW = 320f;
        public const string DigDown = "dig_down", SurfaceLine = "surface_line", PackFull = "pack_full", ClimbUp = "climb_up", Sell = "sell", SkillTree = "skill_tree";
        public static readonly string[] All = { DigDown, SurfaceLine, PackFull, ClimbUp, Sell, SkillTree };

        public static string Title(string id) => id switch
        {
            DigDown => "DIG DOWN", SurfaceLine => "THE SURFACE LINE", PackFull => "PACK FULL",
            ClimbUp => "CLIMB BACK UP", Sell => "SELL", SkillTree => "THE SKILL TREE", _ => "",
        };

        /// <summary>The card's words; `key` is the bound key the card names (lettered on its cap too).</summary>
        public static string Body(string id, string key) => id switch
        {
            DigDown => "Hold the left button: the Beam digs. Go down: deeper ground pays more.",
            SurfaceLine => "Below this line you are on a dig run. Fill your pack, then climb back above it to sell.",
            PackFull => "Your pack is full. What you dig now stays on the ground.",
            ClimbUp => $"Hold {key} to fly the jetpack up past the Surface Line. A heavy pack climbs slower.",
            Sell => $"Topside with a haul: press {key} to sell it for Scrip.",
            SkillTree => $"Spend your Scrip on upgrades: press {key} for the Skill Tree.",
            _ => "",
        };

        /// <summary>The action whose key a card names (its key cap): none for the mouse and the two without a cap.</summary>
        static string ActionOf(string id) => id switch { ClimbUp => "Jump", Sell => "Sell", SkillTree => "Skills", _ => null };

        public SideHud hud;
        public PlayerController player;
        /// <summary>Nothing new shows while this says so (default: a transition, a menu, a panel). Tests may replace it.</summary>
        public static System.Func<bool> Blocked;
        /// <summary>The PlayMode suites switch the cards off (a fresh state on Earth would put DIG DOWN up in every test and capture);
        /// HintPlayTests and the hint capture switch them back on.</summary>
        public static bool Suppressed;

        /// <summary>The card up now (null: none), how long it has been up, and every card shown since load, in order (tests).</summary>
        public string Showing { get; private set; }
        public float ShownFor { get; private set; }
        public readonly List<string> History = new List<string>();
        public event System.Action<string> Fired;
        public Image Card => card;
        public Image Arrow => arrow;
        public Text TitleText => title;
        public Text BodyText => body;
        public Text KeyCap => keycap;
        /// <summary>The arrow tip's distance from its element's centre (canvas px; tests and captures).</summary>
        public float LastArrowGap { get; private set; }

        readonly List<string> queue = new List<string>(4);
        Image card, arrow;
        Text title, body, keycap;
        bool wasTopside = true, packRefused, dug, built;
        int scripEarnedSeen = -1;
        Meridian.Items.Inventory hookedInv;
        Meridian.Rig.RigTools hookedRig;
        Meridian.Transitions.TransitionDirector transitions;
        PlanetSideRoot side;
        Sprite arrowSprite;

        static GameState State => GameState.Instance;

        void Start() => Build();

        void Build()
        {
            if (built || hud == null) return;
            built = true;
            var root = hud.RankSlot != null ? hud.RankSlot.transform.parent : transform;
            card = UiKit.Panel(root, "HintCard", new Vector2(0.5f, 1f), new Vector2(0f, TopY), new Vector2(CardW, CardH), UiKit.Cream);
            card.rectTransform.localScale = new Vector3(Scale, Scale, 1f);
            PlaceAt(true);
            card.raycastTarget = false;
            var c = card.transform;
            // B-213's rects (bottom-left px of the 320-px card), the middle stretched to CardW
            float grow = CardW - BaseW;
            title = Lettering(c, "Title", 42f, 152f, 236f + grow, 26f, 22, TextAnchor.MiddleLeft);
            title.fontStyle = FontStyle.Normal;
            title.font = UiTheme.Active.TitleFace;
            body = Lettering(c, "Body", 156f, 24f, 140f + grow, 114f, 22, TextAnchor.UpperLeft);
            body.horizontalOverflow = HorizontalWrapMode.Wrap;
            body.verticalOverflow = VerticalWrapMode.Truncate;
            body.fontStyle = FontStyle.Bold; // Patrick Hand's regular reads grey at this size (the HUD's tags letter bold)
            body.resizeTextForBestFit = true; body.resizeTextMinSize = Mathf.RoundToInt(15 * Scale); body.resizeTextMaxSize = Mathf.RoundToInt(22 * Scale);
            keycap = Lettering(c, "KeyCap", 104f, 31f, 38f, 35f, 18, TextAnchor.MiddleCenter);
            keycap.horizontalOverflow = HorizontalWrapMode.Wrap;
            keycap.fontStyle = FontStyle.Bold;
            keycap.resizeTextForBestFit = true; keycap.resizeTextMinSize = Mathf.RoundToInt(9 * Scale); keycap.resizeTextMaxSize = Mathf.RoundToInt(18 * Scale);
            arrow = UiKit.Panel(root, "HintArrow", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(72f, 48f), Color.white);
            arrow.rectTransform.pivot = new Vector2(0.9166667f, 0.5f); // B-213: its tip
            arrow.raycastTarget = false;
            var h = Meridian.Art.ArtLoad.Asset<IList<Sprite>>("ui/hints/arrow");
            h.Completed += op => { if (this != null && op.Status == UnityEngine.ResourceManagement.AsyncOperations.AsyncOperationStatus.Succeeded && op.Result.Count > 0) arrowSprite = op.Result[0]; };
            Hide();
        }

        Text Lettering(Transform parent, string name, float x, float y, float w, float hgt, int size, TextAnchor anchor)
        {
            // bottom-left px of the card → its centre-pivot space; lettered at the card's drawn scale and shrunk back, so it stays crisp
            var t = UiKit.Text(parent, name, new Vector2(0f, 0f), new Vector2(x + w * 0.5f, y + hgt * 0.5f), new Vector2(w, hgt) * Scale, Mathf.RoundToInt(size * Scale), false, anchor, UiKit.Ink);
            t.rectTransform.pivot = new Vector2(0.5f, 0.5f);
            t.rectTransform.anchoredPosition = new Vector2(x + w * 0.5f, y + hgt * 0.5f);
            t.rectTransform.localScale = new Vector3(1f / Scale, 1f / Scale, 1f);
            t.raycastTarget = false;
            var o = t.GetComponent<Outline>(); if (o != null) o.enabled = false;
            return t;
        }

        void PlaceAt(bool top)
        {
            AtTop = top;
            var rt = card.rectTransform;
            rt.anchorMin = rt.anchorMax = new Vector2(0.5f, top ? 1f : 0f);
            rt.pivot = new Vector2(0.5f, top ? 1f : 0f);
            rt.anchoredPosition = new Vector2(0f, top ? TopY : BottomY);
        }

        /// <summary>A UI rect on the screen (px, origin bottom-left).</summary>
        public static Rect ScreenRect(RectTransform r)
        {
            var c = new Vector3[4];
            r.GetWorldCorners(c);
            var canvas = r.GetComponentInParent<Canvas>();
            var cam = canvas != null && canvas.renderMode != RenderMode.ScreenSpaceOverlay ? canvas.worldCamera : null;
            Vector2 a = RectTransformUtility.WorldToScreenPoint(cam, c[0]), b = RectTransformUtility.WorldToScreenPoint(cam, c[2]);
            return Rect.MinMaxRect(Mathf.Min(a.x, b.x), Mathf.Min(a.y, b.y), Mathf.Max(a.x, b.x), Mathf.Max(a.y, b.y));
        }

        /// <summary>The card's rect on the screen, and the surveyor's (their box through the side camera; empty without one).</summary>
        public Rect CardScreenRect => card != null ? ScreenRect(card.rectTransform) : default;
        public Rect SurveyorScreenRect
        {
            get
            {
                if (side == null || !side.isActiveAndEnabled) side = FindAnyObjectByType<PlanetSideRoot>();
                var cam = side != null ? side.sideCamera : null;
                if (cam == null || player == null) return default;
                var f = player.Body.position;
                Vector3 a = cam.WorldToScreenPoint(new Vector3(f.x - BodyHalfWidth, f.y, 0f)), b = cam.WorldToScreenPoint(new Vector3(f.x + BodyHalfWidth, f.y + BodyHeight, 0f));
                return Rect.MinMaxRect(Mathf.Min(a.x, b.x), Mathf.Min(a.y, b.y), Mathf.Max(a.x, b.x), Mathf.Max(a.y, b.y));
            }
        }

        /// <summary>Up top unless the surveyor is there; then the lower centre (re-checked while the card is up).</summary>
        void Place()
        {
            PlaceAt(true);
            var who = SurveyorScreenRect;
            if (who.width > 0f && CardScreenRect.Overlaps(who)) PlaceAt(false);
        }

        void Hide()
        {
            Showing = null;
            if (card != null) card.gameObject.SetActive(false);
            if (arrow != null) arrow.enabled = false;
        }

        bool IsBlocked()
        {
            if (Blocked != null) return Blocked();
            if (transitions == null) transitions = FindAnyObjectByType<Meridian.Transitions.TransitionDirector>();
            return (transitions != null && transitions.Busy) || MenuController.HudHidden || InventoryPanel.AnyOpen || CraftingPanel.AnyOpen
                || CataloguePanel.AnyOpen || SellPanel.AnyOpen || SkillTreePanel.AnyOpen;
        }

        /// <summary>Asks for a hint (once ever: seen, queued or up already, nothing happens; off, nothing either).</summary>
        public void Request(string id)
        {
            var s = State;
            if (s == null || Suppressed || !GameSettings.ShowHints || s.hintsSeen.Contains(id) || Showing == id || queue.Contains(id)) return;
            queue.Add(id);
        }

        /// <summary>Puts a card up now whatever its trigger (captures); it counts as seen.</summary>
        public void Show(string id)
        {
            Build();
            var s = State;
            if (s != null) s.hintsSeen.Add(id);
            Showing = id;
            ShownFor = 0f;
            dug = false;
            History.Add(id);
            string key = KeyName(ActionOf(id));
            title.text = Title(id);
            body.text = Body(id, key);
            keycap.text = ActionOf(id) != null ? CapText(key) : "";
            card.gameObject.SetActive(true);
            Place();
            UiPaper.Apply(card, "ui/hints/" + id, _ => { title.color = body.color = keycap.color = UiKit.Ink; });
            Fired?.Invoke(id);
        }

        /// <summary>Takes the card down (its action done, its time up).</summary>
        public void Dismiss()
        {
            var was = Showing;
            Hide();
            if (was == PackFull && !Topside()) Request(ClimbUp); // CLIMB BACK UP right after PACK FULL, while still under the line
        }

        /// <summary>What fits on B-213's 38-px key cap: a letter as is, a long name shortened (SPACE → SPC).</summary>
        public static string CapText(string key) => key == "SPACE" ? "SPC" : key.Length > 4 ? key.Substring(0, 3) : key;

        string KeyName(string action)
        {
            if (action == null || player == null || player.actions == null) return action == "Jump" ? "SPACE" : "";
            var a = player.actions.FindActionMap(MeridianInput.OnFoot, true).FindAction(action, false);
            string k = a != null ? a.GetBindingDisplayString(0) : "";
            return string.IsNullOrEmpty(k) ? action : k.ToUpperInvariant();
        }

        bool Topside()
        {
            if (side == null || !side.isActiveAndEnabled) side = FindAnyObjectByType<PlanetSideRoot>();
            if (side == null || side.terrain == null || player == null || !side.terrain.SmoothGround) return true;
            return DigRun.Topside(side.terrain, player.Body.position);
        }

        void Hook()
        {
            var s = State;
            var inv = s != null ? s.inventory : null;
            if (inv != hookedInv)
            {
                if (hookedInv != null) hookedInv.Refused -= OnRefused;
                hookedInv = inv;
                if (inv != null) inv.Refused += OnRefused;
            }
            var rig = player != null ? player.GetComponent<PlayerRigInput>() : null;
            var tools = rig != null ? rig.rig : null;
            if (tools != hookedRig)
            {
                if (hookedRig != null) hookedRig.Dug -= OnDug;
                hookedRig = tools;
                if (tools != null) tools.Dug += OnDug;
            }
        }

        void OnRefused() => packRefused = true;
        void OnDug(Vector2 _) => dug = true;

        void OnDestroy()
        {
            if (hookedInv != null) hookedInv.Refused -= OnRefused;
            if (hookedRig != null) hookedRig.Dug -= OnDug;
        }

        void Update()
        {
            var s = State;
            if (s == null || player == null || hud == null) return;
            if (Suppressed) { if (Showing != null) Hide(); queue.Clear(); return; }
            Build();
            Hook();
            bool topside = Topside();
            bool d1 = side != null && side.terrain != null && side.terrain.SmoothGround;

            // the triggers (each Request is a no-op once seen)
            if (s.currentPlanet == Meridian.Planets.PlanetId.Earth && player.Grounded
                && Mathf.Abs(player.Body.position.x - Meridian.Planet.POI.PoiCatalog.SpawnCamp.CenterX) < 60f) Request(DigDown);
            if (d1 && wasTopside && !topside) Request(SurfaceLine);
            if (packRefused) { packRefused = false; Request(PackFull); }
            if (d1 && topside && !s.hintsSeen.Contains(Sell) && DigRun.PackValue(s.inventory, false) > 0) Request(Sell);
            if (scripEarnedSeen >= 0 && s.scripEarned > scripEarnedSeen) Request(SkillTree);
            scripEarnedSeen = s.scripEarned;
            wasTopside = topside;

            // the card up: its time, or its action done
            if (Showing != null)
            {
                ShownFor += Time.unscaledDeltaTime;
                bool done = Showing switch
                {
                    DigDown => dug,
                    ClimbUp => topside,
                    Sell => SellPanel.AnyOpen,
                    SkillTree => SkillTreePanel.AnyOpen,
                    _ => false,
                };
                if (done || ShownFor >= ShowSeconds || !GameSettings.ShowHints) Dismiss();
                else
                {
                    var who = SurveyorScreenRect;
                    if (who.width > 0f && CardScreenRect.Overlaps(who)) PlaceAt(!AtTop); // the surveyor moved under it: the other band
                    Aim();
                }
                return;
            }
            if (queue.Count == 0 || IsBlocked()) return;
            if (!GameSettings.ShowHints) { queue.Clear(); return; }
            var next = queue[0];
            queue.RemoveAt(0);
            if (next == ClimbUp && topside) return; // already out
            Show(next);
            Aim();
        }

        /// <summary>The arrow's tip just short of the HUD element the card names, pointing at it (none for DIG DOWN and SELL).</summary>
        void Aim()
        {
            RectTransform target = Showing switch
            {
                SurfaceLine => hud.DepthTag != null ? hud.DepthTag.rectTransform : null,
                ClimbUp => hud.DepthTag != null ? hud.DepthTag.rectTransform : null,
                PackFull => hud.PackText != null ? hud.PackText.rectTransform : null,
                SkillTree => hud.RankSlot != null ? hud.RankSlot.rectTransform : null,
                _ => null,
            };
            bool on = target != null && arrowSprite != null && target.gameObject.activeInHierarchy;
            if (arrow.enabled != on) arrow.enabled = on;
            if (!on) return;
            arrow.sprite = arrowSprite;
            // in the HUD canvas's own space (the canvas scale cancels): the element's centre and half extents, the card's top
            var space = (RectTransform)arrow.rectTransform.parent;
            Vector2 to = space.InverseTransformPoint(target.TransformPoint(target.rect.center));
            Vector2 half = (Vector2)(space.InverseTransformVector(target.TransformVector(new Vector3(target.rect.width, target.rect.height, 0f)))) * 0.5f;
            Vector2 from = space.InverseTransformPoint(card.rectTransform.TransformPoint(card.rectTransform.rect.center)); // the card's centre: only the direction counts
            var d = to - from;
            float len = d.magnitude;
            if (len < 1f) return;
            var u = d / len;
            // the tip just outside the element's edge on the card's side, 14 px off
            float reach = Mathf.Abs(u.x) * Mathf.Abs(half.x) + Mathf.Abs(u.y) * Mathf.Abs(half.y) + 14f;
            arrow.rectTransform.localPosition = to - u * Mathf.Min(reach, len - 10f);
            arrow.rectTransform.localRotation = Quaternion.Euler(0f, 0f, Mathf.Atan2(u.y, u.x) * Mathf.Rad2Deg);
            LastArrowGap = Vector2.Distance(arrow.rectTransform.localPosition, to);
        }
    }
}
