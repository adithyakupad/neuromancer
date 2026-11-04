def test_injected_failure(tmp_path):
 (tmp_path/'returned.json').write_text('{"status":"fixture-failure"}')
 assert False, 'deliberate evidence retention test'
