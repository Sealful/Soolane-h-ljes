import math

# ============================================
# Difficulty configuration - Raskuse seaded
# ============================================

# Time thresholds for difficulty scaling (seconds)
DIFFICULTY_RAMP_TIME = 300.0       # Full ramp reached at 5 minutes
DIFFICULTY_INITIAL_DELAY = 10.0   # Grace period before ramp begins

# Spawn difficulty - Tekitamise raskus
BASE_SPAWN_INTERVAL = 2.0          # Starting seconds between waves
MIN_SPAWN_INTERVAL = 0.5           # Fastest spawn interval
SPAWN_RAMP_RATE = 0.7              # How quickly spawn rate increases

# Enemy scaling - Vaenlase skaala
BASE_SPEED_MULTIPLIER = 1.0
MAX_SPEED_MULTIPLIER = 1.5
SPEED_RAMP_RATE = 0.5

BASE_HEALTH_BONUS = 0
MAX_HEALTH_BONUS = 3
HEALTH_RAMP_RATE = 0.6

# Enemy type weighting - Tüüpide kaal
# Weights for (basic, fast, tank) at different time phases
WEIGHTS_EARLY = (0.7, 0.25, 0.05)  # First 30 seconds
WEIGHTS_MID = (0.4, 0.35, 0.25)    # 30-120 seconds
WEIGHTS_LATE = (0.2, 0.35, 0.45)   # After 120 seconds


class DifficultyManager:
    """Time-based difficulty scaling - Ajaline raskus.

    Tracks elapsed game time and provides scaling multipliers
    for spawn rate, enemy speed, health, and type distribution.
    Extensible: add new scaling methods as new difficulty hooks are needed.
    """

    def __init__(self):
        """Initialize difficulty manager with zero elapsed time."""
        self.elapsed_time = 0.0

    def update(self, dt):
        """Advance elapsed time by delta time - Aja uuendus.

        Args:
            dt (float): Seconds since last frame.
        """
        self.elapsed_time += dt

    def _get_ramp_factor(self, ramp_rate):
        """Calculate smooth ramp factor (0.0 to 1.0) based on elapsed time.

        Uses a smoothstep curve for gradual difficulty increase.

        Args:
            ramp_rate (float): Multiplier controlling ramp speed.

        Returns:
            float: Normalized factor between 0.0 and 1.0.
        """
        effective_time = max(0.0, self.elapsed_time - DIFFICULTY_INITIAL_DELAY)
        raw = effective_time * ramp_rate / DIFFICULTY_RAMP_TIME
        # Smoothstep for gradual ramp
        t = max(0.0, min(1.0, raw))
        return t * t * (3 - 2 * t)

    def get_spawn_interval(self):
        """Get current spawn interval in seconds - Tekitamise intervall.

        Returns:
            float: Seconds between spawn waves, decreasing over time.
        """
        factor = self._get_ramp_factor(SPAWN_RAMP_RATE)
        interval = BASE_SPAWN_INTERVAL - factor * (BASE_SPAWN_INTERVAL - MIN_SPAWN_INTERVAL)
        return max(MIN_SPAWN_INTERVAL, interval)

    def get_enemy_speed_multiplier(self):
        """Get enemy speed multiplier - Kiiruse kordaja.

        Returns:
            float: Multiplier applied to enemy base speed (1.0 to 1.5).
        """
        factor = self._get_ramp_factor(SPEED_RAMP_RATE)
        return BASE_SPEED_MULTIPLIER + factor * (MAX_SPEED_MULTIPLIER - BASE_SPEED_MULTIPLIER)

    def get_enemy_health_bonus(self):
        """Get bonus health added to enemies - Tervise boonus.

        Returns:
            int: Extra health points added to enemy base health.
        """
        factor = self._get_ramp_factor(HEALTH_RAMP_RATE)
        return int(BASE_HEALTH_BONUS + factor * (MAX_HEALTH_BONUS - BASE_HEALTH_BONUS))

    def get_type_weights(self):
        """Get enemy type selection weights - Tüüpide kaalud.

        Returns:
            tuple: (basic_weight, fast_weight, tank_weight) for random selection.
        """
        t = self.elapsed_time

        if t < 30:
            return WEIGHTS_EARLY
        elif t < 120:
            # Interpolate between early and mid
            blend = (t - 30) / 90.0
            return tuple(
                w_early + blend * (w_mid - w_early)
                for w_early, w_mid in zip(WEIGHTS_EARLY, WEIGHTS_MID)
            )
        else:
            # Interpolate between mid and late
            blend = min(1.0, (t - 120) / 180.0)
            return tuple(
                w_mid + blend * (w_late - w_mid)
                for w_mid, w_late in zip(WEIGHTS_MID, WEIGHTS_LATE)
            )

    def get_elapsed_time(self):
        """Get formatted elapsed time string - Aja string.

        Returns:
            str: Time formatted as "M:SS" (e.g. "3:42").
        """
        total_seconds = int(self.elapsed_time)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"
