# Arquitetura do artigo HVE 2.5 aplicada ao repositório

Status: mapa normativo de integração

Versão: 2.5.0

Data: 2026-08-01

## Finalidade

Este documento converte a arquitetura científica do artigo HVE 2.5 em uma
regra operacional para manutenção do repositório `hve-engine`. Ele não cria um
segundo modelo HVE e não substitui o artigo. Sua função é impedir que código,
dados, documentação e alegações científicas evoluam de forma desconectada.

O manifesto legível por máquina está em `docs/article_data_v2_5.json`. As
instruções que agentes de código devem obedecer estão em `AGENTS.md`.

## Fluxo arquitetural obrigatório

```text
Núcleo finito
-> geometria refinada
-> grafos e operadores estruturais
-> condutância perceptual declarada
-> conversão tipada externa
-> controle
-> representação e protocolo
-> testes, benchmarks e evidências
```

As dependências podem avançar nesse sentido. Uma camada de aplicação ou um
adaptador de fronteira não pode redefinir o núcleo, a bijeção, a topologia ou o
significado dos bytes de fio.

## Mapeamento artigo → código → prova executável

| Parte do artigo | Responsabilidade no projeto | Implementação e dados principais | Prova executável |
|---|---|---|---|
| 1. Introdução | objeto, perguntas e fronteiras | `README.md`, `IMPLEMENTATION_STATUS.md` | cadeia de qualidade da versão |
| 2. Núcleo abeliano | estado finito, grupo e índices | `src/hve/core.py`, `src/hve/canonical.py` | `tests/test_core.py`, `tests/test_canonical.py` |
| 3. Grafo produto | vizinhança, distância, Laplaciano e espectro | `src/hve/graph.py`, `docs/mathematical_foundations.md` | `tests/test_graph_operations.py` |
| 4. Operadores harmônicos | caracteres, DFT/IDFT, convolução e correlação | `src/hve/harmonic.py` | `tests/test_harmonic.py` |
| 5. Hierarquias refinadas | ângulo/micro/nano e torção/micro/nano | `src/hve/refined.py`, `src/hve/angular.py` | `tests/test_refined.py`, `tests/test_angular.py` |
| 6. Plano de controle | Control-45 e Control-128/v2-v4 | `src/hve/control.py`, `src/hve/control128.py`, `src/hve/chi_refined128*.py` | `tests/test_control.py`, `tests/test_chi_refined_v4.py` |
| 7. Serialização | layouts explícitos, BASE15 e frame HVE2 | `src/hve/protocol.py`, `docs/protocol_specification.md` | `tests/test_protocol.py`, vetores dourados |
| 8. HVE-chi-Refined | CR80, CR88, perfis RGB, condutância e conversão | `src/hve/chi_refined.py`, `src/hve/chromatic_topology.py`, `c/` | testes HVE 2.5 e conformidade Python/C11 |
| 9. Metodologia | unidades, amostras, repetições e tolerâncias | `benchmarks/`, `docs/reproducibility.md` | scripts reproduzíveis |
| 10. Resultados | conformidade e desempenho medido | `evidence/`, `TEST_REPORT.txt` | JSON, XML, logs e CSV preservados |
| 11. Validade | tolerâncias e interpretação | `TEST_REPORT.txt`, resumo dos benchmarks | limites pré-declarados e falhas preservadas |
| 12. Discussão | relação entre geometria, controle e representação | `docs/architecture.md`, `SPECIFICATION.md` | coerência entre contratos |
| 13. Limitações | fronteiras científicas e instrumentais | `AGENTS.md`, `IMPLEMENTATION_STATUS.md` | rejeição de alegações não demonstradas |
| 14. Engenharia futura | vetorização, hardware, energia e dispositivos | `docs/implementation_plan.md` | não promovido a resultado atual |
| 15. Conclusão | resultado implementado e delimitado | `IMPLEMENTATION_STATUS.md` | portão final da versão |
| Apêndice A | vetores normativos | `tests/golden_vectors.json`, `tests/golden_vectors_v25.json` | reprodução byte a byte |
| Apêndice B | protocolo mínimo | `docs/reproducibility.md`, `Makefile` | comandos de teste e build |
| Apêndice C | dados legados | `src/hve/compatibility.py`, adaptadores | testes de transcodificação explícita |
| Apêndice D | estudos experimentais | `src/hve/fingerprint.py`, `src/hve/embeddings.py`, `evidence/` | resultados positivos e negativos preservados |
| Apêndice E | AUX45 histórico | `src/hve/auxiliary45.py` | testes de compatibilidade |

## Regra de representação

Quatro contratos diferentes coexistem e não podem ser misturados:

1. **CR80**: posto canônico bijetivo do produto refinado com o portador bruto
   apontado; 10 bytes.
2. **HVE2/0x04**: palavras CR80 sob um perfil RGB uniforme declarado no frame.
3. **Control-128/v4**: representação de campos para controle e inspeção; não é
   o mesmo layout de CR80 ou CR88.
4. **CR88/HVE2/0x05**: CR80 inalterado seguido de metadado cromático por
   palavra; 11 bytes.

O layout implementado da Tabela 11 é:

```text
bytes 0..9  : CR80
byte 10     : color_space[7:6] | color_state[5:4] | reservado[3:0]
```

Qualquer implementação que coloque o metadado antes de CR80 é incompatível.

## Regra de semântica cromática

A topologia e a percepção são camadas distintas:

- a topologia usa passos RGB8 limitados, sem retorno de 255 para 0;
- `NoColor` é um ponto isolado, não o preto RGB;
- fibras de perfis diferentes são desconexas;
- a condutância Oklab apenas pondera arestas estruturais existentes;
- conversão de perfil é um operador externo e potencialmente não reversível;
- clipping e mapeamento devem permanecer diagnosticáveis por tipo.

## Regra de evidência

Uma afirmação é classificada como:

- **normativa**, quando fixada na especificação e coberta por vetores/testes;
- **exata**, quando decorre de cardinalidade, bijeção ou prova finita;
- **medida**, quando vem de benchmark com host, amostra e repetição declarados;
- **experimental**, quando depende de corpus, modelo ou proxy;
- **futura**, quando ainda não passou pelo portão de implementação.

Não promover resultado futuro a capacidade presente. Não transformar percentil
de um host em WCET. Não tratar perfil RGB declarado como calibração física de
dispositivo.

## Como usar este mapa em novas implementações

Antes de alterar o projeto:

1. identifique a seção arquitetural afetada;
2. localize o código, os vetores e a evidência correspondentes nesta tabela;
3. determine se a mudança preserva a versão ou exige um novo perfil;
4. implemente paridade Python/C11 quando o contrato for compartilhado;
5. acrescente casos válidos, limites e rejeições;
6. execute `python benchmarks/validate_article_contract.py` e a cadeia de
   qualidade indicada em `AGENTS.md`;
7. atualize o manifesto e regenere `SHA256SUMS.txt` somente no estado final.
