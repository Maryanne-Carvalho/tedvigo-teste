# Site oficial de Ted Vigo — redesign completo

Site estático (HTML + CSS + JavaScript, sem dependências externas), pronto para GitHub Pages ou qualquer hospedagem estática. Funciona também abrindo o `index.html` direto do computador.

## Como executar

- **Mais simples:** dê dois cliques em `index.html`.
- **Como servidor local (recomendado para testar vídeos):** na pasta do projeto, rode `python3 -m http.server 8000` e abra `http://localhost:8000`.

## Como publicar (GitHub Pages)

0. **Montagem dos arquivos recebidos:** descompacte `1-site-ted-vigo.zip` e coloque os 4 arquivos `.mp4` dentro de `ted-vigo-site/assets/videos/` (os nomes precisam ficar exatamente `brazil-2014.mp4`, `france-1938.mp4`, `captain-quin.mp4`, `mexico-1986.mp4`). O `2-backup-original.zip` é só a cópia de segurança e pode ser descompactado dentro de `ted-vigo-site/` se quiser mantê-la junto.
1. Envie **todo o conteúdo desta pasta** para o repositório (a pasta `backup/` e a pasta `tools/` são opcionais; o site não depende delas).
2. Em *Settings → Pages*, escolha a branch e a pasta raiz (`/`).
3. Os vídeos têm entre 12 e 22 MB cada, abaixo do limite de 100 MB por arquivo do GitHub.

## Estrutura

```
index.html                    página (gerada por tools/build.py)
assets/css/main.css           sistema visual (cores, tipografia, layout)
assets/css/fonts.css          fontes embutidas (gerado; funciona até via file://)
assets/js/main.js             menu, carrosséis, janelas de sinopse e vídeo, seletor de idioma
assets/js/teaser-srcdoc.js    teaser interativo de Captain Quin — documento original, intacto, carregado só quando necessário
assets/fonts/                 Cormorant Garamond, Lora, Jost, Cinzel (.woff) + licenças OFL
assets/img/covers/            13 capas originais (bytes idênticos aos do HTML original)
assets/img/portrait-of-author-ted-vigo.webp
assets/img/hero-banner.png    banner original (bytes idênticos) + hero-banner.webp (cópia sem perdas, pixels idênticos, mais leve)
assets/img/posters/           miniaturas tiradas dos próprios vídeos
assets/videos/                brazil-2014.mp4 · france-1938.mp4 · captain-quin.mp4 · mexico-1986.mp4
i18n/pt.js  i18n/es.js        traduções (Português do Brasil, Español)
i18n/en.js                    lista de referência dos textos em inglês (não é carregada pelo site)
tools/template.html           modelo da página
tools/build.py                gera index.html copiando os textos em inglês do HTML original
tools/validate.py             validação automática (conteúdo + testes em 12 tamanhos de tela)
tools/last-validation.txt     resultado da última validação
backup/index.original.html    cópia de segurança do HTML original recebido (com imagens base64)
backup/previous-version/      cópia da versão anterior que estava no zip (HTML, CSS, JS, i18n, tools, README)
```

## Como editar textos

- **Inglês:** o inglês é copiado automaticamente de `backup/index.original.html`. Para mudar um texto em inglês, altere o HTML original e rode `python3 tools/build.py` (ou edite `index.html` diretamente, sabendo que um novo build sobrescreve).
- **Português/Espanhol:** edite `i18n/pt.js` ou `i18n/es.js`. Cada chave corresponde a um `data-i18n` no `index.html`.
- **Novo idioma:** crie `i18n/xx.js` com todas as chaves de `i18n/en.js`, inclua o `<script>` no fim do template e acrescente o idioma (com bandeira SVG) em `LANGS` no `main.js`. Um idioma só aparece no seletor se **todas** as chaves estiverem preenchidas — assim nunca se mistura idiomas.
- Depois de qualquer mudança: `python3 tools/build.py && python3 tools/validate.py`.

## Funcionalidades implementadas

- **Navegação:** cabeçalho fixo, transparente sobre o banner e sólido ao rolar; destaque da seção atual; foco visível; menu compacto (botão ☰) abaixo de 1180 px, que fecha com Esc, clique fora ou ao escolher um item. Nomes e destinos originais dos 9 itens mantidos.
- **Seletor de idioma com bandeiras** (🇬🇧 English, 🇧🇷 Português, 🇪🇸 Español — bandeiras em SVG, para aparecerem também no Windows): troca **todo** o site, incluindo textos alternativos das imagens, rótulos de acessibilidade, título da aba e o próprio teaser de Captain Quin. Idioma ativo marcado; escolha salva no navegador; operável só pelo teclado (Enter, setas, Home/End, Esc). Também aceita `?lang=pt` na URL.
- **Livros:** 3 faixas independentes (Novels & Stories, Children's Books, Cup & Mystery Series), na ordem original, com setas, arraste/toque, teclado (setas) e barra de progresso. Capas sobre uma "estante", todas da mesma altura e sem cortes; nas capas que são uma arte aberta (contracapa + lombada + capa), mostra-se só a capa da frente.
- **Sinopse completa** em uma janela de leitura (capa + texto integral + botão "Explore Book →" com o destino original). Sem JavaScript, continua abrindo no próprio card como antes.
- **The People's Cup:** título fixo à esquerda e texto em coluna de leitura confortável, com capitular; os 6 princípios em uma faixa própria logo abaixo.
- **Audiobooks:** cabeçalho e botão à esquerda, 3 cards com a onda sonora original.
- **Trailers:** galeria 2×2 com os 4 MP4, miniaturas tiradas dos vídeos, botão de play grande; player em janela com controles, que só baixa o vídeo ao clicar e para/descarrega ao fechar. Sem reprodução automática. O teaser interativo original fica em destaque logo abaixo, seguido dos cards "Coming soon" e da nota original.
- **Film & TV:** dois projetos em blocos alternados, capa sobre o próprio fundo desfocado.
- **About / Contact / Rodapé:** retrato emoldurado, biografia completa, e-mail e botões originais.
- **Acessibilidade e desempenho:** HTML semântico, link "pular para o conteúdo", `alt` em todas as imagens, foco devolvido ao fechar janelas, `prefers-reduced-motion` respeitado, imagens com carregamento preguiçoso, HTML de 6,5 MB (versão anterior) → ~50 KB (o teaser de 2,7 MB só carrega quando a seção se aproxima).

## Arquivos alterados em relação ao zip recebido

- Novos/reescritos: `index.html`, `assets/css/main.css`, `assets/css/fonts.css`, `assets/js/main.js`, `assets/js/teaser-srcdoc.js`, `i18n/*.js`, `tools/*`, `README.md`, `assets/fonts/*`, `assets/img/posters/*.webp`, `assets/img/hero-banner.*`.
- Reorganizados sem alteração de conteúdo: capas em `assets/img/covers/`.
- Removidos da raiz (guardados em `backup/previous-version/`): `assets/css/original.css`, `assets/css/modern.css`, `assets/js/site.js`, `original/index.original.html` (agora em `backup/`), pôsteres JPG antigos.
- Vídeos: mesmos arquivos MP4 do zip. Exceção: `france-1938.mp4` foi recomprimido de 28 MB para 21,7 MB (mesma resolução 1024×576 e duração, H.264/AAC) para caber no limite de envio de 25 MB; a diferença visual não é perceptível.

---

## ⚠️ Pontos que dependem de confirmação

1. **Associação dos vídeos** (não há cartela de título em três deles; conferi quadro a quadro):
   | Arquivo | Associado a | Evidência | Confiança |
   |---|---|---|---|
   | captain-quin.mp4 | Captain Quin | cartela final "Captain Quin — The Black Pirates of Sagres — Ted Vigo" | certa |
   | brazil-2014.mp4 | Brazil 2014 | torcedores, polícia, perseguição, rio amazônico | alta |
   | france-1938.mp4 | France 1938 | Europa anos 1930, intriga, bandeiras francesas e vista de Paris no final | alta |
   | mexico-1986.mp4 | Mexico 1986 | igreja colonial, rachadura de terremoto, ruínas, catacumbas, figura maia | alta |
2. **Texto do card do vídeo Mexico 1986:** o site original não tinha espaço para esse vídeo. Usei **"Cup & Mystery — Mexico 1986 Trailer"** e **"Watch the Mexico 1986 trailer."**, seguindo exatamente o padrão dos cards de Brazil e France. Confirme ou envie o texto desejado.
3. **Música do teaser de Captain Quin ausente:** no arquivo recebido o áudio estava como `#midia-removida-para-visualizacao`. O botão "♫ MUSIC ON" do teaser não toca nada até o arquivo de áudio ser enviado.
4. **"Explore Book →"** (13 botões) aponta para o próprio card (`#book-…`), sem página de destino — mantido como no original. Envie os links (loja, Amazon etc.) se existirem.
5. **"Rights & Representation" e "Series Materials"** levam à seção Contact (`#contact`), como no original. **"Contact" no menu** abre o e-mail (`mailto:`), como no original.
6. **Diferenças entre capa e título do site** (nada foi alterado): capa "Abraham and Eloise" × site "Abrahan and Eloise"; capa "Icarus and Dalia" × site "Icaro and Dhalia"; capa "Mario, Helena e Maria" × site "Mario, Helena and Maria"; capa "França 1938" × site "France 1938".
7. **Card "Coming soon — Cup & Mystery"** continua como no original, embora já existam trailers de Cup & Mystery na galeria. Avalie se deve sair.
8. **Traduções** feitas para este projeto (não são traduções oficiais). Títulos das obras, nomes de personagens, "Cup & Mystery", "The People's Cup", "PEOPLE'S CUP" e "International People's Football Council (IPFC)" ficaram em inglês. Recomendo revisão por um falante nativo antes de divulgar.
9. **Detalhes técnicos do original mantidos:** o teaser declara `lang="pt-BR"` embora o texto seja inglês (na versão inglesa o documento foi mantido idêntico; em PT/ES o atributo é corrigido). A faixa "Prévia leve…" no fim do arquivo recebido era um aviso da prévia, não conteúdo do site, e não foi incluída.

## Relatório de validação (resumo — completo em `tools/last-validation.txt`)

**196 verificações aprovadas, 0 falhas.** Automático, comparando com `backup/index.original.html`:

- Textos em inglês: os 197 fragmentos de texto do original estão presentes e idênticos (comparação automatizada, ignorando HTML e espaços). Textos novos: apenas rótulos de interface (Skip to content, Language, Menu, Play video, English/EN) e o card do vídeo Mexico 1986 (item 2 acima).
- 13 livros, mesma ordem e categorias; 13 sinopses com HTML idêntico; título e descrição da página idênticos; todos os `alt` originais; todos os ids originais; os 31 links originais com o mesmo texto e destino; todas as âncoras resolvem.
- Imagens: capas, retrato e banner salvos com bytes idênticos aos embutidos no original; teaser interativo idêntico, com suas 7 imagens.
- Português e Espanhol: 147 chaves cada, completas; as 21 linhas traduzidas do teaser encontradas no documento original.
- Navegador (Chromium) em 12 tamanhos — 320×640, 375×667, 390×844, 430×932, 768×1024, 1024×768, 1280×720, 1366×768, 1440×900, 1920×1080, 2560×1080, 2560×1440: sem rolagem horizontal, nenhum elemento fora da tela, cabeçalho sem sobreposição, áreas de toque ≥ 40 px, menu de idioma inteiro na tela, carrossel funcionando, menu móvel abrindo/fechando, sem erros de console.
- Interação (desktop e celular): janela de sinopse com texto integral e Esc; player abre com controles e descarrega ao fechar; teaser carrega o documento original; troca para Português aplicada a todos os elementos, ao teaser e aos `alt`; idioma lembrado após recarregar; troca para Español só com teclado; volta ao inglês restaura o texto original; movimento reduzido respeitado; abertura direta por arquivo funciona.

**Não testado aqui:** reprodução real dos MP4 (o Chromium de teste não decodifica H.264 — os arquivos são H.264/AAC padrão e tocam em Chrome, Edge, Firefox e Safari), Safari/iOS e Firefox reais, leitores de tela, Lighthouse.
