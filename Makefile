install:
	@pip install \
	-r requirements.txt \
	-r requirements-dev.txt

compile_reqs:
	@rm -f requirements*.txt
	@pip-compile pyproject.toml
	@pip-compile -o requirements-dev.txt --extra dev pyproject.toml

sync_reqs:
	@pip-sync requirements*.txt