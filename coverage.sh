# run coverage and generate html report
coverage  run --source tabarnak,tests -m pytest
coverage html
