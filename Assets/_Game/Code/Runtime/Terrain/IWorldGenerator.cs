namespace Meridian.Terrain
{
    /// <summary>
    /// Pure, thread-safe world generation from a seed (Bible §10.4). Called from worker threads.
    /// </summary>
    public interface IWorldGenerator
    {
        int Width { get; }
        int Height { get; }

        /// <summary>Tile id at world tile (x, y); x must already be wrapped into [0, Width).</summary>
        byte TileAt(int x, int y);

        /// <summary>Topmost solid tile's y at column x (for spawning).</summary>
        int SurfaceHeight(int x);
    }
}
