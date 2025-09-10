import os
import tempfile
from pr_analyzer.indexer import build_index, search_index


def test_index_and_search(tmp_path):
    import os
    os.environ["PR_ANALYZER_UNIT_TEST"] = "1"
    repo = tmp_path / "repo"
    repo.mkdir()
    f = repo / "a.py"
    f.write_text("def foo():\n    return 1\n")
    index_path = tmp_path / "test.index"
    build_index(str(repo), str(index_path))
    results = search_index(str(index_path), "foo", top_k=2)
    assert isinstance(results, list)
