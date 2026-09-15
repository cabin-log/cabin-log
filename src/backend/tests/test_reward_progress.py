from datetime import UTC, datetime

import pytest

from app.models.game import StackProfileResponse
from app.services.game import EVENT_REWARD_CATALOG, STACK_REWARD_CATALOG, GameService


@pytest.mark.parametrize(
    "owned,code,activities,days,status,remaining",
    [
        (0, 0, 10, 0, "ready", [50000, 0]),
        (1, 250000, 4, 0, "tracking", [0, 1]),
        (2, 1000000, 15, 0, "ready", [0, 0]),
        (3, 3000000, 30, 6, "tracking", [0, 0, 1]),
        (4, 10000000, 75, 21, "ready", [0, 0, 0]),
        (5, 0, 0, 0, "maximum", []),
    ],
)
def test_stack_progress_tracks_next_owned_level(owned, code, activities, days, status, remaining):
    """Scenario: progress follows owned level and the real OR/AND mastery rules."""
    # Given: current profile metrics and an independently owned reward level.
    service = GameService()
    profile = StackProfileResponse(
        language="Python",
        total_bytes=code,
        ratio=1,
        repository_count=1,
        recent_activity_count=activities,
        active_days_30d=days,
        score=0,
        tier=0,
        mastery_level=0,
        calculated_at=datetime.now(UTC),
    )
    # When: requesting next milestone progress.
    result = service._build_reward_progress(
        definition=STACK_REWARD_CATALOG["Python"],
        owned_level=owned,
        profile=profile,
        event_progress={},
        github_connected=True,
    )
    # Then: remaining units and completion agree with the actual mastery calculation.
    assert result.status == status
    assert [m.remaining for m in result.metrics] == remaining
    if status == "ready":
        assert (
            service._calculate_mastery_level(
                total_bytes=code, recent_activity_count=activities, active_days_30d=days
            )
            >= result.next_level
        )


def test_event_progress_reports_real_count_and_no_invented_upgrade():
    """Scenario: event progress counts documentation commits and stops after ownership."""
    # Given: seven qualifying documentation commits.
    service = GameService()
    args = dict(
        definition=EVENT_REWARD_CATALOG["event.docs-scroll"],
        profile=None,
        event_progress={"docs_commits": 7},
        github_connected=True,
    )
    # When: comparing unowned and owned event rewards.
    unowned = service._build_reward_progress(owned_level=0, **args)
    owned = service._build_reward_progress(owned_level=1, **args)
    # Then: three commits remain before acquisition and no second level is fabricated.
    assert unowned.metrics[0].remaining == 3
    assert unowned.metrics[0].target == 10
    assert owned.status == "no_next_level"
    assert owned.next_level is None
