# ---------------------------------------------------------------------------
.PHONY: help install run format lint clean

# Define o shell padrão
SHELL := /bin/bash

help: ## Mostra os comandos disponíveis no Makefile
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Instala as dependências do projeto usando o UV
	uv sync

run: ## Roda a aplicação Streamlit do Kubernetes Dashboard
	uv run streamlit run app.py

format: ## Formata o código usando Ruff (baixado via uvx automaticamente)
	uvx ruff format .
	uvx ruff check --fix .

lint: ## Verifica erros no código usando Ruff
	uvx ruff check .

clean: ## Remove ambientes virtuais e arquivos de cache
	rm -rf .venv __pycache__ .ruff_cache

build-linux: ## Compila o KubeDeck em um executável Linux
	uv run pyinstaller --noconfirm --clean \
		--name KubeDeck \
		--onefile \
		--collect-all streamlit \
		--add-data "app.py:." \
		--add-data "i18n.py:." \
		--add-data "utils.py:." \
		--add-data "logo-KubeDeck.svg:." \
		--add-data "pages:pages" \
		--hidden-import k8s_client \
		run_kubedeck.py

build-windows: ## Compila o KubeDeck para Windows (Requer máquina Windows nativa)
	@echo "Aviso: Execute este comando nativamente no Windows para gerar o .exe perfeito."
	uv run pyinstaller --noconfirm --clean \
		--name KubeDeck \
		--onefile \
		--collect-all streamlit \
		--add-data "app.py;." \
		--add-data "i18n.py;." \
		--add-data "utils.py;." \
		--add-data "logo-KubeDeck.svg;." \
		--add-data "pages;pages" \
		--hidden-import k8s_client \
		run_kubedeck.py

clean-build: ## Remove diretórios de build temporários
	rm -rf build/ dist/ KubeDeck.spec
