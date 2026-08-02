# Integração do HVE 2.5 em um repositório existente

## Decisão estrutural

Integre o HVE 2.5 na raiz do repositório `hve-engine` ou como um diretório
normal de um monorepositório. Não execute `git init` dentro de outro
repositório. Um `.git` aninhado vira um repositório independente oculto para o
repositório pai; se a independência for realmente necessária, use submódulo de
forma explícita.

Esta mudança foi preparada como um commit aplicável sobre a árvore publicada
da versão 2.4.0. Ela preserva os arquivos da 2.4 e promove a 2.5 como extensão
versionada.

## Opção A — importar o bundle e fazer cherry-pick

Na raiz do repositório HVE existente:

```bash
git status --short
git fetch /caminho/hve-engine-v2.5-article-architecture.bundle \
  refs/heads/hve-2.5-article-architecture
git cherry-pick FETCH_HEAD
```

O primeiro comando deve estar limpo. O bundle contém o histórico-base 2.4 e o
commit 2.5, mas o `cherry-pick` aplica apenas a alteração final ao histórico do
seu repositório.

## Opção B — aplicar o patch por e-mail Git

```bash
git status --short
git am --3way 0001-feat-hve-2.5-add-heterogeneous-perceptual-architecture.patch
```

`--3way` permite ao Git usar o ancestral 2.4 quando os hashes de contexto
coincidem. Se o repositório existente tiver mudanças próprias sobre os mesmos
arquivos, resolva os conflitos preservando os contratos de `AGENTS.md`.

## Opção C — usar como diretório de um monorepositório

```bash
mkdir -p packages/hve-engine
rsync -a --exclude='.git' /caminho/hve-engine-commit-v2.5/ packages/hve-engine/
git add packages/hve-engine
git commit -m "feat(hve): integrate HVE Engine 2.5 architecture"
```

Nesse caso, ajuste somente caminhos de CI e empacotamento. Não altere os bytes
de fio, as cardinalidades ou a semântica para acomodar o monorepositório.

## Verificação após a importação

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,visualization]"
python benchmarks/validate_article_contract.py
python -m pytest -q
python -m ruff check .
python -m mypy src tests examples benchmarks
cmake -S c -B build/c
cmake --build build/c
ctest --test-dir build/c --output-on-failure
```

No PowerShell, ative o ambiente com:

```powershell
.venv\Scripts\Activate.ps1
```

O relatório científico preservado da versão 2.5 registra 185 testes Python e
19 grupos C11. O validador arquitetural é uma verificação adicional do commit
de integração e não reescreve a evidência histórica do artigo.
