import pytest
from ai_governance_controls.release_a import ai_risk_classify_v2, ai_output_validate, ai_red_team_v2, ai_eval_review

def test_risk_intake_abstains_and_separates_legal_guidance():
    result=ai_risk_classify_v2({"intended_purpose":"clinical diagnosis","decision_role":"clinical","provider_or_deployer":"hospital","affected_people":"patients","geography":"EU","deployment_stage":"pilot","data_categories":"health","consequence":"high","oversight_mechanism":"none"})
    assert result["completion"] == "complete"
    assert result["internal_risk"]["rating"] == "high"
    assert result["legal_applicability"][0]["applicability"] == "potentially_applicable"
    assert result["legal_applicability"][1]["applicability"] == "voluntary_guidance"

def test_risk_fixtures_distinguish_health_hiring_and_unknowns():
    clinical=ai_risk_classify_v2({"intended_purpose":"administrative appointment scheduling","decision_role":"none","oversight_mechanism":"staff review"})
    hiring=ai_risk_classify_v2({"intended_purpose":"rank applicants for hiring","decision_role":"employment decision","oversight_mechanism":"none"})
    unknown=ai_risk_classify_v2({"intended_purpose":"generic HR assistant"})
    assert clinical["legal_applicability"][0]["applicability"] == "unknown"
    assert "employment" in hiring["internal_risk"]["factors"][0]
    assert unknown["completion"] == "needs_input"

def test_output_validation_reports_real_sample_results():
    result=ai_output_validate({"type":"object","required":["decision","reason"]}, [{"decision":"allow","reason":"reviewed"},{"decision":"deny"},"not an object"])
    assert result["summary"] == {"total":3,"passed":1,"failed":2}
    assert result["results"][1]["status"] == "fail"

def test_red_team_v2_is_stable_and_not_run():
    args=({"has_tools":True},["chat","tool"],4,["tool_abuse","prompt_injection"])
    a=ai_red_team_v2(*args); b=ai_red_team_v2(*args)
    assert a["plan_id"] == b["plan_id"]
    assert a["execution_status"] == "not_run"
    assert [x["id"] for x in a["cases"]] == [x["id"] for x in b["cases"]]

def test_eval_review_tracks_inconclusive_and_regressions():
    plan=ai_red_team_v2({},["chat"],2,["prompt_injection"])
    first=[{"case_id":plan["cases"][0]["id"],"outcome":"pass","trace_hash":"sha256:a"}]
    prior=ai_eval_review(plan,first)
    current=ai_eval_review(plan,[{"case_id":plan["cases"][0]["id"],"outcome":"fail","trace_hash":"sha256:b"}],prior)
    assert current["coverage"]["inconclusive"] == 1
    assert plan["cases"][0]["id"] in current["regressions"]
