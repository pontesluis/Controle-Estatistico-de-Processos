# 📈 Software de Controle Estatístico de Processos (CEP)

Projeto desenvolvido para a disciplina de **Tópicos Especiais em Eletrônica** da **Universidade de Brasília (UnB) – Faculdade do Gama (FGA)**.

Este software implementa uma ferramenta completa de Controle Estatístico de Processos (CEP / SPC) em **Python puro**. Ele lê dados de arquivos JSON, realiza todos os cálculos estatísticos internamente, e gera relatórios em texto, dados consolidados em JSON, imagens das cartas de controle e relatórios completos em PDF (individuais e consolidados).

> **Nota Técnica:** Seguindo os requisitos do projeto, este software **não** utiliza bibliotecas como `numpy`, `scipy` ou `pandas`. Todos os cálculos, constantes estatísticas e distribuições de probabilidade foram implementados do zero utilizando a biblioteca matemática padrão do Python. Apenas o `matplotlib` é utilizado para a geração dos gráficos e dos relatórios em PDF.

---

## ✨ Funcionalidades

- **Cartas de Controle Suportadas:**
  - **Variáveis:** $\bar{X}$ e $R$ (Média e Amplitude), I-MR (Individuais e Amplitude Móvel).
  - **Atributos:** P (Fração não conforme), C (Número de defeitos).
- **Modos de Operação:**
  - **Fase I (Calibrar):** Estabelecimento de parâmetros base com revisão iterativa automática de limites (remoção de amostras que violam a Regra 1).
  - **Fase II (Acompanhar):** Monitoramento de novas amostras contra uma *baseline* fixa.
- **Análise de Capacidade:** Cálculo de RCP, RCPk, $k$ e estimativa de fração (ppm) fora de especificação para dados aproximadamente normais.
- **Análise de Deslocamento:**
  - Cálculo de Risco $\beta$, Probabilidade de Detecção ($Pd$) e $ARL_1$ para diferentes cenários de deslocamento ($\delta$).
  - Detecção precoce de deslocamento da média utilizando **Filtro de Kalman Escalar** e **Regras do Western Electric Handbook**.
- **Regras de Controle:** Implementação da Regra 1 (pontos fora dos limites de controle $\pm 3\sigma$) e testes de padrões adicionais nas zonas A, B e C.
- **Relatórios em PDF Profissionais:**
  - **PDF Individual por Processo:** Ficha técnica com metadados, limites de controle, carta de controle gráfica, análise de capacidade e tabela de deslocamento.
  - **PDF Consolidado:** Capa executiva com quadro geral de todos os processos gerados (calibrações e acompanhamentos), seguido do detalhamento de cada um.

---

## 🚀 Instalação e Execução

### Pré-requisitos
- **Python 3.10** ou superior.

### 1. Clonando e preparando o ambiente
Clone o repositório e crie um ambiente virtual (recomendado):
```bash
git clone https://github.com/pontesluis/Controle-Estat-stico-de-Processos.git
cd Controle-Estatistico-de-Processos

# Criar ambiente virtual
python -m venv venv

# Ativar no Linux/Mac:
source venv/bin/activate
# Ativar no Windows:
venv\Scripts\activate

# Instalar a única dependência externa (matplotlib)
pip install -r requirements.txt
```

### 2. Executando o software

Para processar qualquer arquivo de dados, execute o `main.py` passando o caminho do arquivo JSON que você deseja utilizar:

```bash
python main.py <caminho_do_arquivo.json>
```

> **Nota:** Substitua `<caminho_do_arquivo.json>` pelo nome ou caminho do arquivo JSON que você for utilizar.

#### Exemplo de execução:
```bash
python main.py exemplos/dados_calibracao_x.json
```

Você também pode passar múltiplos arquivos de uma só vez (ou calibrar e acompanhar em sequência):
```bash
python main.py exemplos/dados_calibracao_x.json exemplos/dados_acompanhar_x.json
```

Arquivos de exemplo disponíveis na pasta `exemplos/`:
- `exemplos/dados_calibracao_x.json` (Fase I: Cartas $\bar{X}$ e $R$)
- `exemplos/dados_acompanhar_x.json` (Fase II: Monitoramento $\bar{X}$)
- `exemplos/dados_calibracao_imr.json` (Fase I: Cartas I-MR)
- `exemplos/dados_calibracao_p.json` (Fase I: Carta P)
- `exemplos/dados_calibracao_c.json` (Fase I: Carta C)

---

## 📄 Geração dos Relatórios em PDF

Ao final de cada execução, o software gera automaticamente:
1. **Relatório Individual em PDF:** Salvo em `saida/<nome_do_arquivo>/relatorio.pdf` para cada processo, contendo a ficha técnica completa, cartas de controle, indicadores de capacidade e tabela de deslocamento.
2. **Relatório Consolidado em PDF:** Salvo em `saida/relatorio_consolidado.pdf`, contendo uma folha de rosto executiva com tabela comparativa de todos os processos gerados (calibrações e acompanhamentos) e o detalhamento técnico completo de cada um.

> [!IMPORTANT]
> ### 👁️ Visualização dos PDFs no VS Code
> Por padrão, o **VS Code** não possui um leitor gráfico nativo integrado de arquivos `.pdf`. Caso tente abrir o PDF gerado diretamente no editor sem uma extensão adequada, o VS Code exibirá os dados binários brutos (dando a impressão de ser um "arquivo criptografado" ou ilegível).
> 
> Para visualizar os relatórios normalmente dentro do VS Code:
> - Instale uma extensão de visualização de PDF na aba de extensões (`Ctrl + Shift + X`), por exemplo a **[vscode-pdf](https://marketplace.visualstudio.com/items?itemName=tomoki1207.pdf)** (por *tomoki1207*) ou qualquer leitor de PDF como **PDF Viewer**.
> - Alternativamente, você pode abrir o arquivo `.pdf` gerado fora do VS Code com o visualizador padrão do seu sistema operacional ou diretamente no navegador web (Google Chrome, Microsoft Edge, etc.).

#### Consolidando processos já existentes:
Se você já gerou processos anteriormente e deseja apenas compilar ou atualizar o relatório PDF consolidado com tudo o que está na pasta `saida/`:
```bash
python main.py --consolidar
```

---

## ⚙️ Parâmetros Opcionais

- `--sem-graficos`: Executa gerando todos os arquivos (texto, JSON, gráficos e PDFs) sem abrir janelas interativas na tela.
- `--sem-pdf`: Desativa a geração dos arquivos em PDF.
- `--pdf-saida <caminho>`: Define um caminho ou nome customizado para o PDF consolidado.
- `--saida <pasta>`: Define um diretório de saída customizado (padrão: `saida/`).
- `--sem-revisao`: Desativa a revisão iterativa automática de limites na calibração (Fase I).
- `--kalman`: Ativa o monitoramento com Filtro de Kalman.
- `--consolidar`: Compila todos os processos da pasta de saída em um único PDF consolidado.