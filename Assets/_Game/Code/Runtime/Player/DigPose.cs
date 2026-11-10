using UnityEngine;

namespace Meridian.Player
{
    /// <summary>
    /// U-209 (D-196): where the shovel lies on a swing's contact drawing so its blade's tip meets the contact point. The tool is turned
    /// along the line from the glove to the target. A target nearer than the blade is long is met by sliding the tool back through the
    /// glove (a mid-shaft hold, up to the clip's slide_max); a farther one by the body's lunge carrying the glove toward it (up to
    /// `lungeMax`). Past both the tip stops short; nearer than the slide allows the blade buries. Pure: RigToolView places the sprite
    /// with it, DigPoseTests hold it.
    /// </summary>
    public static class DigPose
    {
        /// <summary>
        /// `hand`: the glove before any lunge (world). `blade`: the tool's grip to its blade tip (m). Out: `grip` where the tool's own
        /// grip (its sprite's pivot) lies, `dir` its direction, `slide` and `lunge` what was used, `tip` the blade's tip. Returns the
        /// miss along the tool: 0 the tip is on the target, above 0 it stops short by that much, under 0 it passes it (the blade buries).
        /// </summary>
        public static float Contact(Vector2 hand, Vector2 target, float blade, float slideMax, float lungeMax,
            out Vector2 grip, out Vector2 dir, out float slide, out float lunge, out Vector2 tip)
        {
            Vector2 to = target - hand;
            float d = to.magnitude;
            dir = d > 1e-5f ? to / d : Vector2.right;
            lunge = Mathf.Clamp(d - blade, 0f, Mathf.Max(0f, lungeMax));
            slide = Mathf.Clamp(blade - d, 0f, Mathf.Max(0f, slideMax));
            grip = hand + dir * (lunge - slide);
            tip = grip + dir * blade;
            return (d - lunge) - (blade - slide);
        }

        /// <summary>The nearest and the farthest a contact point can lie from the glove and still be met by the tip.</summary>
        public static void Span(float blade, float slideMax, float lungeMax, out float nearest, out float farthest)
        {
            nearest = blade - Mathf.Max(0f, slideMax);
            farthest = blade + Mathf.Max(0f, lungeMax);
        }
    }
}
