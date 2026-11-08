using System.Collections.Generic;
using Meridian.Art;
using Meridian.Flora;
using Meridian.Rendering;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Ship
{
    /// <summary>
    /// The Pilgrim's side view. U-103 (D-111, B-122): the drawn rig `ships/pilgrim/rig` (plant `pilgrim_side`: hull, nose,
    /// three fins that are the landing legs, hatch, bell + porthole slots) built by RigBuild under the SquashRoot with its
    /// origin on the skid line, its Animator playing fin_wobble in flight (held at frame 0 on the ground), leg_flex once on
    /// touchdown and hatch_open once when the surveyor steps out; the ±35° tilt, thrust stretch and cut squash stay on the
    /// root (RocketFlight / SquashStretch). Without the rig in the catalog the pre-D-111 view runs: `ships/pilgrim/side`
    /// above 10 m, `ships/pilgrim/side_legs` at or below (D-025), replaced by the B-079 model when it loads (U-076).
    /// </summary>
    public sealed class ShipLegsView : MonoBehaviour
    {
        public const string SidePlant = "pilgrim_side";
        public const string FinWobble = "fin_wobble", LegFlex = "leg_flex", HatchOpen = "hatch_open";

        public SideShip ship;
        public SpriteRenderer target;

        public Sprite Retracted { get; private set; }
        public Sprite Deployed { get; private set; }
        public bool ShowingLegs { get; private set; }

        /// <summary>U-103: the drawn rig once built (null before, and for ever on the legacy path).</summary>
        public RigInstance Rig { get; private set; }
        public bool RigReady => Rig != null;
        /// <summary>True once the catalog answered that the rig exists (the legacy sprites and model are then never loaded).</summary>
        public bool UsesRig { get; private set; }
        /// <summary>True until the catalog answered whether the rig exists.</summary>
        public bool Probing { get; private set; } = true;
        /// <summary>Drawn: the rig, or the legacy model. Captures wait on this.</summary>
        public bool Ready => RigReady || (Model != null && Model.Ready);
        public event System.Action<RigInstance> RigBuilt;

        AsyncOperationHandle<IList<Sprite>> retractedHandle, deployedHandle;
        readonly List<AsyncOperationHandle> rigHandles = new List<AsyncOperationHandle>();
        bool applied;
        TextAsset rigJson; IList<Sprite> rigSprites; RuntimeAnimatorController rigController;
        int rigPending;
        ShipBoarding boarding;
        bool lastAboard, aboardKnown;

        void Start()
        {
            if (ship != null && target != null)
            {
                // U-103 (D-100): the squash root carries the cartoon stretch/squash along the ship's up axis (its local y, since it
                // never rotates against the hull); the sprite view, the model or the rig hang under it.
                var root = new GameObject("SquashRoot");
                root.transform.SetParent(ship.transform, false);
                SquashRoot = root.transform;
                target.transform.SetParent(SquashRoot, false);
                boarding = ship.GetComponent<ShipBoarding>();
                ship.TouchedDown += OnTouchedDown;
            }
            var probe = Addressables.LoadResourceLocationsAsync(ArtKeys.Ships.PilgrimRig + FloraRigs.JsonSuffix, typeof(TextAsset));
            probe.Completed += loc =>
            {
                bool exists = loc.Status == AsyncOperationStatus.Succeeded && loc.Result != null && loc.Result.Count > 0;
                ArtLoad.Release(loc);
                if (this == null) return;
                Probing = false;
                if (exists) LoadRig(); else LoadLegacy();
            };
        }

        void LoadLegacy()
        {
            retractedHandle = Load(ArtKeys.Ships.PilgrimSide, s => Retracted = s);
            deployedHandle = Load(ArtKeys.Ships.PilgrimSideLegs, s => Deployed = s);
            // U-076: the Pilgrim's model (B-079) replaces the side sprites once loaded. Its origin is the centre of mass, so its
            // lowest point is set on the skid line, SkidDrop below the body. U-107 (D-102): art wider than tall is the old level
            // hull, stood on its stern as a stand-in.
            // U-168: not on the cartoon path, which never shows the model (the side sprites stay as the fallback there).
            if (ship != null && target != null && SquashRoot != null && Model == null && !Meridian.View2D.CartoonStage.DrawsCurrentPlanet)
            {
                Model = ModelSwap.Attach(target, ArtKeys.Ships.PilgrimModel, SquashRoot, Vector3.zero);
                Model.Swapped += s =>
                {
                    var b = ModelSwap.ModelBounds(s.Views[0].Instance);
                    StandUpright(s.transform, b);
                };
            }
        }

        void LoadRig()
        {
            UsesRig = true;
            string key = ArtKeys.Ships.PilgrimRig;
            rigPending = 3;
            Fetch<TextAsset>(key + FloraRigs.JsonSuffix, a => rigJson = a);
            Fetch<IList<Sprite>>(key, a => rigSprites = a);
            // The controller is built by RigSetBuilder on import; without it the rig still draws (static pose) and says so.
            var probe = Addressables.LoadResourceLocationsAsync(key + FloraRigs.AnimatorSuffix, typeof(RuntimeAnimatorController));
            probe.Completed += loc =>
            {
                bool exists = loc.Status == AsyncOperationStatus.Succeeded && loc.Result != null && loc.Result.Count > 0;
                ArtLoad.Release(loc);
                if (this == null) return;
                if (exists) Fetch<RuntimeAnimatorController>(key + FloraRigs.AnimatorSuffix, a => rigController = a);
                else { Debug.LogWarning($"[MERIDIAN] ShipLegsView: no {key}{FloraRigs.AnimatorSuffix} in the catalog (run CheckSetup); the rig draws without its clips."); Arrived(); }
            };
        }

        void Fetch<T>(string address, System.Action<T> set) where T : class
        {
            var h = ArtLoad.Asset<T>(address);
            rigHandles.Add(h);
            h.Completed += op =>
            {
                if (this == null) return;
                if (op.Status == AsyncOperationStatus.Succeeded && op.Result != null) set(op.Result);
                else Debug.LogWarning($"[MERIDIAN] ShipLegsView: {address} failed to load.");
                Arrived();
            };
        }

        void Arrived()
        {
            if (--rigPending > 0 || Rig != null) return;
            if (rigJson == null || rigSprites == null || rigSprites.Count == 0) { UsesRig = false; LoadLegacy(); return; }
            var set = RigSet.Parse(rigJson.text, out var error);
            var def = set != null ? set.FindPlant(SidePlant) ?? set.plants[0] : null;
            if (def == null) { Debug.LogError($"[MERIDIAN] ShipLegsView: {ArtKeys.Ships.PilgrimRig}: {error ?? "no plants"}."); UsesRig = false; LoadLegacy(); return; }
            var parent = SquashRoot != null ? SquashRoot : transform;
            int layer = target != null ? target.sortingLayerID : 0, order = target != null ? target.sortingOrder : 0;
            Rig = RigBuild.Build(def, RigBuild.ByName(rigSprites), parent, rigController, layer, order, ArtMaterials.MaterialFor(ArtKeys.Ships.PilgrimRig));
            Rig.Root.localPosition = new Vector3(0f, -SideShip.SkidDrop, 0f); // the rig origin is the ground line under the pads
            if (target != null) target.enabled = false;
            Rig.Play(FinWobble);
            RigBuilt?.Invoke(Rig);
        }

        void OnTouchedDown(float speed)
        {
            if (Rig != null && Rig.Has(LegFlex)) Rig.Play(LegFlex);
        }

        /// <summary>True while the art is the level (pre-D-102) hull stood on its stern.</summary>
        public bool StandIn { get; private set; }

        /// <summary>
        /// U-107: places a view so its lowest point is on the skid line, centred on the ship. Level art (wider than tall, nose
        /// at +x) turns 90° so the nose points up and the stern stands on the skid line; upright art stays as drawn.
        /// </summary>
        void StandUpright(Transform view, Bounds b)
        {
            StandIn = b.size.x > b.size.y;
            if (StandIn)
            {
                view.localRotation = Quaternion.Euler(0f, 0f, 90f); // (x, y) → (−y, x): the stern (min x) becomes the bottom
                view.localPosition = new Vector3(b.center.y, -SideShip.SkidDrop - b.min.x, view.localPosition.z);
            }
            else
            {
                view.localRotation = Quaternion.identity;
                view.localPosition = new Vector3(-b.center.x, -SideShip.SkidDrop - b.min.y, view.localPosition.z);
            }
        }

        /// <summary>U-103: thrust stretch 1.15 / cut squash 0.9 along the up axis (pure solver), applied to SquashRoot each frame.</summary>
        public SquashStretch Squash { get; } = new SquashStretch();
        public Transform SquashRoot { get; private set; }

        /// <summary>U-076: the Pilgrim's 3D model view (legacy path only).</summary>
        public ModelSwap Model { get; private set; }

        AsyncOperationHandle<IList<Sprite>> Load(string key, System.Action<Sprite> set)
        {
            var h = ArtLoad.Asset<IList<Sprite>>(key);
            h.Completed += op =>
            {
                if (this == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                set(op.Result[0]);
                applied = false; // re-apply with the new sprite
            };
            return h;
        }

        void LateUpdate()
        {
            if (ship == null || target == null) return;
            if (SquashRoot != null)
            {
                Squash.Step(ship.intent.thrust > 0.05f, Time.deltaTime);
                SquashRoot.localScale = Squash.LocalScale;
            }
            bool legs = ship.LegsDeployed;
            if (Rig != null)
            {
                ShowingLegs = legs; // the fins are the legs: always drawn, flexed on touchdown
                StepRig();
                return;
            }
            if (applied && legs == ShowingLegs) return;
            var sprite = legs ? (Deployed ?? Retracted) : (Retracted ?? Deployed);
            if (sprite == null) return;
            target.sprite = sprite;
            StandUpright(target.transform, sprite.bounds);
            var mat = ArtMaterials.MaterialFor(legs ? ArtKeys.Ships.PilgrimSideLegs : ArtKeys.Ships.PilgrimSide);
            if (mat != null) target.sharedMaterial = mat;
            ShowingLegs = legs;
            applied = true;
        }

        /// <summary>
        /// Clip control: a finished one-shot hands back to fin_wobble (write-defaults closes the hatch again); the surveyor
        /// stepping out opens the hatch; the fins wobble only in flight (speed 0 at frame 0 on the ground, one-shots excepted).
        /// </summary>
        void StepRig()
        {
            if (Rig.OneShotDone) Rig.Play(FinWobble);
            bool aboard = boarding != null && boarding.Aboard;
            if (!aboardKnown) { aboardKnown = true; lastAboard = aboard; }
            else if (aboard != lastAboard)
            {
                lastAboard = aboard;
                if (!aboard && ship.Grounded && Rig.Has(HatchOpen)) Rig.Play(HatchOpen);
            }
            if (Rig.Animator != null)
            {
                bool wobble = !ship.Grounded || Rig.Playing != FinWobble;
                float speed = wobble ? 1f : 0f;
                if (Rig.Animator.speed != speed) Rig.Animator.speed = speed;
            }
        }

        void OnDestroy()
        {
            if (ship != null) ship.TouchedDown -= OnTouchedDown;
            if (retractedHandle.IsValid()) ArtLoad.Release(retractedHandle);
            if (deployedHandle.IsValid()) ArtLoad.Release(deployedHandle);
            foreach (var h in rigHandles) if (h.IsValid()) ArtLoad.Release(h);
        }
    }
}
