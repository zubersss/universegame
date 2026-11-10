using System.Collections.Generic;
using UnityEngine;

namespace Meridian.View2D.Living
{
    /// <summary>How a piece moves (contract §12.6): it never bends; rooted below, it bends in the wind; fixed above, it hangs (a chain).</summary>
    public enum LivingMotion { Stands, Sways, Hangs }

    /// <summary>One piece of the stage (contract §12): its picture on the atlas, its size, its root, how it bends.</summary>
    public struct LivingPiece
    {
        public string name;
        /// <summary>Its picture on the layer's atlas (0..1, the lower left first).</summary>
        public Rect uv;
        /// <summary>The picture's size in the world (m).</summary>
        public Vector2 sizeM;
        /// <summary>The root in the picture (0..1 from its lower left): where the plant leaves the ground; a hanging piece's attachment.</summary>
        public Vector2 pivot;
        public LivingMotion motion;
        /// <summary>The bend weight of a point `d` metres from the root: clamp((d − bendFromM) / (bendToM − bendFromM))^bendPower.</summary>
        public float bendFromM, bendToM, bendPower;
        /// <summary>How far the farthest tip travels in a full gust (m).</summary>
        public float giveM;
    }

    /// <summary>One placement of a piece on a layer (the stage file's instances; their order is the draw order).</summary>
    public struct LivingInstance
    {
        public int piece;
        /// <summary>The root's place (m, in the layer's own space).</summary>
        public Vector2 at;
        public float scale;
        /// <summary>Mirrored in x (foreground and far layers only: the painted light then comes from the wrong side).</summary>
        public bool flip;
        /// <summary>The plant's own phase (0..1): its flutter's beat and start.</summary>
        public float phase;
        public Color32 tint;
        /// <summary>Its ground was dug away: it is no longer drawn.</summary>
        public bool gone;
        /// <summary>A foreground piece: it clears round the surveyor and fades underground (D-206b).</summary>
        public bool clears;
    }

    /// <summary>
    /// U-216 (D-206): the living stage's geometry. A layer is ONE mesh: each swaying piece a small grid (cells of about CellM)
    /// over its picture, each standing piece one quad. Every vertex carries what the wind needs, so the vertex shader moves the
    /// whole layer from a few global constants: uv1 = (root x, root y, bend weight, give in metres), uv2 = (phase, the normal's x
    /// sign, 1 for a foreground piece that clears round the surveyor, 0). Pure: lists in, lists out; the stage fills a Mesh from them once at load and again only when a piece goes.
    /// </summary>
    public static class LivingMesh
    {
        /// <summary>A swaying piece's grid cell (m) and the most cells along one side.</summary>
        public const float CellM = 0.2f;
        public const int MaxCells = 24;

        /// <summary>Cells along a side `sizeM` long.</summary>
        public static int CellsFor(float sizeM) => Mathf.Clamp(Mathf.CeilToInt(sizeM / CellM - 1e-4f), 1, MaxCells);

        /// <summary>The bend weight of a point `d` metres from the root (0 at the root, 1 at the farthest tip). Pure.</summary>
        public static float Weight(float d, float fromM, float toM, float power)
        {
            if (toM <= fromM) return d > fromM ? 1f : 0f;
            float k = Mathf.Clamp01((d - fromM) / (toM - fromM));
            return power == 1f || k <= 0f ? k : Mathf.Pow(k, Mathf.Max(0.05f, power));
        }

        /// <summary>The vertices one instance adds: a grid for a swaying piece, a quad for the rest.</summary>
        public static int VertexCount(in LivingPiece piece, float scale)
        {
            if (piece.motion != LivingMotion.Sways) return 4;
            return (CellsFor(piece.sizeM.x * scale) + 1) * (CellsFor(piece.sizeM.y * scale) + 1);
        }

        /// <summary>Appends one instance to the layer's lists (nothing for one that is gone). Returns the vertices added.</summary>
        public static int Append(in LivingPiece piece, in LivingInstance inst, List<Vector3> vertices, List<Vector2> uv0, List<Vector4> uv1, List<Vector4> uv2, List<Color32> colors, List<int> triangles)
        {
            if (inst.gone) return 0;
            float scale = inst.scale > 0f ? inst.scale : 1f;
            bool sways = piece.motion == LivingMotion.Sways;
            int nx = sways ? CellsFor(piece.sizeM.x * scale) : 1, ny = sways ? CellsFor(piece.sizeM.y * scale) : 1;
            int first = vertices.Count;
            float w = piece.sizeM.x * scale, h = piece.sizeM.y * scale, side = inst.flip ? -1f : 1f;
            var packed2 = new Vector4(inst.phase, side, inst.clears ? 1f : 0f, 0f);
            for (int j = 0; j <= ny; j++)
            {
                float v = (float)j / ny;
                for (int i = 0; i <= nx; i++)
                {
                    float u = (float)i / nx;
                    var local = new Vector2((u - piece.pivot.x) * w * side, (v - piece.pivot.y) * h); // from the root
                    float weight = sways ? Weight(local.magnitude, piece.bendFromM * scale, piece.bendToM * scale, piece.bendPower) : 0f;
                    vertices.Add(new Vector3(inst.at.x + local.x, inst.at.y + local.y, 0f));
                    uv0.Add(new Vector2(piece.uv.xMin + piece.uv.width * u, piece.uv.yMin + piece.uv.height * v));
                    uv1.Add(new Vector4(inst.at.x, inst.at.y, weight, piece.giveM * scale));
                    uv2.Add(packed2);
                    colors.Add(inst.tint);
                }
            }
            int row = nx + 1;
            for (int j = 0; j < ny; j++)
                for (int i = 0; i < nx; i++)
                {
                    int a = first + j * row + i, b = a + 1, c = a + row, d = c + 1;
                    triangles.Add(a); triangles.Add(c); triangles.Add(b);
                    triangles.Add(b); triangles.Add(c); triangles.Add(d);
                }
            return vertices.Count - first;
        }
    }
}
