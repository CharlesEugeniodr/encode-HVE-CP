# Checklist de execução física — HVE Parte II-B

## Antes do build

- [ ] Identificar placa, revisão e número de série.
- [ ] Registrar tensão de alimentação e clock.
- [ ] Congelar commit/tag do repositório.
- [ ] Registrar SDK, Cube, compilador e flags.
- [ ] Confirmar GPIO marcador e canal serial.
- [ ] Limpar diretório de build e preservar log integral.

## MCU

- [ ] INFO retorna alvo e frequências corretos.
- [ ] SELFTEST retorna 32.400 válidos, 368 reservados e zero falhas.
- [ ] quick_plan executa após cold boot.
- [ ] JSONL passa pelo schema sem erros.
- [ ] Repetir após reset e comparar checksum.
- [ ] Verificar duração abaixo do wrap do contador.
- [ ] Arquivar ELF, BIN/UF2, map e SHA-256.
- [ ] Medir flash, rodata, data, bss e stack.
- [ ] Executar publication_plan com 30 repetições.

## Energia

- [ ] Instrumento e calibração registrados.
- [ ] Taxa de amostragem registrada.
- [ ] Tensão e shunt registrados.
- [ ] GPIO marcador capturado no mesmo eixo temporal.
- [ ] Baseline medido antes e depois.
- [ ] CSV bruto preservado.
- [ ] power_integrate.py executado com contagem exata de operações.
- [ ] Incerteza declarada.

## FPGA

- [ ] Icarus/Verilator executa tb_hve_seq sem falhas.
- [ ] Log de simulação preservado.
- [ ] Yosys executa sem warning crítico.
- [ ] nextpnr fecha timing na frequência declarada.
- [ ] Relatórios de LUT, FF, RAM, DSP e Fmax preservados.
- [ ] Bitstream e SHA-256 arquivados.
- [ ] iCEBreaker mostra LED verde após autoteste.
- [ ] Foto/vídeo e configuração da bancada arquivados.

## Artigo

- [ ] Cada número possui arquivo de evidência.
- [ ] Dados host-mock permanecem fora dos resultados físicos.
- [ ] Baselines carregam os mesmos campos.
- [ ] Nenhum resultado é estimado a partir de datasheet.
- [ ] Tabelas são regeneradas por script.
- [ ] Limitações e ameaças à validade permanecem explícitas.
