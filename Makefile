setup-local-development:
	@echo "Setting up local development environment..."
	pip install .[development] && pre-commit install
	@echo "Local development environment setup complete."
