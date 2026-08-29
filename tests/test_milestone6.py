from demo.run_demo import run_demo


def test_demo_runner_fixes_bug_and_passes_tests(tmp_path):
    result = run_demo(project_dir=tmp_path)

    assert "passed" in result.lower()
    assert "demo" in result.lower()
