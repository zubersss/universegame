using System.Collections.Generic;
using Meridian.Art;
using Meridian.Rig;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.InputSystem;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Player
{
    /// <summary>Mouse aim + Rig buttons → RigTools (Bible §6: 1 Beam, 4 Builder, Q/E cycle, left click uses).</summary>
    public sealed class PlayerRigInput : MonoBehaviour
    {
        public enum Module { Beam = 1, Builder = 4 }

        public RigTools rig;
        public Camera view;
        public PlayerController controller;
        public Module module = Module.Beam;

        InputAction aim, primary, m1, m4, prev, next;

        void Start()
        {
            if (controller == null || controller.actions == null) { enabled = false; return; }
            var foot = controller.actions.FindActionMap(MeridianInput.OnFoot, true);
            aim = foot.FindAction("Aim"); primary = foot.FindAction("RigPrimary");
            m1 = foot.FindAction("Module1"); m4 = foot.FindAction("Module4");
            prev = foot.FindAction("ModulePrev"); next = foot.FindAction("ModuleNext");
        }

        void Update()
        {
            if (m1.WasPressedThisFrame()) module = Module.Beam;
            if (m4.WasPressedThisFrame()) module = Module.Builder;
            if (prev.WasPressedThisFrame() || next.WasPressedThisFrame())
                module = module == Module.Beam ? Module.Builder : Module.Beam;
            if (rig == null || view == null || !primary.IsPressed()) return;

            var screen = aim.ReadValue<Vector2>();
            var world = (Vector2)view.ScreenToWorldPoint(new Vector3(screen.x, screen.y, -view.transform.position.z));
            if (module == Module.Beam) rig.Dig(world);
            else rig.Place(world);
        }
    }
}
