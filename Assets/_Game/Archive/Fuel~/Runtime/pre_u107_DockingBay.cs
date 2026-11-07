using Meridian.Art;
using System.Collections.Generic;
using Meridian.Core;
using Meridian.Items;
using Meridian.Player;
using Meridian.Space;
using Meridian.UI;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.InputSystem;
using UnityEngine.ResourceManagement.AsyncOperations;
using UnityEngine.UI;

namespace Meridian.Trade
{
    /// <summary>
    /// U-052: docking and the docking-bay interior. Near a Waystation and slow, F docks: the ship holds still
    /// and the bay opens (backgrounds/waystation layers, B-039) with the Halcyon market on the U-058 panel
    /// style: goods (buy/sell in Scrip at this station's prices), refuel and repair, cargo contracts
    /// (accept here, deliver at the destination), and UNDOCK. Lives on the Space root (off while on a planet).
    /// </summary>
    public sealed class DockingBay : MonoBehaviour
    {
        public SpaceShip ship;
        public Waystation At { get; private set; }
        public bool Docked => At != null;
        public string LastMessage { get; private set; } = "";
        public static bool AnyOpen { get; private set; }

        GameObject root, prompt;
        Text promptText, title, scripText, message;
        InputAction dock;
        readonly List<AsyncOperationHandle<Texture2D>> handles = new List<AsyncOperationHandle<Texture2D>>();
        readonly List<(string item, Text price, Text held, Image icon, Button buy, Button sell)> goods = new List<(string, Text, Text, Image, Button, Button)>();
        readonly List<(Text label, Button button)> contractRows = new List<(Text, Button)>();
        Button refuel, repair;
        Text refuelText, repairText;
        bool savedExternal;

        GameState State => GameState.Instance;

        void Start()
        {
            if (ship == null) ship = GetComponentInChildren<SpaceShip>(true);
            var world = GetComponentInChildren<SpaceWorld>(true) ?? (ship != null ? ship.world : null);
            if (world != null)
                foreach (var p in Market.Stations) Waystation.Create(transform, p, world);
            Build();
            var actions = ship != null ? ship.actions : null;
            if (actions != null)
            {
                dock = actions.FindActionMap(MeridianInput.ShipTop, true).FindAction("Enter");
                if (dock != null) dock.performed += OnDockKey;
            }
            ItemIcons.Loaded += FillIcons;
        }

        void OnDestroy()
        {
            if (dock != null) dock.performed -= OnDockKey;
            ItemIcons.Loaded -= FillIcons;
            foreach (var h in handles) if (h.IsValid()) global::Meridian.Art.ArtLoad.Release(h);
            if (Docked) AnyOpen = false;
        }

        void OnDisable() { if (Docked) Undock(); }

        void OnDockKey(InputAction.CallbackContext _)
        {
            if (Docked || ship == null || !isActiveAndEnabled) return;
            var w = Waystation.DockableFrom(ship.Position, ship.Velocity);
            if (w != null) Dock(w.planet);
        }

        void Update()
        {
            if (ship == null) return;
            if (Docked) { ship.Velocity = Vector2.zero; return; }
            var near = Waystation.DockableFrom(ship.Position, ship.Velocity);
            bool show = near != null;
            if (prompt.activeSelf != show) prompt.SetActive(show);
            if (show) promptText.text = $"F  DOCK AT {near.planet.ToUpperInvariant()} WAYSTATION";
        }

        /// <summary>Docks at a station (the F key, tests). The ship holds still until UNDOCK.</summary>
        public bool Dock(string planet)
        {
            if (Docked) return false;
            Waystation w = null;
            foreach (var s in Waystation.All) if (s.planet == planet) w = s;
            if (w == null) return false;
            At = w;
            savedExternal = ship.externalInput;
            ship.externalInput = true;
            ship.intent = default;
            ship.Velocity = Vector2.zero;
            ship.Position = (Vector2)w.transform.position + new Vector2(0f, -Waystation.Size * 0.5f);
            root.SetActive(true);
            prompt.SetActive(false);
            AnyOpen = true;
            title.text = $"{planet.ToUpperInvariant()} WAYSTATION  ·  HALCYON FREIGHT";
            BuildContracts();
            FillIcons();
            Refresh();
            return true;
        }

        public void Undock()
        {
            if (!Docked) return;
            At = null;
            root.SetActive(false);
            AnyOpen = false;
            ship.externalInput = savedExternal;
            ship.Velocity = Vector2.zero;
        }

        // ---------- market actions (buttons and tests) ----------

        string Station => At != null ? At.planet : "";

        public bool SellItem(string item, int count)
        {
            int scrip = State.scrip;
            bool ok = Docked && Market.Sell(Station, item, count, State.inventory, ref scrip);
            State.scrip = scrip;
            Say(ok ? $"Sold {count} × {Name(item)} for {Market.SellPrice(Station, item) * count} Scrip" : $"Can't sell {Name(item)}");
            return ok;
        }

        public bool BuyItem(string item, int count)
        {
            int scrip = State.scrip;
            bool ok = Docked && Market.Buy(Station, item, count, State.inventory, ref scrip);
            State.scrip = scrip;
            Say(ok ? $"Bought {count} × {Name(item)}" : $"Can't buy {Name(item)}");
            return ok;
        }

        public float Refuel()
        {
            if (!Docked) return 0f;
            int scrip = State.scrip; float fuel = State.fuel;
            float units = Market.Refuel(Station, ref fuel, State.tankCapacity, ref scrip);
            State.fuel = fuel; State.scrip = scrip;
            Say(units > 0f ? $"Refuelled {units:F0} units" : "Tank full (or no Scrip)");
            return units;
        }

        public float Repair()
        {
            if (!Docked) return 0f;
            int scrip = State.scrip; float hull = State.hull;
            float pts = Market.Repair(Station, ref hull, 100f, ref scrip);
            State.hull = hull; State.scrip = scrip;
            Say(pts > 0f ? $"Repaired {pts:F0} hull points" : "Hull sound (or no Scrip)");
            return pts;
        }

        /// <summary>Accepts an offer posted here (once).</summary>
        public bool Accept(string contractId)
        {
            if (!Docked || State.contracts.Exists(c => c.id == contractId)) return false;
            var offer = Market.OffersAt(Station).Find(c => c.id == contractId);
            if (offer == null) return false;
            offer.accepted = true;
            State.contracts.Add(offer);
            Say($"Accepted: {offer.count} × {Name(offer.item)} to {offer.to.ToUpperInvariant()} for {offer.reward} Scrip");
            BuildContracts();
            return true;
        }

        public bool Deliver(string contractId)
        {
            var c = State.contracts.Find(k => k.id == contractId);
            int scrip = State.scrip;
            bool ok = c != null && Docked && Market.Deliver(c, Station, State.inventory, ref scrip);
            State.scrip = scrip;
            Say(ok ? $"Delivered: +{c.reward} Scrip" : "Nothing to deliver here");
            BuildContracts();
            return ok;
        }

        void Say(string s)
        {
            LastMessage = s;
            if (message != null) message.text = s;
            Refresh();
        }

        static string Name(string key) => ItemRegistry.Get(key)?.name ?? key;

        // ---------- UI ----------

        void Build()
        {
            var theme = UiTheme.Active;
            var canvas = UiKit.Canvas(transform, "DockingCanvas", 112);
            var center = new Vector2(0.5f, 0.5f);

            prompt = UiKit.Panel(canvas.transform, "DockPrompt", new Vector2(0.5f, 0f), new Vector2(0f, 120f), new Vector2(520f, 44f), UiKit.PanelFill).gameObject;
            promptText = UiKit.Text(prompt.transform, "Text", center, Vector2.zero, new Vector2(500f, 40f), 18, true, TextAnchor.MiddleCenter, theme.text);
            prompt.SetActive(false);

            // The bay: the interior art fills the screen; the market panel stands on the right.
            root = UiKit.Rect(canvas.transform, "DockingBay", center, Vector2.zero, new Vector2(1920f, 1080f)).gameObject;
            root.AddComponent<Image>().color = UiKit.PanelFill; // behind the art until it loads
            for (int i = 0; i < 3; i++)
            {
                var layer = UiKit.Rect(root.transform, "BayLayer" + i, center, Vector2.zero, new Vector2(1920f, 1080f)).gameObject.AddComponent<RawImage>();
                layer.enabled = false;
                LoadLayer(i, layer);
            }
            var frame = UiKit.Panel(root.transform, "MarketFrame", new Vector2(1f, 0.5f), new Vector2(-40f, 0f), new Vector2(964f, 984f), UiTheme.Accent(null) * new Color(1f, 1f, 1f, 0.6f));
            frame.rectTransform.pivot = new Vector2(1f, 0.5f);
            var panel = UiKit.Panel(frame.transform, "Market", center, Vector2.zero, new Vector2(960f, 980f), UiKit.PanelFill);
            panel.raycastTarget = true;
            var tl = new Vector2(0f, 1f);
            title = UiKit.Text(panel.transform, "Title", tl, new Vector2(24f, -30f), new Vector2(700f, 28f), 20, true, TextAnchor.MiddleLeft, theme.text);
            scripText = UiKit.Text(panel.transform, "Scrip", new Vector2(1f, 1f), new Vector2(-24f, -30f), new Vector2(240f, 28f), 20, true, TextAnchor.MiddleRight, UiTheme.Accent(null));
            scripText.rectTransform.pivot = new Vector2(1f, 0.5f);
            message = UiKit.Text(panel.transform, "Message", new Vector2(0f, 0f), new Vector2(24f, 24f), new Vector2(700f, 24f), 15, false, TextAnchor.MiddleLeft, theme.text);
            var undock = UiKit.ActionButton(panel.transform, "UNDOCK", new Vector2(1f, 0f), new Vector2(-24f, 16f), new Vector2(150f, 36f), Undock);
            ((RectTransform)undock.transform).pivot = new Vector2(1f, 0f);

            UiKit.Text(panel.transform, "GoodsTitle", tl, new Vector2(24f, -70f), new Vector2(400f, 22f), 15, true, TextAnchor.MiddleLeft, theme.label).text = "GOODS          BUY / SELL (SCRIP)        HELD";
            int row = 0;
            foreach (var item in Market.Goods)
            {
                float y = -100f - row * 36f;
                var icon = UiKit.Panel(panel.transform, "Icon_" + item, tl, new Vector2(24f, y), new Vector2(28f, 28f), Color.white);
                icon.rectTransform.pivot = tl; icon.preserveAspect = true; icon.enabled = false;
                UiKit.Text(panel.transform, "Name_" + item, tl, new Vector2(60f, y - 4f), new Vector2(200f, 26f), 15, true, TextAnchor.MiddleLeft, theme.text).text = Name(item);
                var price = UiKit.Text(panel.transform, "Price_" + item, tl, new Vector2(270f, y - 4f), new Vector2(150f, 26f), 15, false, TextAnchor.MiddleLeft, theme.text);
                var held = UiKit.Text(panel.transform, "Held_" + item, tl, new Vector2(430f, y - 4f), new Vector2(60f, 26f), 15, false, TextAnchor.MiddleLeft, theme.label);
                string it = item;
                var buy = UiKit.ActionButton(panel.transform, "BUY", tl, new Vector2(500f, y), new Vector2(84f, 28f), () => BuyItem(it, 1));
                var sell = UiKit.ActionButton(panel.transform, "SELL", tl, new Vector2(592f, y), new Vector2(84f, 28f), () => SellItem(it, 1));
                goods.Add((item, price, held, icon, buy, sell));
                row++;
            }

            UiKit.Text(panel.transform, "ServicesTitle", tl, new Vector2(700f, -70f), new Vector2(240f, 22f), 15, true, TextAnchor.MiddleLeft, theme.label).text = "SERVICES";
            refuel = UiKit.ActionButton(panel.transform, "REFUEL", tl, new Vector2(700f, -100f), new Vector2(236f, 34f), () => Refuel());
            refuelText = UiKit.Text(panel.transform, "RefuelCost", tl, new Vector2(700f, -138f), new Vector2(236f, 22f), 13, false, TextAnchor.MiddleLeft, theme.label);
            repair = UiKit.ActionButton(panel.transform, "REPAIR", tl, new Vector2(700f, -168f), new Vector2(236f, 34f), () => Repair());
            repairText = UiKit.Text(panel.transform, "RepairCost", tl, new Vector2(700f, -206f), new Vector2(236f, 22f), 13, false, TextAnchor.MiddleLeft, theme.label);
            UiKit.Text(panel.transform, "ContractsTitle", tl, new Vector2(700f, -250f), new Vector2(240f, 22f), 15, true, TextAnchor.MiddleLeft, theme.label).text = "CARGO CONTRACTS";
            for (int i = 0; i < 4; i++)
            {
                float y = -282f - i * 112f;
                var label = UiKit.Text(panel.transform, "Contract" + i, tl, new Vector2(700f, y), new Vector2(236f, 64f), 13, false, TextAnchor.UpperLeft, theme.text);
                label.horizontalOverflow = HorizontalWrapMode.Wrap;
                var b = UiKit.ActionButton(panel.transform, "ACCEPT", tl, new Vector2(700f, y - 66f), new Vector2(236f, 32f), () => { });
                contractRows.Add((label, b));
            }
            root.SetActive(false);
        }

        void LoadLayer(int i, RawImage target)
        {
            var h = ArtLoad.Asset<Texture2D>($"backgrounds/waystation/layer{i}");
            handles.Add(h);
            h.Completed += op =>
            {
                if (target == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null) return;
                target.texture = op.Result;
                target.enabled = true;
            };
        }

        void FillIcons()
        {
            foreach (var g in goods)
            {
                var sp = ItemIcons.Get(g.item);
                g.icon.sprite = sp;
                g.icon.enabled = sp != null;
            }
        }

        /// <summary>The contract rows: offers posted here, then accepted contracts deliverable here.</summary>
        void BuildContracts()
        {
            var list = new List<(Contract c, bool deliver)>();
            foreach (var o in Market.OffersAt(Station))
                if (!State.contracts.Exists(c => c.id == o.id)) list.Add((o, false));
            foreach (var c in State.contracts)
                if (c.accepted && !c.done && c.to == Station) list.Add((c, true));
            for (int i = 0; i < contractRows.Count; i++)
            {
                var (label, b) = contractRows[i];
                b.onClick.RemoveAllListeners();
                bool on = i < list.Count;
                label.gameObject.SetActive(on);
                b.gameObject.SetActive(on);
                if (!on) continue;
                var (c, deliver) = list[i];
                label.text = $"{c.count} × {Name(c.item)}\n{c.from.ToUpperInvariant()} → {c.to.ToUpperInvariant()}   {c.reward} Scrip";
                b.GetComponentInChildren<Text>().text = deliver ? "DELIVER" : "ACCEPT";
                string id = c.id;
                if (deliver) b.onClick.AddListener(() => Deliver(id)); else b.onClick.AddListener(() => Accept(id));
                var def = ItemRegistry.Get(c.item);
                UiKit.SetAction(b, !deliver || (def != null && State.inventory.Count(def.id) >= c.count));
            }
        }

        void Refresh()
        {
            if (!Docked || State == null) return;
            scripText.text = $"{State.scrip} SCRIP";
            foreach (var g in goods)
            {
                var def = ItemRegistry.Get(g.item);
                int held = def != null ? State.inventory.Count(def.id) : 0;
                g.price.text = $"{Market.BuyPrice(Station, g.item)} / {Market.SellPrice(Station, g.item)}";
                g.held.text = held.ToString();
                UiKit.SetAction(g.buy, State.scrip >= Market.BuyPrice(Station, g.item));
                UiKit.SetAction(g.sell, held > 0);
            }
            float fuelUnits = Mathf.Max(0f, State.tankCapacity - State.fuel), hullPts = Mathf.Max(0f, 100f - State.hull);
            refuelText.text = $"{fuelUnits:F0} units × {Market.FuelPrice(Station)} Scrip";
            repairText.text = $"{hullPts:F0} points × {Market.RepairPrice(Station)} Scrip";
            UiKit.SetAction(refuel, fuelUnits >= 1f && State.scrip >= Market.FuelPrice(Station));
            UiKit.SetAction(repair, hullPts >= 1f && State.scrip >= Market.RepairPrice(Station));
            BuildContracts();
        }
    }
}
