# Commit de integração — HVE Engine 2.5

Commit:

```text
a34f30ad2c271e37cdf5ae010cd029942576593a
feat(hve-2.5): add heterogeneous perceptual architecture
```

Ancestral reconstruído da versão 2.4.0:

```text
6b5d8115f7d50bcd8fe8a7ad6675164830fb8e9e
```

## Conteúdo

- implementação Python e C11 de CR88/HVE2 `0x05`;
- condutância `hve-chi-oklab/v1` na escala nativa do Oklab;
- conversão tipada entre fibras sRGB, Display-P3 e Adobe RGB (1998);
- vetores dourados, benchmarks e evidências;
- `AGENTS.md` e instruções do Copilot;
- mapa artigo→código→evidência;
- manifesto científico legível por máquina;
- validador executável do contrato arquitetural.

## Importar por bundle

Na raiz do repositório `hve-engine` existente:

```bash
git status --short
git fetch /caminho/hve-engine-v2.5-article-architecture.bundle \
  refs/heads/hve-2.5-article-architecture
git cherry-pick FETCH_HEAD
```

## Importar por patch

```bash
git status --short
git am --3way 0001-feat-hve-2.5-add-heterogeneous-perceptual-architecture.patch
```

Não crie um `.git` dentro de um repositório já existente. Para um
monorepositório, copie o snapshot para um diretório normal, como
`packages/hve-engine/`, e faça o commit no repositório pai.

## Verificar

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,visualization]"
python benchmarks/validate_article_contract.py
python -m pytest -q
python -m ruff check .
python -m mypy src tests examples benchmarks
```

Resultados verificados antes da criação do commit:

- 185/185 testes Python;
- Ruff sem achados;
- mypy sem erros em 100 arquivos;
- 19/19 grupos C11;
- 100.015 vetores CR88 Python/C11 sem divergência;
- 255 hashes internos verificados.
