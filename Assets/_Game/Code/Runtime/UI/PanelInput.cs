using System.Collections.Generic;
using UnityEngine.InputSystem;

namespace Meridian.UI
{
    /// <summary>
    /// U-134: while an in-game panel (inventory, catalogue, crafting) is open the surveyor stands still: every on-foot action except the
    /// panels' own keys (Tab, N, B) is held off, and comes back when the last panel closes. The open panel re-holds it each frame, because
    /// a resume from the pause menu re-enables whole maps. No allocation per frame (a for loop over the map's actions).
    /// </summary>
    public static class PanelInput
    {
        /// <summary>The on-foot actions that stay live while a panel is open: the panels' own toggles.</summary>
        public static readonly string[] PanelKeys = { "Inventory", "Catalogue", "BuildMenu", "Sell" };

        static readonly List<InputAction> held = new List<InputAction>(24);
        static readonly HashSet<object> openers = new HashSet<object>();
        static InputActionMap heldMap;

        /// <summary>True while any panel holds the surveyor.</summary>
        public static bool Holding => openers.Count > 0;

        public static bool IsPanelKey(string action)
        {
            for (int i = 0; i < PanelKeys.Length; i++) if (PanelKeys[i] == action) return true;
            return false;
        }

        /// <summary>A panel opened over the on-foot map `foot`.</summary>
        public static void Open(object panel, InputActionMap foot)
        {
            if (panel == null || foot == null) return;
            openers.Add(panel);
            Hold(foot);
        }

        /// <summary>A panel closed (or went away); the last one gives the held actions back, if their map is still live.</summary>
        public static void Close(object panel)
        {
            if (panel == null || !openers.Remove(panel) || openers.Count > 0) return;
            bool live = heldMap != null && heldMap.asset != null && heldMap.enabled; // a panel key is still on: the surveyor is on foot, no menu up
            if (live) for (int i = 0; i < held.Count; i++) held[i].Enable();
            held.Clear();
            heldMap = null;
        }

        /// <summary>Holds every enabled on-foot action but the panel keys off (called on open and each frame while a panel is open).</summary>
        public static void Hold(InputActionMap foot)
        {
            if (foot == null || openers.Count == 0) return;
            if (heldMap != foot) { held.Clear(); heldMap = foot; }
            var actions = foot.actions;
            for (int i = 0; i < actions.Count; i++)
            {
                var a = actions[i];
                if (!a.enabled || IsPanelKey(a.name)) continue;
                a.Disable();
                if (!held.Contains(a)) held.Add(a);
            }
        }
    }
}
