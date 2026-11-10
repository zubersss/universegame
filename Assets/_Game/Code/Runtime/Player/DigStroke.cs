using Meridian.Rig;
using UnityEngine;

namespace Meridian.Player
{
    /// <summary>U-209: what a dig stroke works on (PlayerRigInput in play; a fake in DigStrokeTests).</summary>
    public interface IDigWorld
    {
        /// <summary>The dig tool in hand.</summary>
        DigTool Tool { get; }
        /// <summary>Where a dig aimed at `aim` lands: the aim itself inside the reach, else the nearest diggable point to the reach's edge along
        /// the aim line (`clamped`). False: nothing to dig there (`point` is where the swing whiffs).</summary>
        bool Target(Vector2 aim, out Vector2 point, out bool clamped);
        /// <summary>The D1 tables' time to open the ground at `point` with the tool in hand (0: it opens at once).</summary>
        float StrokeSeconds(Vector2 point);
        /// <summary>Opens the ground at `point` (RigTools.Dig). False: nothing was dug.</summary>
        bool Open(Vector2 point);
        /// <summary>The Rhythm nodes (dig_rhythm_1 / _2): the share of the stroke time each consecutive stroke on the same face takes off,
        /// and the most a run takes off (0, 0: not bought).</summary>
        float RhythmStep { get; }
        float RhythmMax { get; }
    }

    public enum DigPhase { Idle, Swing, Beam }
    /// <summary>What a contact did: nothing to dig; work added, the cell still shut; the cell opened.</summary>
    public enum DigContact { Whiff, Chip, Open }

    /// <summary>
    /// U-209 (D-196, the owner's 0.6.2 playtest: "disconnected from clicks and the avatar"): the dig as one motion. A press starts a swing
    /// that frame and commits it, released or not; a press in a swing's last BufferSeconds is kept and chains; held, swings chain with no
    /// gap; a swing's target is fixed at its start. The shovel swings on a fixed rhythm (Drawings drawings at DrawingsPerSecond, the
    /// contact on drawing ContactDrawing); each contact adds SwingSeconds ÷ the D1 stroke time of work to its target, so a cell opens in
    /// the tables' time to within one swing; a contact that does not open it is a chip; a target's work is kept WorkKeepSeconds after its
    /// last contact, then heals. The Beam is on from the press' own frame for at least BeamTapSeconds and its work accrues by the second
    /// while the ray rests on a target; the cell opens the frame the work completes. The Rhythm nodes shorten each consecutive stroke
    /// on the same face (Rhythm). No Unity objects and no allocation: PlayerRigInput steps it once a frame, the views read it.
    /// </summary>
    public sealed class DigStroke
    {
        public const int Drawings = 5, ContactDrawing = 1, ChipStages = 3;
        public const float DrawingsPerSecond = 12f;
        public const float SwingSeconds = Drawings / DrawingsPerSecond, ContactSeconds = ContactDrawing / DrawingsPerSecond;
        public const float BufferSeconds = 0.15f, WorkKeepSeconds = 1.5f, BeamTapSeconds = 0.1f;
        /// <summary>Two aims this close are one target: the work goes on where it was (a cursor that drifts between swings).</summary>
        public const float SameTargetM = 0.5f;
        /// <summary>A kept target still stands where it was when aiming at it lands this close to it (the contact is found to a centimetre).</summary>
        public const float KeptSlackM = 0.03f;
        const float Eps = 1e-4f;
        const int Slots = 4;

        public DigPhase Phase { get; private set; }
        /// <summary>A swing or the ray is under way.</summary>
        public bool Active => Phase != DigPhase.Idle;
        /// <summary>Seconds into the swing (0 outside one).</summary>
        public float SwingTime { get; private set; }
        /// <summary>The swing's drawing now (0..Drawings - 1; -1 outside a swing).</summary>
        public int Drawing => Phase == DigPhase.Swing ? Mathf.Min(Drawings - 1, (int)((SwingTime + Eps) * DrawingsPerSecond)) : -1;
        /// <summary>The swing has made its contact.</summary>
        public bool ContactDone { get; private set; }
        /// <summary>A press waits for the swing's end.</summary>
        public bool Buffered { get; private set; }
        /// <summary>Where the stroke works: fixed for a swing, under the ray for the Beam.</summary>
        public Vector2 Target { get; private set; }
        /// <summary>The target has something to dig (false: the swing whiffs, the ray rests on nothing).</summary>
        public bool Diggable { get; private set; }
        /// <summary>The target is the aim pulled in to the reach.</summary>
        public bool Clamped { get; private set; }
        /// <summary>The stroke's own clock (s).</summary>
        public float Clock { get; private set; }

        /// <summary>Tests and the views: swings begun, contacts made and what they did, since the last Reset.</summary>
        public int Swings { get; private set; }
        public int Contacts { get; private set; }
        public int Opens { get; private set; }
        public int Chips { get; private set; }
        public int Whiffs { get; private set; }
        public DigContact LastContact { get; private set; }
        public Vector2 LastContactAt { get; private set; }
        /// <summary>The crack stage the last chip left (1..ChipStages; 0 after a whiff or an open).</summary>
        public int LastStage { get; private set; }

        /// <summary>A swing begins: its target and whether there is anything there.</summary>
        public event System.Action<Vector2, bool> SwingStarted;
        /// <summary>A swing's contact, or the Beam's opening of a cell: what it did, where, the crack stage a chip left.</summary>
        public event System.Action<DigContact, Vector2, int> Contacted;

        struct Slot { public Vector2 at; public float work, last; public bool used; }
        readonly Slot[] slots = new Slot[Slots];
        float beamUntil = -1f;

        // ---- the rhythm (P-U209-3, LEAD 07:1x; D1 §5: "each consecutive stroke on the same face -10 % time (max -30 %)") ----

        /// <summary>A stroke this far from the last one is on another face: the run starts again (a cell's opening moves the face back
        /// about 1.75 brush radii: 1.6 m, 2.3 m with both brush nodes).</summary>
        public const float SameFaceM = 3f;
        const int RhythmCap = 100;
        /// <summary>The strokes made in the run so far: a shovel's contact that does work, a cell the Beam opens. The next stroke's time
        /// is the tables' x RhythmOf(Rhythm, step, max). The run ends on a whiff, when a stroke lands SameFaceM from the last one, and
        /// when the tool has rested WorkKeepSeconds (as the kept work heals).</summary>
        public int Rhythm { get; private set; }
        /// <summary>The share of the tables' stroke time the last stroke took (1: no rhythm; 0.7 at dig_rhythm_1's most).</summary>
        public float RhythmFactor { get; private set; } = 1f;
        Vector2 rhythmAt;
        float rhythmLast = -99f;

        /// <summary>The share of the stroke time left after `strokes` consecutive strokes: 1 - min(strokes x step, max).</summary>
        public static float RhythmOf(int strokes, float step, float max) => 1f - Mathf.Clamp(Mathf.Min(Mathf.Max(0, strokes) * step, max), 0f, 0.9f);

        /// <summary>The tables' `need` at the stroke's target with the run's rhythm; called as a stroke works there (it keeps the run).</summary>
        float Paced(IDigWorld world, float need)
        {
            if (Rhythm > 0 && (Clock - rhythmLast >= WorkKeepSeconds || (Target - rhythmAt).sqrMagnitude > SameFaceM * SameFaceM)) Rhythm = 0;
            rhythmAt = Target;
            rhythmLast = Clock;
            RhythmFactor = RhythmOf(Rhythm, world.RhythmStep, world.RhythmMax);
            return need * RhythmFactor;
        }

        /// <summary>The work a point holds (0..1): its own target's, or a kept one's within SameTargetM.</summary>
        public float WorkAt(Vector2 p)
        {
            int i = Find(p);
            return i >= 0 ? Mathf.Clamp01(slots[i].work) : 0f;
        }

        /// <summary>The crack stage of `work` (0 none, 1..ChipStages).</summary>
        public static int StageOf(float work) => work <= 0f ? 0 : Mathf.Clamp(1 + (int)(work * ChipStages), 1, ChipStages);

        /// <summary>The contacts a shovel needs to open ground whose D1 stroke time is `strokeSeconds` (1 at least).</summary>
        public static int ContactsToOpen(float strokeSeconds) => strokeSeconds <= Eps ? 1 : Mathf.Max(1, Mathf.CeilToInt(strokeSeconds / SwingSeconds - Eps));

        /// <summary>The shovel's time from the press to the cell's opening, held: the first contact, then a swing a further contact.</summary>
        public static float SecondsToOpen(float strokeSeconds) => ContactSeconds + (ContactsToOpen(strokeSeconds) - 1) * SwingSeconds;

        /// <summary>Stops whatever is under way and forgets the kept work (a new planet, a scripted reset).</summary>
        public void Reset()
        {
            Cancel();
            for (int i = 0; i < Slots; i++) slots[i].used = false;
            Swings = Contacts = Opens = Chips = Whiffs = 0;
            LastStage = 0;
            Rhythm = 0;
            RhythmFactor = 1f;
        }

        /// <summary>Stops the swing or the ray (the dig tool was put away); kept work stays and heals in its time.</summary>
        public void Cancel()
        {
            Phase = DigPhase.Idle;
            SwingTime = 0f;
            ContactDone = Buffered = false;
            beamUntil = -1f;
        }

        /// <summary>One frame: `pressed` the button went down this frame, `held` it is down, `aim` where the cursor points.</summary>
        public void Step(IDigWorld world, float dt, bool pressed, bool held, Vector2 aim)
        {
            Clock += dt;
            for (int i = 0; i < Slots; i++) if (slots[i].used && Clock - slots[i].last >= WorkKeepSeconds) slots[i].used = false; // it heals
            if (world == null) { Cancel(); return; }
            if (world.Tool == DigTool.Beam) StepBeam(world, dt, pressed, held, aim);
            else StepSwing(world, dt, pressed, held, aim);
        }

        void StepSwing(IDigWorld world, float dt, bool pressed, bool held, Vector2 aim)
        {
            if (Phase != DigPhase.Swing)
            {
                Phase = DigPhase.Idle;
                if (pressed || held) Begin(world, aim, 0f); // the press' own frame shows the swing's first drawing
                return;
            }
            SwingTime += dt;
            if (pressed && SwingTime + Eps >= SwingSeconds - BufferSeconds) Buffered = true;
            if (!ContactDone && SwingTime + Eps >= ContactSeconds) Contact(world);
            if (SwingTime + Eps < SwingSeconds) return;
            if (Buffered || held) Begin(world, aim, Mathf.Max(0f, SwingTime - SwingSeconds)); // chained: the time over carries, no gap
            else { Phase = DigPhase.Idle; SwingTime = 0f; ContactDone = false; }
        }

        void Begin(IDigWorld world, Vector2 aim, float carried)
        {
            Phase = DigPhase.Swing;
            SwingTime = carried;
            ContactDone = Buffered = false;
            Aim(world, aim);
            Swings++;
            SwingStarted?.Invoke(Target, Diggable);
        }

        /// <summary>The target for `aim`: a kept target within SameTargetM is worked on where it was, while it can still be dug from here.</summary>
        void Aim(IDigWorld world, Vector2 aim)
        {
            Diggable = world.Target(aim, out var p, out bool clamped);
            Clamped = clamped;
            if (Diggable)
            {
                int i = Find(p);
                if (i >= 0)
                {
                    var kept = slots[i].at;
                    if (world.Target(kept, out var q, out bool pulled) && !pulled && (q - kept).sqrMagnitude < KeptSlackM * KeptSlackM) p = kept;
                    else slots[i].at = p; // the surveyor moved: the kept work follows the new point
                }
            }
            Target = p;
        }

        void Contact(IDigWorld world)
        {
            ContactDone = true;
            Contacts++;
            LastContactAt = Target;
            if (!Diggable) { Whiff(); return; }
            int i = Find(Target);
            if (i < 0) i = Add(Target);
            float need = Paced(world, world.StrokeSeconds(Target));
            slots[i].work += need > Eps ? SwingSeconds / need : 1f;
            slots[i].last = Clock;
            if (Rhythm < RhythmCap) Rhythm++; // a stroke of the run
            if (slots[i].work + Eps >= 1f) { Open(world, i); return; }
            Chips++;
            LastContact = DigContact.Chip;
            LastStage = StageOf(slots[i].work);
            Contacted?.Invoke(DigContact.Chip, Target, LastStage);
        }

        bool Open(IDigWorld world, int slot)
        {
            slots[slot].used = false;
            LastContactAt = Target;
            if (!world.Open(Target)) { Whiff(); return false; } // the ground went meanwhile
            Opens++;
            LastContact = DigContact.Open;
            LastStage = 0;
            Contacted?.Invoke(DigContact.Open, Target, 0);
            return true;
        }

        void Whiff()
        {
            Rhythm = 0; // the run is broken
            Whiffs++;
            LastContact = DigContact.Whiff;
            LastStage = 0;
            Contacted?.Invoke(DigContact.Whiff, Target, 0);
        }

        void StepBeam(IDigWorld world, float dt, bool pressed, bool held, Vector2 aim)
        {
            if (pressed) beamUntil = Clock + BeamTapSeconds; // a tap still shows its ray and does its work
            if (!(pressed || held || Clock < beamUntil)) { if (Phase != DigPhase.Idle) Cancel(); return; }
            bool first = Phase != DigPhase.Beam;
            Phase = DigPhase.Beam;
            SwingTime = 0f;
            ContactDone = Buffered = false;
            Aim(world, aim);
            if (!Diggable) return;
            int i = Find(Target);
            if (i < 0) i = Add(Target);
            float need = Paced(world, world.StrokeSeconds(Target));
            if (need <= Eps) slots[i].work = 1f;                 // not a D1 planet: a stroke a frame, as before
            else if (!first) slots[i].work += dt / need;         // the press' own frame lights the ray; the work runs from the next
            slots[i].last = Clock;
            if (slots[i].work + Eps >= 1f && Open(world, i) && Rhythm < RhythmCap) Rhythm++; // the Beam's stroke is a cell opened
        }

        int Find(Vector2 p)
        {
            int best = -1;
            float bestSq = SameTargetM * SameTargetM;
            for (int i = 0; i < Slots; i++)
            {
                if (!slots[i].used) continue;
                float sq = (slots[i].at - p).sqrMagnitude;
                if (sq <= bestSq) { bestSq = sq; best = i; }
            }
            return best;
        }

        int Add(Vector2 p)
        {
            int pick = 0;
            float oldest = float.MaxValue;
            for (int i = 0; i < Slots; i++)
            {
                if (!slots[i].used) { pick = i; break; }
                if (slots[i].last < oldest) { oldest = slots[i].last; pick = i; }
            }
            slots[pick] = new Slot { at = p, work = 0f, last = Clock, used = true };
            return pick;
        }
    }
}
