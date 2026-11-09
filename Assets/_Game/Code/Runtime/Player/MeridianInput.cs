using UnityEngine;
using UnityEngine.InputSystem;

namespace Meridian.Player
{
    /// <summary>
    /// The Input System map from Bible §6, defined once in code. The editor writes it to
    /// Assets/_Game/Settings/Input/MERIDIAN.inputactions so it can be inspected and rebound.
    /// </summary>
    public static class MeridianInput
    {
        public const string OnFoot = "OnFoot", ShipSide = "ShipSide", ShipTop = "ShipTop", Always = "Always";

        public static InputActionAsset Build()
        {
            var asset = ScriptableObject.CreateInstance<InputActionAsset>();
            asset.name = "MERIDIAN";

            var foot = asset.AddActionMap(OnFoot);
            foot.AddAction("Move", InputActionType.Value, expectedControlLayout: "Axis")
                .AddCompositeBinding("1DAxis").With("Negative", "<Keyboard>/a").With("Positive", "<Keyboard>/d");
            foot.FindAction("Move").AddBinding("<Gamepad>/leftStick/x");
            Button(foot, "Sprint", "<Keyboard>/leftShift", "<Gamepad>/leftStickPress");
            Button(foot, "Jump", "<Keyboard>/space", "<Gamepad>/buttonSouth");
            Button(foot, "Dash", "<Keyboard>/leftShift", "<Gamepad>/buttonEast");   // U-088 (D-078): Shift tapped while airborne
            Button(foot, "Crouch", "<Keyboard>/s", "<Gamepad>/leftStick/down");
            // U-176: up / down a ladder or the winch line (W / S).
            foot.AddAction("Climb", InputActionType.Value, expectedControlLayout: "Axis")
                .AddCompositeBinding("1DAxis").With("Negative", "<Keyboard>/s").With("Positive", "<Keyboard>/w");
            foot.FindAction("Climb").AddBinding("<Gamepad>/leftStick/y");
            Button(foot, "Recall", "<Keyboard>/r", "<Gamepad>/dpad/up"); // U-176: the recall beacon (asc_recall)
            foot.AddAction("Aim", InputActionType.Value, "<Mouse>/position", expectedControlLayout: "Vector2");
            Button(foot, "RigPrimary", "<Mouse>/leftButton", "<Gamepad>/rightTrigger");
            Button(foot, "RigSecondary", "<Mouse>/rightButton", "<Gamepad>/leftTrigger");
            Button(foot, "Module1", "<Keyboard>/1");
            Button(foot, "Module2", "<Keyboard>/2");
            Button(foot, "Module3", "<Keyboard>/3");
            Button(foot, "Module4", "<Keyboard>/4");
            Button(foot, "ModulePrev", "<Keyboard>/q", "<Gamepad>/leftShoulder");
            Button(foot, "ModuleNext", "<Keyboard>/e", "<Gamepad>/rightShoulder");
            Button(foot, "Interact", "<Keyboard>/f", "<Gamepad>/buttonWest");
            Button(foot, "BuildMenu", "<Keyboard>/b");
            Button(foot, "Inventory", "<Keyboard>/tab");
            Button(foot, "Map", "<Keyboard>/m");
            Button(foot, "Catalogue", "<Keyboard>/n");
            Button(foot, "FloatCell", "<Keyboard>/v");
            Button(foot, "Sell", "<Keyboard>/g"); // U-174: the Sell panel, topside
            Button(foot, "Skills", "<Keyboard>/k"); // U-175: the Skill Tree

            // U-107 (§6 v4.1): the upright rocket: thrust held on W or Space, A/D tilt (springs upright on release). Thrust
            // and tilt check their keys' state when enabled, so a key held through launch or entry keeps working on the
            // first frame of the other view (D-103: control never leaves the player).
            var side = asset.AddActionMap(ShipSide);
            Button(side, "Thrust", "<Keyboard>/w", "<Keyboard>/space", "<Gamepad>/rightTrigger").wantsInitialStateCheck = true;
            side.AddAction("Lateral", InputActionType.Value, expectedControlLayout: "Axis")
                .AddCompositeBinding("1DAxis").With("Negative", "<Keyboard>/a").With("Positive", "<Keyboard>/d");
            Button(side, "Exit", "<Keyboard>/f", "<Gamepad>/buttonWest");

            var top = asset.AddActionMap(ShipTop);
            Button(top, "Thrust", "<Keyboard>/w", "<Keyboard>/space", "<Gamepad>/rightTrigger").wantsInitialStateCheck = true;
            Button(top, "Retro", "<Keyboard>/s", "<Gamepad>/leftTrigger").wantsInitialStateCheck = true;
            top.AddAction("Rotate", InputActionType.Value, expectedControlLayout: "Axis")
                .AddCompositeBinding("1DAxis").With("Negative", "<Keyboard>/d").With("Positive", "<Keyboard>/a");
            Button(top, "Boost", "<Keyboard>/leftShift", "<Gamepad>/leftStickPress");
            Button(top, "SkipDrive", "<Keyboard>/j", "<Gamepad>/buttonNorth");
            // U-204 F12: no "Fire" (the lance is retired, D-087 / D-173; nothing read the action, and the key list still printed "Fire: LMB")
            Button(top, "Scan", "<Mouse>/rightButton");
            Button(top, "Enter", "<Keyboard>/f", "<Gamepad>/buttonWest"); // hold inside a ring: controlled entry (§5.3)
            Button(top, "SystemMap", "<Keyboard>/m");
            Button(top, "Inventory", "<Keyboard>/tab");

            var always = asset.AddActionMap(Always);
            Button(always, "Pause", "<Keyboard>/escape", "<Gamepad>/start");
            Button(always, "PhotoMode", "<Keyboard>/p");
            return asset;
        }

        static InputAction Button(InputActionMap map, string name, params string[] bindings)
        {
            var a = map.AddAction(name, InputActionType.Button);
            foreach (var b in bindings) a.AddBinding(b);
            return a;
        }
    }
}
