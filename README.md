# Laboratorio De Analise De Redes Wi-Fi

Analisa SSID, canal, RSSI e seguranca usando amostras sinteticas seguras.

> Projeto educacional inspirado na EETEPA Vilhena Alves. Não é sistema oficial institucional e não usa dados reais de estudantes.

## Visão Geral

**Código curricular:** R-07  
**Curso/área:** Tecnico Em Redes De Computadores  
**Disciplina:** Mobile E Redes Sem Fio  
**Dificuldade:** Intermediate

Este repositório é um MVP executável para portfólio e prática em sala. O comando padrão usa somente amostras seguras em `data/sample/` e gera saídas locais em `data/processed/`, `charts/` ou `reports/`.

## Competências Praticadas

- leitura de dados
- processamento local
- relatório reprodutível

## Como Rodar

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m src.main --sample
```

No Linux/macOS:

```bash
source .venv/bin/activate
```

## Operação Segura

- O CI usa apenas dados sintéticos e não depende de APIs externas.
- Coletas reais, quando existirem, devem ocorrer apenas em ambiente autorizado.
- Nenhum dataset grande, documento interno escolar, telefone, e-mail pessoal ou dado real de estudante é versionado.

## Licença

MIT. Consulte [LICENSE](LICENSE).
