using System.Collections;
using Meridian.Art;
using Meridian.Building;
using Meridian.Core;
using Meridian.Planet.POI;
using Meridian.Ship;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-076 (PlayMode, Earth camp): the models replace the cards (the pad as two 2 m modules under one 4 m collider,
    /// the Pilgrim's lowest point on the skid line and the pad deck), the depth bands stand behind the play plane with
    /// the ground strip and flora, the sky quad shows layer 0 only; a base lamp lights from socket_light and a door
    /// opens for the surveyor and closes behind (LEAD cycle 179).
    /// </summary>
    public class U076SceneTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        [UnityTest]
        public IEnumerator ModelsBandsFloraLampAndDoorInTheEarthCamp()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            var side = director.PlanetSide;
            var camp = side.pois.placed.Find(p => p.def == PoiCatalog.SpawnCamp);
            Assert.NotNull(camp, "spawn camp placed on Earth");
            for (int i = 0; i < 90; i++) yield return new WaitForFixedUpdate();

            var legs = side.ship.GetComponentInChildren<ShipLegsView>();
            Assert.NotNull(legs, "ship legs view");
            float until = Time.realtimeSinceStartup + 30f;
            while (Time.realtimeSinceStartup < until)
            {
                bool all = legs.Ready && side.depthBands != null && side.depthBands.RidgeReady && side.depthBands.SkylineReady;
                foreach (var s in side.pois.ModelSwaps) all &= s.Ready;
                if (all) break;
                yield return null;
            }

            // The pad: two 2 m modules, one 4 m collider whose top is the deck; the Pilgrim's skids on it.
            ModelSwap pad = null;
            foreach (var s in side.pois.ModelSwaps) if (s.Key == "props/common/landing_pad") pad = s;
            Assert.NotNull(pad, "pad swap");
            Assert.IsTrue(pad.Ready, "pad model loaded");
            Assert.AreEqual(2, pad.Views.Count, "two modules (D-068)");
            Assert.AreEqual(-1f, pad.Views[0].transform.localPosition.x, 1e-3f, "module 0 at −1 m");
            Assert.AreEqual(1f, pad.Views[1].transform.localPosition.x, 1e-3f, "module 1 at +1 m");
            Assert.IsTrue(pad.Sprite.forceRenderingOff, "the card no longer draws");
            BoxCollider2D padBox = null;
            foreach (var c in side.pois.Solids) if (c.name.StartsWith("landing_pad")) padBox = c;
            Assert.NotNull(padBox, "pad collider");
            Assert.AreEqual(4f, padBox.size.x, 1e-3f, "landing width 4 m");
            float padTop = padBox.bounds.max.y;
            var padBounds = ModelSwap.ModelBounds(pad.Views[0].Instance);
            Assert.AreEqual(padTop, pad.transform.position.y + padBounds.max.y, 0.05f, "collider top = the module's deck");
            float skidLine = float.MaxValue;
            if (legs.UsesRig)
            {
                // U-103 (D-111): the drawn rig's origin is the ground line under the pads.
                Assert.IsTrue(legs.RigReady, "Pilgrim rig built");
                skidLine = legs.Rig.Root.position.y;
            }
            else
            {
                Assert.IsTrue(legs.Model.Ready, "Pilgrim model loaded");
                var shipB = ModelSwap.ModelBounds(legs.Model.Views[0].Instance);
                // U-107: the level stand-in hull stands on its stern (rotated 90°), so take the lowest corner in world space.
                for (int k = 0; k < 8; k++)
                {
                    var corner = shipB.center + Vector3.Scale(shipB.extents, new Vector3((k & 1) == 0 ? -1 : 1, (k & 2) == 0 ? -1 : 1, (k & 4) == 0 ? -1 : 1));
                    skidLine = Mathf.Min(skidLine, legs.Model.Views[0].Instance.transform.TransformPoint(corner).y);
                }
            }
            Assert.AreEqual(side.ship.Body.position.y - SideShip.SkidDrop, skidLine, 0.05f, "the model's lowest point is on the skid line");
            Assert.AreEqual(padTop, skidLine, 0.15f, "skids on the pad");

            // Depth bands behind the play plane, flora on the ground strip, the sky quad parked behind the skyline.
            var db = side.depthBands;
            Assert.NotNull(db, "depth bands");
            Assert.IsTrue(db.RidgeReady, "ridge loaded");
            Assert.IsTrue(db.SkylineReady, "skyline loaded");
            Assert.AreEqual("backgrounds/earth_forest/ridge_mid", db.RidgeKey, "spawn: the forest ridge");
            Assert.That(db.RidgeDepth.x, Is.GreaterThanOrEqualTo(15f), $"ridge front behind the play plane ({db.RidgeDepth}, mirrored {db.RidgeMirrored})");
            Assert.That(db.RidgeDepth.y, Is.LessThanOrEqualTo(70f), "ridge back within its band");
            Assert.Greater(db.FloraCount, 0, "flora planted");
            Assert.NotNull(db.Ground, "ground strip");
            Assert.Greater(db.Ground.vertexCount, 0, "ground strip built");
            Assert.IsTrue(side.backdrop.DepthBandsOn, "the sky quad shows layer 0 only");
            int floraReady = 0, floraTotal = 0;
            until = Time.realtimeSinceStartup + 15f;
            while (Time.realtimeSinceStartup < until && floraReady == 0)
            {
                floraReady = floraTotal = 0;
                foreach (var v in db.GetComponentsInChildren<ModelView>()) if (v.name.StartsWith("Flora")) { floraTotal++; if (v.Ready) floraReady++; }
                if (floraReady == 0) yield return null;
            }
            Assert.Greater(floraReady, 0, $"flora models loaded ({floraReady}/{floraTotal})");

            // A base lamp lights from its bulb socket; a door opens for the surveyor and closes behind.
            var b = side.bases;
            int gy = camp.groundY;
            var lamp = b.Place(new Vector2(PoiCatalog.SpawnCamp.x + 10.5f, gy + 1.5f), PieceKind.Lamp);
            var door = b.Place(new Vector2(PoiCatalog.SpawnCamp.x + 12.5f, gy + 1.5f), PieceKind.Door);
            Assert.NotNull(lamp, "lamp placed");
            Assert.NotNull(door, "door placed");
            until = Time.realtimeSinceStartup + 20f;
            while (Time.realtimeSinceStartup < until && !(lamp.model.Ready && door.model.Ready)) yield return null;
            Assert.IsTrue(lamp.model.Ready && door.model.Ready, "lamp and door models loaded");
            var socket = lamp.model.Find("socket_light");
            Assert.NotNull(socket, "lamp has socket_light (B-081)");
            var lightT = lamp.go.transform.Find("Light");
            Assert.NotNull(lightT, "lamp light");
            Assert.AreEqual(socket.position.x, lightT.position.x, 0.02f, "light x at the bulb");
            Assert.AreEqual(socket.position.y, lightT.position.y, 0.02f, "light y at the bulb");
            Assert.AreEqual(socket.position.z - BaseBuilder.Lamp3DFront, lightT.position.z, 0.02f, "light in front of the faces (U-074)");
            Assert.Greater(socket.position.y, gy + 2f, "the bulb is at the lamp's head");

            var pl = side.player;
            var near = new Vector2(door.go.transform.position.x + 0.5f, gy + 1.05f);
            pl.Body.position = near; pl.transform.position = near;
            until = Time.realtimeSinceStartup + 5f;
            while (Time.realtimeSinceStartup < until && door.model.Views[0].Towards != 1) yield return null;
            Assert.AreEqual(BaseBuilder.DoorClip, door.model.Views[0].Current, "door plays `open`");
            Assert.AreEqual(1, door.model.Views[0].Towards, "opening for the surveyor");
            var far = new Vector2(PoiCatalog.SpawnCamp.x + 5.5f, gy + 1.05f);
            pl.Body.position = far; pl.transform.position = far;
            until = Time.realtimeSinceStartup + 5f;
            while (Time.realtimeSinceStartup < until && door.model.Views[0].Towards != -1) yield return null;
            Assert.AreEqual(-1, door.model.Views[0].Towards, "closing behind");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
