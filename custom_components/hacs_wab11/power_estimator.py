"""Estimate average power from WAB11 daily energy counters."""

from __future__ import annotations

from collections import deque
from datetime import date, datetime, timedelta
from math import isfinite

from wab11.models.energy import EnergyStatistics

_JOULES_PER_KWH = 3_600_000


class EnergyPowerEstimator:
    """Estimate unweighted average power between recent energy changes.

    The WAB11 total-energy-today counter is coarse and resets at midnight. This
    estimator unwraps a single midnight reset with total-energy-yesterday,
    calculates the slope over a bounded history of positive counter changes,
    and retains the latest result while the counter remains unchanged.
    """

    def __init__(self, *, max_change_points: int = 4) -> None:
        """Initialize an empty estimator.

        Args:
            max_change_points: Number of energy-change boundaries used for the
                rolling slope, including the baseline boundary.

        Raises:
            ValueError: If fewer than two change points are requested.
        """
        if max_change_points < 2:
            raise ValueError("max_change_points must be at least 2")
        self._change_points: deque[tuple[datetime, float]] = deque(
            maxlen=max_change_points
        )
        self._previous_timestamp: datetime | None = None
        self._previous_date: date | None = None
        self._previous_today: float | None = None
        self._cumulative_energy_kwh = 0.0
        self._estimated_power_watts: float | None = None

    @property
    def estimated_power_watts(self) -> float | None:
        """Return the latest estimated average power in watts.

        Returns:
            Estimated watts, or ``None`` until a valid positive interval exists.
        """
        return self._estimated_power_watts

    def update(
        self,
        statistics: EnergyStatistics,
        sampled_at: datetime,
    ) -> float | None:
        """Process one energy sample and return the current estimate.

        Args:
            statistics: WAB11 energy statistics containing today and yesterday
                total-energy counters in kWh.
            sampled_at: Time at which the counters were sampled.

        Returns:
            Rolling average power in watts, or ``None`` while uncalibrated or
            after an invalid sequence forces re-baselining.
        """
        today = float(statistics.total.today)
        yesterday = float(statistics.total.yesterday)
        if not self._valid_counter(today) or not self._valid_counter(yesterday):
            self._clear()
            return None

        if self._previous_timestamp is None:
            self._rebaseline(today, sampled_at)
            return None

        if sampled_at <= self._previous_timestamp:
            self._rebaseline(today, sampled_at)
            return None

        sampled_date = sampled_at.date()
        assert self._previous_date is not None
        assert self._previous_today is not None
        if sampled_date == self._previous_date:
            delta_kwh = today - self._previous_today
        elif sampled_date == self._previous_date + timedelta(days=1):
            delta_kwh = yesterday - self._previous_today + today
        else:
            self._rebaseline(today, sampled_at)
            return None

        self._previous_timestamp = sampled_at
        self._previous_date = sampled_date
        self._previous_today = today
        if delta_kwh < 0:
            self._rebaseline(today, sampled_at)
            return None
        if delta_kwh == 0:
            return self._estimated_power_watts

        self._cumulative_energy_kwh += delta_kwh
        self._change_points.append((sampled_at, self._cumulative_energy_kwh))
        first_time, first_energy = self._change_points[0]
        elapsed_seconds = (sampled_at - first_time).total_seconds()
        energy_delta = self._cumulative_energy_kwh - first_energy
        self._estimated_power_watts = energy_delta * _JOULES_PER_KWH / elapsed_seconds
        return self._estimated_power_watts

    @staticmethod
    def _valid_counter(value: float) -> bool:
        """Return whether a counter is finite and non-negative."""
        return isfinite(value) and value >= 0

    def _rebaseline(self, today: float, sampled_at: datetime) -> None:
        """Start a new uncalibrated sequence from one valid sample."""
        self._change_points.clear()
        self._change_points.append((sampled_at, 0.0))
        self._previous_timestamp = sampled_at
        self._previous_date = sampled_at.date()
        self._previous_today = today
        self._cumulative_energy_kwh = 0.0
        self._estimated_power_watts = None

    def _clear(self) -> None:
        """Discard all estimator state after an invalid counter value."""
        self._change_points.clear()
        self._previous_timestamp = None
        self._previous_date = None
        self._previous_today = None
        self._cumulative_energy_kwh = 0.0
        self._estimated_power_watts = None
