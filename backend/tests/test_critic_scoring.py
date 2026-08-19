from schemas.critic import CriticScores, compute_overall_score


def test_overall_score_is_weighted_average_not_llm_reported():
    scores = CriticScores(
        requirement_understanding=8.0,
        workflow_completeness=8.0,
        logical_correctness=8.0,
        tool_feasibility=8.0,
    )
    assert compute_overall_score(scores) == 8.0


def test_overall_score_weights_are_equal_25_percent():
    scores = CriticScores(
        requirement_understanding=10.0,
        workflow_completeness=0.0,
        logical_correctness=0.0,
        tool_feasibility=0.0,
    )
    assert compute_overall_score(scores) == 2.5


def test_overall_score_below_threshold():
    scores = CriticScores(
        requirement_understanding=5.0,
        workflow_completeness=5.0,
        logical_correctness=5.0,
        tool_feasibility=5.0,
    )
    assert compute_overall_score(scores) == 5.0
