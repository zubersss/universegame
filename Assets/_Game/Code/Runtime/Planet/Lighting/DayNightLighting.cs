using System;
using Meridian.Core;
using Meridian.Planets;
using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace Meridian.Planet.Lighting
{
    /// <summary>
    /// U-025: drives the PlanetSide lights from the game clock (Bible §3 day lengths, §9 sunlight).
    /// `ambient` is the scene's one global light; `sun` is a far point light kept around the view
    /// in the Sun's direction, so normal-mapped sprites are shaded from the side the Sun is on.
    /// Also tints the sky and backdrop. No allocation per frame.
    /// </summary>
    public sealed class DayNightLighting : MonoBehaviour
    {
        /// <summary>The Sun light sits this far from the view center (m), well outside a 9 m ortho view.</summary>
        public const float SunDistance = 60f;

        public Light2D ambient;
        public Light2D sun;
        public Camera view;
        public PlanetBackdrop backdrop;
        public TimeSystem time;

        public PlanetConfig Planet { get; private set; }
        /// <summary>Local time 0..1 (0 midnight, 0.5 noon) used for the last update.</summary>
        public float LocalTime { get; private set; }

        /// <summary>Tests and captures: pin the local time (null = follow the clock).</summary>
        public float? Override;

        /// <summary>Weather (U-026): 0..1 dims the Sun and warms the ambient toward dust; Flash adds a static-discharge burst.</summary>
        [NonSerialized] public float StormDim, Flash;
        /// <summary>The current sky/backdrop multiplier (used by weather to darken its dust at night).</summary>
        public Color SkyTint { get; private set; } = Color.white;

        static readonly Color StormAmbient = new Color(0.95f, 0.72f, 0.52f);

        public void ConfigureFor(PlanetConfig planet)
        {
            Planet = planet;
            Apply();
        }

        void LateUpdate() => Apply();

        public void Apply()
        {
            if (Planet == null) return;
            if (time == null) time = FindAnyObjectByType<TimeSystem>();
            float t = Override ?? DayNightMath.LocalTime(time != null ? time.DayFraction(Planet) : 0f);
            LocalTime = t;
            var id = Planet.id;

            if (ambient != null)
            {
                ambient.intensity = DayNightMath.AmbientIntensity(id, t) * (1f + 0.4f * StormDim) + 1.5f * Flash;
                ambient.color = Color.Lerp(DayNightMath.AmbientColor(id, t), StormAmbient, 0.6f * StormDim);
            }
            if (sun != null)
            {
                float k = DayNightMath.SunIntensity(id, t) * (1f - 0.75f * StormDim); // dust blots out the direct Sun
                sun.intensity = k; // stays enabled at 0 by night: its shaders stay warm (U-028), no dawn hitch
                sun.color = DayNightMath.SunColor(id, t);
                if (view != null)
                {
                    var c = view.transform.position;
                    var d = DayNightMath.SunDirection(t) * SunDistance;
                    sun.transform.position = new Vector3(c.x + d.x, c.y + d.y, 0f);
                }
            }
            SkyTint = DayNightMath.SkyTint(id, t);
            if (backdrop != null) backdrop.SetTint(SkyTint);
        }
    }
}
