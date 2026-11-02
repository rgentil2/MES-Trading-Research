// V5 pure C# ATR-to-ticks math shared by native strategy and CI tests.
// ATR uses completed signal bar; execution occurs on next historical bar.
// Ticks rounded UP; never tighten a stop silently or clip rejected risk.
using System;
namespace NinjaTrader.NinjaScript.Strategies
{
    public static class NQNativeATRExitMathV5
    {
        public static bool TryCompute(int mode, double atr, double tickSize,
            int fixedStopTicks, int fixedTargetTicks,
            int stopMultiplierX10, int targetMultiplierX10,
            out int stopTicks, out int targetTicks)
        {
            stopTicks = 0; targetTicks = 0;
            if (mode < 0 || mode > 3 ||
                fixedStopTicks < 1 || fixedStopTicks > 55 ||
                fixedTargetTicks < 0 || fixedTargetTicks > 240)
                return false;

            if (mode == 0)
            {
                stopTicks = fixedStopTicks;
                targetTicks = fixedTargetTicks;
                return true;
            }
            if (tickSize <= 0.0 || double.IsNaN(tickSize) ||
                double.IsInfinity(tickSize) ||
                atr <= 0.0 || double.IsNaN(atr) ||
                double.IsInfinity(atr) ||
                stopMultiplierX10 < 10 || stopMultiplierX10 > 30 ||
                targetMultiplierX10 < 10 || targetMultiplierX10 > 50)
                return false;
            double rawStop = atr / tickSize * (stopMultiplierX10 / 10.0);
            if (rawStop < 1.0 || rawStop > 55.0 ||
                double.IsNaN(rawStop) || double.IsInfinity(rawStop))
                return false;
            stopTicks = (int)Math.Ceiling(rawStop);
            if (mode == 1)
            {
                if (fixedTargetTicks < 1) return false;
                targetTicks = fixedTargetTicks;
            }
            else if (mode == 2)
            {
                double rawTarget = atr / tickSize *
                    (targetMultiplierX10 / 10.0);
                if (rawTarget < 1.0 || rawTarget > 240.0 ||
                    double.IsNaN(rawTarget) || double.IsInfinity(rawTarget))
                    return false;
                targetTicks = (int)Math.Ceiling(rawTarget);
            }
            // mode3: no TP installed.
            return true;
        }
    }
}
