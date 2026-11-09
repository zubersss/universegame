using Meridian.Art;
using Meridian.FX;
using Meridian.Rig;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Meridian.Player
{
    /// <summary>
    /// Mouse aim + Rig buttons (Bible §6/§8 v4; U-046): 1 Beam, 2 Grapple, 3 Survey, 4 Builder, Q/E cycle.
    /// Left click uses the module: the Beam digs and the Builder places while held; the Survey pulses once per
    /// press (with a cooldown); the Grapple does nothing until its task (D-087 retired the Lance from slot 2).
    /// </summary>
    public sealed class PlayerRigInput : MonoBehaviour
    {
        public const float SurveyCooldown = 1.2f;

        public RigTools rig;
        public Camera view;
        public PlayerController controller;
        public RigModule module = RigModule.Beam;

        InputAction aim, primary, secondary, prev, next;
        /// <summary>U-176: the Grapple's line (added here; PlayerController reads its reel).</summary>
        public GrappleLine Grapple { get; private set; }
        readonly InputAction[] slots = new InputAction[RigModules.Count + 1];
        float nextSurvey;

        /// <summary>The rig is in use (primary held) this frame, and where it points (U-032: aim pose, facing).</summary>
        public bool Using { get; private set; }
        public Vector2 AimWorld { get; private set; }
        public RigToolView ToolView { get; private set; }
        public FxPool Fx { get; private set; }

        /// <summary>Raised when the Survey pulses (U-054 scans what the ring covers), with the pulse centre.</summary>
        public event System.Action<Vector2> Surveyed;
        /// <summary>Whether the last Survey pulse got its scan ring from the FX pool.</summary>
        public bool LastSurveyRing { get; private set; }
        /// <summary>Survey ring radius (m): the 240 px frame at ppu 128 drawn ×2.</summary>
        public const float SurveyRadius = 3.75f;

        void Start()
        {
            if (controller == null || controller.actions == null) { enabled = false; return; }
            var foot = controller.actions.FindActionMap(MeridianInput.OnFoot, true);
            aim = foot.FindAction("Aim"); primary = foot.FindAction("RigPrimary"); secondary = foot.FindAction("RigSecondary", false);
            for (int i = 1; i <= RigModules.Count; i++) slots[i] = foot.FindAction("Module" + i);
            prev = foot.FindAction("ModulePrev"); next = foot.FindAction("ModuleNext");
            AimWorld = (Vector2)transform.position + new Vector2(2f, 1f);

            ToolView = GetComponent<RigToolView>() ?? gameObject.AddComponent<RigToolView>();
            ToolView.input = this;
            ToolView.rig = rig;
            Grapple = GetComponent<GrappleLine>() ?? gameObject.AddComponent<GrappleLine>();
            Grapple.controller = controller;
            Grapple.tool = ToolView;
            controller.grapple = Grapple;
            Fx = FindAnyObjectByType<FxPool>();
            // Load now: a first pulse would otherwise find its sheet not ready (as SideFx does).
            FxSheet.Get(ArtKeys.Fx.SurveyScan);
        }

        void Update()
        {
            for (int i = 1; i <= RigModules.Count; i++)
                if (slots[i] != null && slots[i].WasPressedThisFrame()) module = (RigModule)i;
            if (prev.WasPressedThisFrame()) module = RigModules.Next(module, -1);
            if (next.WasPressedThisFrame()) module = RigModules.Next(module, +1);

            var screen = aim.ReadValue<Vector2>();
            if (view != null && !externalAim) AimWorld = (Vector2)view.ScreenToWorldPoint(new Vector3(screen.x, screen.y, -view.transform.position.z));
            // While the inventory panel is open, clicks select slots, not tiles (U-045).
            bool uiFree = !Meridian.UI.InventoryPanel.AnyOpen && !Meridian.UI.CraftingPanel.AnyOpen && !Meridian.UI.CataloguePanel.AnyOpen && !Meridian.UI.SellPanel.AnyOpen && !Meridian.UI.SkillTreePanel.AnyOpen;
            bool pressed = (primary.IsPressed() || holdUse) && uiFree;
            // U-176: the right click: the Builder's ladder (or the winch at a shaft's mouth), the Grapple's second hook (asc_grapple_3)
            if (uiFree && rig != null && ((secondary != null && secondary.WasPressedThisFrame()) || secondaryLatched)) Secondary();
            secondaryLatched = false;
            if (Grapple != null) Grapple.held = pressed && module == RigModule.Grapple && rig != null;
            bool edge = primary.WasPressedThisFrame() || (holdUse && !heldLast);
            heldLast = holdUse;
            Using = rig != null && view != null && pressed;
            if (!Using) { strokeHeld = 0f; StrokeProgress = 0f; return; }
            // U-174 (D-174): a Beam stroke takes its time (0.25 s x the planet's and the tier's hardness / Beam power, capped at 8 s), held.
            if (module == RigModule.Beam)
            {
                float need = rig.StrokeSeconds(AimWorld);
                if (need > 0f)
                {
                    strokeHeld += Time.deltaTime;
                    StrokeProgress = Mathf.Clamp01(strokeHeld / need);
                    if (strokeHeld < need) return;
                    strokeHeld = 0f;
                }
            }
            Use(module, edge);
        }

        /// <summary>One use of a module at the current aim (tests call this directly). `pressedNow`: the press edge.</summary>
        public void Use(RigModule m, bool pressedNow)
        {
            switch (m)
            {
                case RigModule.Beam: rig.Dig(AimWorld); break;
                case RigModule.Builder: rig.Place(AimWorld); break;
                case RigModule.Grapple: if (pressedNow && Grapple != null) Grapple.Fire(AimWorld); break; // U-176: the hook flies; held, it reels
                case RigModule.Survey:
                    if (!pressedNow || Time.time < nextSurvey) break;
                    nextSurvey = Time.time + SurveyCooldown;
                    var centre = (Vector2)transform.position + new Vector2(0f, 0.9f);
                    LastSurveyRing = Fx != null && Fx.Play(ArtKeys.Fx.SurveyScan, centre, 2f);
                    Surveyed?.Invoke(centre);
                    break;
            }
        }

        float strokeHeld;
        /// <summary>U-174: the Beam stroke under way (0..1; the tool view and tests read it).</summary>
        public float StrokeProgress { get; private set; }

        /// <summary>Tests: a right click on the next frame.</summary>
        [System.NonSerialized] public bool secondaryLatched;
        /// <summary>U-176: what the last right click did (metres of ladder placed; the winch stood; a second hook thrown).</summary>
        public int LastLadderMetres { get; private set; }

        /// <summary>
        /// U-176: the right click at the aim. The Builder: the winch at a shaft's mouth (asc_winch), else ladder metres upward (asc_ladder_1);
        /// the Grapple: a second hook while the first holds (asc_grapple_3). Returns whether it did anything.
        /// </summary>
        public bool Secondary()
        {
            LastLadderMetres = 0;
            switch (module)
            {
                case RigModule.Builder:
                    if (Meridian.Building.Winch.Instance != null && Meridian.Building.Winch.Instance.Place(AimWorld)) return true;
                    if (Meridian.Building.Ladders.Instance != null) LastLadderMetres = Meridian.Building.Ladders.Instance.Place(AimWorld);
                    return LastLadderMetres > 0;
                case RigModule.Grapple:
                    return Grapple != null && Grapple.Attached && Meridian.Progress.SkillStats.GrappleAnchors >= 2 && Grapple.Fire(AimWorld);
            }
            return false;
        }

        /// <summary>Points the rig at a world point without the mouse (tests, scripted demos).</summary>
        public void AimAt(Vector2 world) { externalAim = true; AimWorld = world; }

        /// <summary>True once AimAt was used: the mouse no longer moves the aim.</summary>
        public bool externalAim;
        /// <summary>Scripted use: acts as the primary button held (its first frame is the press).</summary>
        public bool holdUse;
        bool heldLast;
    }
}
