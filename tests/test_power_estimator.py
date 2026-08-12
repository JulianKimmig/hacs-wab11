"""Behavioral tests for power estimation from resetting energy counters."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from wab11.models.energy import EnergyStatistics

from custom_components.hacs_wab11.power_estimator import EnergyPowerEstimator


def _statistics(*, today: float, yesterday: float) -> EnergyStatistics:
    """Create energy statistics containing the relevant total counters.

    Args:
        today: Current daily total energy in kWh.
        yesterday: Completed previous-day total energy in kWh.

    Returns:
        Energy statistics populated with the requested totals.
    """
    statistics = EnergyStatistics()
    statistics.total.today = today
    statistics.total.yesterday = yesterday
    return statistics


def test_estimator_requires_two_change_points() -> None:
    """Reject a rolling window that cannot define a slope."""
    with pytest.raises(ValueError, match="at least 2"):
        EnergyPowerEstimator(max_change_points=1)


def test_estimator_holds_smoothed_power_between_energy_changes() -> None:
    """Estimate a rolling average and retain it across unchanged samples."""
    estimator = EnergyPowerEstimator()
    started = datetime(2026, 8, 12, 10, tzinfo=timezone.utc)

    assert estimator.update(_statistics(today=10, yesterday=18), started) is None
    assert (
        estimator.update(
            _statistics(today=10, yesterday=18),
            started + timedelta(minutes=30),
        )
        is None
    )
    assert estimator.update(
        _statistics(today=11, yesterday=18), started + timedelta(hours=1)
    ) == pytest.approx(1000)
    assert estimator.update(
        _statistics(today=11, yesterday=18), started + timedelta(hours=1, minutes=15)
    ) == pytest.approx(1000)
    assert estimator.update(
        _statistics(today=12, yesterday=18), started + timedelta(hours=1, minutes=30)
    ) == pytest.approx(4000 / 3)


def test_estimator_bounds_the_smoothing_history() -> None:
    """Use only the configured number of recent energy-change boundaries."""
    estimator = EnergyPowerEstimator(max_change_points=4)
    started = datetime(2026, 8, 12, 8, tzinfo=timezone.utc)
    assert estimator.update(_statistics(today=0, yesterday=8), started) is None
    for hour in (1, 2, 3):
        assert estimator.update(
            _statistics(today=hour, yesterday=8),
            started + timedelta(hours=hour),
        ) == pytest.approx(1000)

    assert estimator.update(
        _statistics(today=4, yesterday=8),
        started + timedelta(hours=5),
    ) == pytest.approx(750)


def test_estimator_unwraps_one_midnight_reset_with_yesterday_total() -> None:
    """Bridge midnight using the controller's completed yesterday counter."""
    estimator = EnergyPowerEstimator()
    before_midnight = datetime(2026, 8, 12, 23, tzinfo=timezone.utc)

    assert (
        estimator.update(_statistics(today=10, yesterday=16), before_midnight) is None
    )
    assert estimator.update(
        _statistics(today=0, yesterday=11),
        before_midnight + timedelta(hours=1),
    ) == pytest.approx(1000)


@pytest.mark.parametrize(
    ("sampled_at", "today", "yesterday"),
    [
        (datetime(2026, 8, 12, 11, tzinfo=timezone.utc), 4.0, 18.0),
        (datetime(2026, 8, 14, 11, tzinfo=timezone.utc), 1.0, 7.0),
        (datetime(2026, 8, 12, 9, tzinfo=timezone.utc), 6.0, 18.0),
    ],
)
def test_estimator_rebaselines_invalid_sequences(
    sampled_at: datetime,
    today: float,
    yesterday: float,
) -> None:
    """Reject same-day decreases, multi-day gaps, and backward timestamps."""
    estimator = EnergyPowerEstimator()
    started = datetime(2026, 8, 12, 10, tzinfo=timezone.utc)
    assert estimator.update(_statistics(today=5, yesterday=18), started) is None

    assert (
        estimator.update(_statistics(today=today, yesterday=yesterday), sampled_at)
        is None
    )
    assert estimator.estimated_power_watts is None


def test_estimator_rejects_invalid_counter_values() -> None:
    """Rebaseline when a counter is negative or non-finite."""
    estimator = EnergyPowerEstimator()
    sampled_at = datetime(2026, 8, 12, 10, tzinfo=timezone.utc)
    assert estimator.update(_statistics(today=2, yesterday=1), sampled_at) is None

    assert (
        estimator.update(
            _statistics(today=-1, yesterday=1), sampled_at + timedelta(hours=1)
        )
        is None
    )
    assert (
        estimator.update(
            _statistics(today=float("nan"), yesterday=1),
            sampled_at + timedelta(hours=2),
        )
        is None
    )
