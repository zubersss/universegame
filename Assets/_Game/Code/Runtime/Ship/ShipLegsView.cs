using System.Collections.Generic;
using Meridian.Art;
using Meridian.Rendering;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Ship
{
    /// <summary>
    /// Pilgrim's side sprite (U-018, Bible §4.3, D-025): `ships/pilgrim/side` (gear retracted) above
    /// 10 m altitude, `ships/pilgrim/side_legs` (skids deployed) at or below it. Both share one canvas
    /// and pivot, so swapping never moves the hull.
    /// </summary>
    public sealed class ShipLegsView : MonoBehaviour
    {
        public SideShip ship;
        public SpriteRenderer target;

        public Sprite Retracted { get; private set; }
        public Sprite Deployed { get; private set; }
        public bool ShowingLegs { get; private set; }

        AsyncOperationHandle<IList<Sprite>> retractedHandle, deployedHandle;
        bool applied;

        void Start()
        {
            retractedHandle = Load(ArtKeys.Ships.PilgrimSide, s => Retracted = s);
            deployedHandle = Load(ArtKeys.Ships.PilgrimSideLegs, s => Deployed = s);
            // U-076: the Pilgrim's model (B-079) replaces the side sprites once loaded. Its origin is the centre of
            // mass, so its lowest point is set on the skid line, SkidDrop below the body. U-107 (D-102): until the upright
            // Pilgrim (B-123) lands, art wider than tall is the old level hull, stood on its stern as a stand-in.
            if (ship != null && target != null)
            {
                Model = ModelSwap.Attach(target, ArtKeys.Ships.PilgrimModel, ship.transform, Vector3.zero);
                Model.Swapped += s =>
                {
                    var b = ModelSwap.ModelBounds(s.Views[0].Instance);
                    StandUpright(s.transform, b);
                };
            }
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

        /// <summary>U-076: the Pilgrim's 3D model view.</summary>
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
            bool legs = ship.LegsDeployed;
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

        void OnDestroy()
        {
            if (retractedHandle.IsValid()) global::Meridian.Art.ArtLoad.Release(retractedHandle);
            if (deployedHandle.IsValid()) global::Meridian.Art.ArtLoad.Release(deployedHandle);
        }
    }
}
