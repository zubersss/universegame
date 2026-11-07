using System.Runtime.CompilerServices;

// U-108: the test assemblies read a few internals (FloraRigs.CycleClockOffset, RigPlant's timers); nothing else does.
[assembly: InternalsVisibleTo("MERIDIAN.Tests.Unit")]
[assembly: InternalsVisibleTo("MERIDIAN.Tests.Play")]
