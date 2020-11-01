# run coverage and generate html report
coverage  run --source tabarnak,tests -m unittest discover -v -s tests -p 'test_*.py'
coverage html
