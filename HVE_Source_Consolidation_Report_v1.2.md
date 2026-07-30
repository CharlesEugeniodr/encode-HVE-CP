# HVE Engine 1.2 — Relatório de consolidação das novas fontes

Data: 28 de julho de 2026

## Resultado

Os novos arquivos fortalecem o projeto, mas pertencem a camadas diferentes.
Eles foram integrados sem substituir o núcleo HVE-4D já validado.

### 1. HVE-6480+tau

O CSV de 32.400 linhas foi validado integralmente.

| Verificação | Resultado |
| --- | ---: |
| Linhas | 32.400 |
| Estados únicos | 32.400 |
| Índices sequenciais | aprovado |
| Correspondência com o layout documental | 32.400/32.400 |
| Cardinalidade HVE-6480 | `360 * 2 * 9 = 6.480` |
| Cardinalidade com tau | `6.480 * 5 = 32.400` |

Conclusão: HVE-6480+tau é uma decomposição semântica do mesmo núcleo de
32.400 estados, não uma arquitetura incompatível.

A ordem normativa encontrada no CSV é:

- theta: 0 a 359, variando mais rápido;
- sigma: +1, -1;
- tau: 0°, +15°, -15°, +30°, -30°;
- phi: base, +15°, +30°, +45°, +60°, -15°, -30°, -45°, -60°.

O índice coincide com:

`index = phi * 3600 + tau * 720 + sigma * 360 + theta`.

### 2. Tabela legada de 18.000 estados

O novo CSV contém exatamente:

`360 * 2 * 5 * 5 = 18.000` estados.

Todos os 18.000 estados são únicos e seus índices são consistentes. Foi
construída uma migração injetiva para o HVE-32.400:

- tau `-2,-1,0,1,2` -> `-30°,-15°,0°,+15°,+30°`;
- phi `0,1,2,3,4` -> `base,+15°,+30°,+45°,+60°`.

Nenhuma colisão ocorreu. Os 14.400 estados adicionais do núcleo de 32.400
correspondem aos quatro planos phi negativos, ausentes na versão legada.

Os campos métricos do CSV legado não foram promovidos a especificação:

- 18.000 estados precisam de 15 bits para um índice fixo mínimo, não 70;
- `Bits_Total_Minimo=40,34` é menor que o próprio campo cromático declarado de
  41 bits;
- 25 bytes equivalem a 200 bits, valor que não decorre de `70+41=111` sem uma
  especificação adicional de quadro, redundância ou correção de erro.

### 3. HVE-128 EFQ

O layout publicado tinha um erro objetivo de contagem. Os tamanhos declarados
somavam 127 bits. O intervalo “87–80” foi descrito como direção de 7 bits, mas
possui oito posições.

O código anexado usa máscara de 7 bits deslocada para a posição 80. Portanto:

- direção ocupa os bits 86–80;
- o bit 87 estava sem função;
- o Engine 1.2 nomeia o bit 87 como reservado e exige zero no perfil estrito;
- o layout passa a contabilizar exatamente 128 bits sem quebrar tokens antigos.

O produto semântico declarado possui:

`log2(N) = 62,0787734942664 bits`.

Consequentemente, o mínimo inteiro de largura fixa é 63 bits. O token completo
continua com 128 bits porque também contém modo, metadados e reservas.

### 4. HVE-Zeta

Foi implementada e testada uma injeção explícita de 137.000 conceitos no
subespaço `(micro,tau)` com theta zero:

`micro = índice mod 1000`

`tau = floor(índice / 1000)`

`índice = 1000 * tau + micro`

Resultado: 137.000 tokens distintos e 137.000 round-trips aprovados.

Limite: o arquivo afirma que existia um `hve_toolkit_128.py`, mas esse código
não foi anexado. Por isso, o novo perfil foi nomeado
`zeta-sigma0/micro-fast/engine-v1`. A injeção atual está provada; não se afirma
compatibilidade binária com um código histórico ausente.

### 5. Imagem do numeral zero

A imagem radial é útil como visualização de camadas angulares. Ela não prova,
sozinha, uma estrutura fractal. Para isso seriam necessários uma regra
iterativa de autossimilaridade, uma lei de escala ou o cálculo de dimensão
fractal. O Engine a trata como visualização conceitual, não como tabela
normativa nem como prova matemática.

### 6. Arquivos duplicados e ausentes

- Os dois DOCX HVE-128 EFQ são byte a byte idênticos.
- `._Linguagem_Angular_Base-720__Mapa_Completo_.csv` possui apenas metadados
  AppleDouble; não é o mapa BASE-720 real.
- O CSV de 18.000 estados não é um mapa de símbolos BASE-720; é uma enumeração
  de estados angulares de versão legada.

## Validação executada

- compilação de todos os módulos Python: aprovada;
- comparador HVE: 35/35 verificações aprovadas;
- núcleo C11 com avisos tratados como erro: aprovado;
- suíte C exaustiva: aprovada;
- HVE-6480+tau: 32.400/32.400;
- migração legada: 18.000/18.000, sem colisões;
- HVE-Zeta: 137.000/137.000;
- HVE-128: soma de campos 128 e pack/unpack aprovado.

O núcleo HVE-4D permanece canônico. As novas fontes agora estão organizadas
como perfil semântico, camada de migração, envelope EFQ e extensão Zeta.
