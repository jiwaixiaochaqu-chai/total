"""Regression checks for narrowly scoped guardrail exceptions."""

from scripts import check_project_guardrails as guardrails


def test_runtime_import_exceptions_are_scoped():
    root = guardrails.PROJECT_ROOT
    assert guardrails._is_allowed_runtime_import(
        root / "qa_core/pipeline/retrieval_steps.py", "qa_core.retrieval.models"
    )
    assert not guardrails._is_allowed_runtime_import(
        root / "qa_core/pipeline/retrieval_steps.py", "app"
    )
    assert not guardrails._is_allowed_runtime_import(
        root / "qa_core/other.py", "qa_core.retrieval.models"
    )


def test_rule_and_evidence_files_do_not_trigger_schema_issues():
    issues = guardrails.check_schema_bootstrap_boundary()
    exempt = {
        "scripts/check_codealong_alignment.py",
        "scripts/export_rag_architecture_comparison_xmind.py",
    }
    assert not any(
        issue.path.relative_to(guardrails.PROJECT_ROOT).as_posix() in exempt
        for issue in issues
    )


def test_business_ddl_remains_blocked(tmp_path, monkeypatch):
    schema = tmp_path / guardrails.REQUIRED_MYSQL_SCHEMA_FILE
    schema.parent.mkdir(parents=True)
    schema.write_text("", encoding="utf-8")
    business = tmp_path / "business.py"
    business.write_text('sql = "CREATE ' + 'TABLE example (id INT)"\n', encoding="utf-8")
    monkeypatch.setattr(guardrails, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(guardrails, "iter_python_files", lambda: [business])
    assert guardrails.check_schema_bootstrap_boundary()


def test_implicit_table_creation_remains_blocked(tmp_path, monkeypatch):
    schema = tmp_path / guardrails.REQUIRED_MYSQL_SCHEMA_FILE
    schema.parent.mkdir(parents=True)
    schema.write_text("", encoding="utf-8")
    business = tmp_path / "business.py"
    business.write_text("def ensure_" + "table():\n    pass\n", encoding="utf-8")
    monkeypatch.setattr(guardrails, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(guardrails, "iter_python_files", lambda: [business])
    assert guardrails.check_schema_bootstrap_boundary()
