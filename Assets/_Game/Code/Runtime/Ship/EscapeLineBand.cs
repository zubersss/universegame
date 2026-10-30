using Meridian.Art;
using Meridian.Planets;
using UnityEngine;

namespace Meridian.Ship
{
    /// <summary>
    /// The Escape Line drawn in the world (Bible §5.1): a faint, slowly scrolling band of light at
    /// the planet's Escape Line y with the label "ESCAPE", following the camera horizontally.
    /// </summary>
    public sealed class EscapeLineBand : MonoBehaviour
    {
        public Camera view;
        public SpriteRenderer band;
        public TextMesh label;
        public float scrollSpeed = 0.6f;
        public float bandHeight = 1.2f;
        float lineY;

        public void ConfigureFor(PlanetConfig planet) => lineY = planet.EscapeLineY;

        void LateUpdate()
        {
            if (view == null) return;
            float width = view.orthographicSize * 2f * view.aspect + 4f;
            transform.position = new Vector3(view.transform.position.x, lineY, 0f);
            if (band != null)
            {
                band.size = new Vector2(width, bandHeight);
                var c = band.color;
                c.a = 0.22f + 0.08f * Mathf.Sin(Time.time * scrollSpeed * 3f);
                band.color = c;
            }
            if (label != null)
            {
                // Label drifts slowly along the band and wraps across the view.
                float x = Mathf.Repeat(Time.time * scrollSpeed * 2f, width) - width * 0.5f;
                label.transform.localPosition = new Vector3(x, 0.9f, 0f);
            }
        }
    }
}
