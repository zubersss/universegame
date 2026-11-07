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
            // mass, so its lowest point (the skid feet) is set on the skid line, SkidDrop below the body.
            if (ship != null && target != null)
            {
                Model = ModelSwap.Attach(target, ArtKeys.Ships.PilgrimModel, ship.transform, Vector3.zero);
                Model.Swapped += s =>
                {
                    var b = ModelSwap.ModelBounds(s.Views[0].Instance);
                    s.transform.localPosition = new Vector3(0f, -SideShip.SkidDrop - b.min.y, 0f);
                };
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
