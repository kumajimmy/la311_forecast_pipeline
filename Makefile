.PHONY: verify checkpoint ingest
verify:
	./scripts/verify.sh
checkpoint:
	./scripts/checkpoint.sh
ingest:
	.venv/bin/python -m src.ingest.cli
