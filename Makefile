MODEL ?= tiny

install:
	bash scripts/install.sh

run:
	venv/bin/python openflow/main.py --model $(MODEL)

models:
	bash scripts/install_models.sh

release:
	git tag v1.0.0 && git push --tags
