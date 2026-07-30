# HVE Engine 1.3 — Auditoria EFQ128 e memória episódica

Data: 28 de julho de 2026

## Conclusão executiva

Os cinco arquivos recebidos acrescentam duas fontes úteis ao projeto:

1. o formato binário realmente produzido pelo toolkit EFQ128 histórico;
2. um protótipo funcional de contexto episódico baseado em direção e RGB.

Eles também corrigem uma conclusão da versão 1.2. O toolkit histórico não usa o
layout canônico que havia sido inferido apenas do documento. Os dois formatos
são reversíveis isoladamente, mas não são binariamente compatíveis.

O Engine 1.3 passa a manter:

- `efq128-canonical-v1`: bit 87 reservado, direção em 86–80 e RGB contíguo em
  79–56;
- `efq128-attached-toolkit-legacy-v1`: reprodução exata dos bytes históricos;
- transcodificação semântica explícita do legado para o canônico;
- `efq128/episodic-context/v1`: perfil próprio para memória episódica;
- migração PostgreSQL que identifica o layout e calcula similaridade real.

## 1. Inventário auditado

| Arquivo | Resultado |
| --- | --- |
| `hve_toolkit_128.py` | codec EFQ128 histórico identificado; não contém HVE-Zeta |
| `hve_episodic_mappers.py` | heurísticas de direção e RGB aproveitadas |
| `gap3_episodic_memory_hve.py` | protótipo conceitual aproveitado e reestruturado |
| `efc54ed3-d657-45da-9290-0a35410e7eff.py` | cópia byte a byte do arquivo `gap3` |
| `hve_128_episodic_migration.sql` | placeholder substituído por SQL executável |

Hashes e papéis normativos estão registrados em `docs/source_manifest.json`.

## 2. Prova da incompatibilidade binária

O toolkit reconstrói a variável `high_64` três vezes. As duas primeiras
construções são descartadas; apenas a última chega a `struct.pack`.

O layout efetivamente gravado pelo arquivo é:

| Campo | Layout canônico | Toolkit histórico |
| --- | --- | --- |
| direção, 7 bits | 86–80 | 87–81 |
| RGB alto, 16 bits | 79–64 | 80–65 |
| bit 64 | RGB | lacuna igual a zero |
| RGB baixo, 8 bits | 63–56 | 63–56 |

Vetor de prova:

`theta=12, micro=94, sigma=1, tau=2, direction=2, RGB=0xFF0000, extra=12`

| Codificador | Hexadecimal |
| --- | --- |
| canônico | `80060bd00202ff00000000000c000000` |
| histórico | `80060bd00205fe00000000000c000000` |

Quando os bytes históricos são lidos como canônicos, `direction=2` torna-se
`direction=5` e `RGB=0xFF0000` torna-se `RGB=0xFE0000`. Quando os bytes canônicos
são lidos pelo decodificador histórico, `direction=2` torna-se `1` e o RGB é
alterado. Isso demonstra incompatibilidade sem depender de interpretação.

## 3. Defeitos isolados no toolkit histórico

### 3.1 Tau negativo

A validação de tau está comentada. O empacotamento aplica `tau & 0xFFF`:

- `-2` é gravado como `4094`;
- `-1` é gravado como `4095`.

O decodificador devolve os valores unsigned, não os valores negativos
originais. O transcodificador 1.3 preserva primeiro todo valor raw válido entre
0 e 3.599. Somente a região inválida `3600..4095` recebe a interpretação signed
de 12 bits e é projetada no ciclo canônico:

- `-2 -> 3598`;
- `-1 -> 3599`.

### 3.2 Colisão no campo EXTRA

O código usa:

`extra = (phi << 2) | (tau + 2)`

Mas `tau+2` assume cinco valores (`0..4`) e precisa de três bits. O deslocamento
de apenas dois bits provoca sobreposição. Em 25 pares possíveis de
`phi in 0..4` e `tau in -2..2`, aparecem apenas 21 códigos distintos.

Exemplos de colisão:

- código `4`: `(phi=0,tau=2)`, `(phi=1,tau=-2)` e `(phi=1,tau=2)`;
- código `12`: `(phi=2,tau=2)`, `(phi=3,tau=-2)` e `(phi=3,tau=2)`.

Logo, esse `EXTRA` não é uma codificação injetiva do par.

### 3.3 Direção com endpoint duplicado

O arquivo declara 112 direções, mas aceita `0..112`, totalizando 113 valores.
No ciclo de 112 posições, `112` coincide com `0`. A migração normaliza esse
endpoint para zero por padrão ou o rejeita quando a política estrita é pedida.

### 3.4 Mapa textual parcialmente inexequível

O mapa contém 111 símbolos. A regra de microângulo calcula
`int(theta/127*999)`. Para símbolos com theta acima de 127 — como travessões e
aspas curvas nos índices 206, 207, 215 e 216 — o resultado excede 999 e o
próprio encoder rejeita o caractere.

Caracteres não mapeados retornam `None` e são descartados silenciosamente na
codificação de texto. Portanto, esse perfil histórico não é universal nem
lossless para texto arbitrário.

## 4. Limite da HVE-Zeta

O arquivo recebido não contém:

- constante de 137.000 símbolos;
- função de coordenada Zeta;
- codificador ou decodificador Zeta;
- dicionário Sigma-0;
- teste exaustivo Zeta.

Assim, ele não é o código v5 descrito pela nota de entrega, apesar do mesmo nome
genérico. A implementação Zeta do Engine continua matematicamente válida e
exaustivamente testada em 137.000 estados, mas permanece um perfil
independentemente versionado.

## 5. Memória episódica corrigida

O protótipo original já expressava a ideia correta: usar `D` para direção e
`RGB` para uma projeção de valência/arousal. A versão 1.3 formaliza:

- oito direções principais nos pontos `0,14,28,...,98` de `Z_112`;
- distância circular, preservando a vizinhança entre `111` e `0`;
- distância euclidiana RGB normalizada em `[0,1]`;
- peso de direção explícito, com padrão `0,5`;
- tag `EPI1` no campo `EXTRA`, separando memória episódica de Zeta;
- validação rígida de todos os campos.

O RGB continua sendo uma heurística determinística do projeto CONDESSA. Não é
apresentado como modelo emocional aprendido nem como métrica psicológica
validada.

## 6. Correção do banco PostgreSQL

O SQL original não executava similaridade: retornava `0,999` para todas as
linhas. Também mencionava GIN, embora `BYTEA` bruto não forneça busca
vetorial por vizinhança.

A nova migração:

- exige token de 16 bytes e modo HVE-128;
- grava `hve_profile` ao lado do token;
- decodifica direção/RGB nos dois layouts;
- cria colunas geradas para direção e RGB;
- calcula direção circular e distância RGB;
- ordena efetivamente as memórias pelo escore;
- declara que a consulta é exata e linear, não ANN.

## 7. Evidência executável

| Verificação | Resultado |
| --- | ---: |
| golden vector histórico | aprovado |
| diferença entre os layouts | comprovada |
| round-trip histórico | aprovado |
| transcodificação semântica | aprovada |
| amostras aleatórias legado/transcode | 100.000/100.000 |
| extração PostgreSQL canônica/legada | 200.000/200.000 |
| token episódico | 16 bytes |
| similaridade de identidade | `1,0` |
| ranking Leste/positivo | primeiro resultado correto |
| HVE-6480+tau | 32.400/32.400 |
| migração HVE-Lang | 18.000/18.000 |
| HVE-Zeta independente | 137.000/137.000 |

## Decisão técnica

O formato histórico não deve ser apagado nem promovido a canônico. Ele deve ser
preservado como codec legado, identificado por versão e convertido quando
necessário. O layout canônico permanece matematicamente coerente. A memória
episódica passa a ser um perfil de aplicação real do HVE-128, mas sua vantagem
sobre alternativas ainda deve ser medida em corpus de memórias e carga de
banco representativos.
