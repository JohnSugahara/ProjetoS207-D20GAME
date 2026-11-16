"use strict";

/* Ícones provisórios. Para usar sua arte, coloque os arquivos em
   app/static/img/<chave-da-classe>.png (barbaro, ladino, mago, clerigo, guerreiro). */
const ICONES = { barbaro: "🪓", ladino: "🗡️", mago: "🔮", clerigo: "✨", guerreiro: "🛡️" };

const estado = { classes: [], torneio: null, torneioId: null, vendoId: null };
const $ = (id) => document.getElementById(id);

function h(tag, attrs = {}, ...filhos) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") el.className = v;
    else el.setAttribute(k, v);
  }
  for (const f of filhos) el.append(f);
  return el;
}

async function api(caminho, metodo = "GET", corpo) {
  const resposta = await fetch(caminho, {
    method: metodo,
    headers: corpo ? { "Content-Type": "application/json" } : {},
    body: corpo ? JSON.stringify(corpo) : undefined,
  });
  const dados = await resposta.json().catch(() => ({}));
  if (!resposta.ok) {
    const detalhe = Array.isArray(dados.detail) ? "Dados inválidos." : dados.detail;
    throw new Error(detalhe || "Erro inesperado.");
  }
  return dados;
}

function avisar(texto, erro = false) {
  const el = $("mensagem");
  el.textContent = texto;
  el.className = erro ? "erro" : "";
}

async function tentar(acao) {
  try {
    await acao();
  } catch (e) {
    avisar(e.message, true);
  }
}

/* ---------- Cartas ---------- */
function criarCarta(cls, { grande = false, apagada = false, entrada = null } = {}) {
  const arte = h("div", { class: "arte" });
  const img = h("img", { src: `/static/img/${cls.key}.png`, alt: `Arte do ${cls.name}` });
  img.addEventListener("error", () => {
    img.remove();
    arte.append(h("span", { class: "icone" }, ICONES[cls.key] || "🎲"));
  });
  arte.append(img);

  const carta = h("article", { class: `carta${grande ? " grande" : ""}${apagada ? " apagada" : ""}` },
    h("h3", {}, cls.name), arte);

  const habilidades = entrada?.abilities || cls.abilities || [{
    name: cls.ability_name,
    description: cls.ability_description,
    unlocked: false,
  }];
  const listaHabilidades = h("ol", { class: "lista-habilidades" });
  for (const habilidade of habilidades) {
    const item = h("li", { class: habilidade.unlocked ? "desbloqueada" : "bloqueada" },
      h("p", { class: "habilidade" }, habilidade.name),
      h("p", { class: "descricao" }, habilidade.description),
      h("span", { class: "estado-habilidade" }, habilidade.unlocked ? "Desbloqueada" : "Bloqueada"));
    listaHabilidades.append(item);
  }
  carta.append(listaHabilidades);
  if (entrada) {
    const texto = entrada.eliminated ? "Eliminado."
      : entrada.ability_unlocked ? `Habilidade ativa${entrada.lives_left ? ` · vidas extras: ${entrada.lives_left}` : ""}.`
      : "Habilidade bloqueada: vença o primeiro duelo.";
    carta.append(h("p", { class: "estado" }, texto));
  }
  return carta;
}

function minhaEntrada() {
  if (!estado.torneio) return null;
  const id = Number(localStorage.getItem(`d20.eu.${estado.torneioId}`));
  return estado.torneio.entries.find((e) => e.id === id) || null;
}

function entradaVista() {
  if (!estado.torneio || estado.vendoId === null) return null;
  return estado.torneio.entries.find((e) => e.id === estado.vendoId) || null;
}

function desenharCartas() {
  const minha = minhaEntrada();
  const alvo = entradaVista() || minha;
  const destaque = $("minha-carta");
  const outras = $("outras-cartas");
  destaque.replaceChildren();
  outras.replaceChildren();
  $("titulo-carta").textContent =
    alvo && alvo !== minha ? `Carta de ${alvo.name}` : "Sua carta";
  if (!alvo) {
    destaque.className = "vazio";
    destaque.textContent = "Entre em um torneio para sortear a sua carta.";
    return;
  }
  destaque.className = "";
  const cls = estado.classes.find((c) => c.key === alvo.class_key);
  destaque.append(criarCarta(cls, { grande: true, entrada: alvo }));
  for (const outra of estado.classes.filter((c) => c.key !== alvo.class_key)) {
    outras.append(criarCarta(outra, { apagada: true }));
  }
}

/* ---------- Chaveamento ---------- */
function nomeEntrada(id) {
  const e = estado.torneio.entries.find((x) => x.id === id);
  return e ? e : null;
}

/* Chave no formato de Copa: metade dos confrontos à esquerda, metade à
   direita, e a final no centro. Cada confronto tem o seu "Ver rolagens". */
const FASES = ["Final", "Semifinal", "Quartas", "Oitavas"];

function nomeFase(rodada, total) {
  return FASES[total - rodada] || `Rodada ${rodada}`;
}

function desenharLado(id, venceu, decidido, bye) {
  const e = id ? nomeEntrada(id) : null;
  const lado = h("span", { class: `lado${decidido ? (venceu ? " vencedor" : " perdedor") : ""}` });
  if (!e) {
    lado.append(h("span", { class: "nome vago" }, bye ? "bye" : "a definir"));
    return lado;
  }
  lado.append(h("span", { class: "nome" }, e.name), h("span", { class: "classe" }, e.class_name));
  return lado;
}

function desenharDuelo(m) {
  const decidido = m.winner_id !== null;
  const pronto = !decidido && m.entry_a_id && m.entry_b_id;
  const duelo = h("div", { class: `duelo${pronto ? " pronto" : ""}${m.is_bye ? " bye" : ""}` },
    desenharLado(m.entry_a_id, m.winner_id === m.entry_a_id, decidido),
    desenharLado(m.entry_b_id, m.winner_id === m.entry_b_id, decidido && !m.is_bye, m.is_bye));
  if (m.log.length) {
    // "Ver rolagens" abre o log numa janelinha por cima da página (popover):
    // não é cortada pela rolagem da chave e não desalinha os confrontos.
    const id = `log-${m.id}`;
    const nome = (eid) => nomeEntrada(eid)?.name || "bye";
    const titulo = `${nomeFase(m.round_no, estado.torneio.rounds)} · ${nome(m.entry_a_id)} x ${nome(m.entry_b_id)}`;
    const fechar = h("button", {
      type: "button", class: "fechar", popovertarget: id, popovertargetaction: "hide", "aria-label": "Fechar",
    }, "×");
    const janela = h("div", { id, popover: "", class: "log-duelo" },
      h("div", { class: "log-topo" }, h("h3", {}, titulo), fechar));
    for (const linha of m.log) janela.append(h("p", {}, linha));
    duelo.append(h("button", { type: "button", class: "ver-rolagens", popovertarget: id }, "Ver rolagens"), janela);
  }
  return duelo;
}

function colunaRodada(rodada, total, partidas, extraClasse = "") {
  const vagas = h("div", { class: "vagas" });
  for (const m of partidas) vagas.append(h("div", { class: "vaga" }, desenharDuelo(m)));
  return h("div", { class: `rodada${extraClasse}` }, h("h3", {}, nomeFase(rodada, total)), vagas);
}

function desenharChave() {
  const t = estado.torneio;
  const chave = $("chave");
  chave.replaceChildren();
  $("titulo-chave").textContent = t ? `Chaveamento · ${t.name}` : "Chaveamento";
  if (!t) return;

  if (t.status === "open") {
    chave.append(h("p", { class: "vazio" }, "O chaveamento aparece quando o torneio for iniciado."));
    return;
  }

  const esquerda = h("div", { class: "metade esquerda" });
  const direita = h("div", { class: "metade direita" });
  for (let r = 1; r < t.rounds; r++) {
    const partidas = t.matches.filter((x) => x.round_no === r);
    const meio = partidas.length / 2;
    esquerda.append(colunaRodada(r, t.rounds, partidas.slice(0, meio)));
    direita.append(colunaRodada(r, t.rounds, partidas.slice(meio)));
  }

  const final = t.matches.find((x) => x.round_no === t.rounds);
  const centro = colunaRodada(t.rounds, t.rounds, [final], " centro");
  const vagaFinal = centro.querySelector(".vaga");
  vagaFinal.prepend(h("div", { class: "trofeu", "aria-hidden": "true" }, "🏆"));
  if (t.status === "finished") {
    const campeao = nomeEntrada(t.champion_id);
    vagaFinal.append(h("div", { class: "campeao" },
      h("span", {}, "Campeão"), h("strong", {}, campeao.name), h("span", {}, campeao.class_name)));
  }

  chave.append(esquerda, centro, direita);
}

function desenharParticipantes() {
  const lista = $("participantes");
  lista.replaceChildren();
  if (!estado.torneio) return;
  if (!estado.torneio.entries.length) {
    lista.append(h("li", { class: "vazio" }, "Ninguém entrou ainda."));
    return;
  }
  for (const e of estado.torneio.entries) {
    const info = e.eliminated ? "eliminado" : e.ability_unlocked ? "habilidade ativa" : "habilidade bloqueada";
    const link = h("a", { href: "#titulo-carta", class: "link-classe" }, e.name);
    link.addEventListener("click", (ev) => {
      ev.preventDefault();
      estado.vendoId = e.id;
      desenharCartas();
      $("titulo-carta").scrollIntoView({ behavior: "smooth", block: "start" });
    });
    const item = h("li", { class: e.eliminated ? "eliminado" : "" },
      h("strong", {}, link), h("span", {}, e.class_name), h("span", {}, info));
    // Só dá para remover antes de iniciar: depois o jogador já está na chave.
    if (estado.torneio.status === "open") {
      const remover = h("button", {
        type: "button", class: "remover", title: `Remover ${e.name}`, "aria-label": `Remover ${e.name}`,
      }, "×");
      remover.addEventListener("click", () => removerParticipante(e));
      item.append(remover);
    }
    lista.append(item);
  }
}

function removerParticipante(e) {
  return tentar(async () => {
    if (!confirm(`Remover ${e.name} do torneio?`)) return;
    await api(`/api/tournaments/${estado.torneioId}/entries/${e.id}`, "DELETE");
    if (estado.vendoId === e.id) estado.vendoId = null;
    const chaveEu = `d20.eu.${estado.torneioId}`;
    if (Number(localStorage.getItem(chaveEu)) === e.id) localStorage.removeItem(chaveEu);
    await abrirTorneio(estado.torneioId);
    avisar(`${e.name} saiu do torneio.`);
  });
}

function atualizarBotoes() {
  const t = estado.torneio;
  $("btn-entrar").disabled = !t || t.status !== "open";
  $("btn-iniciar").disabled = !t || t.status !== "open" || t.entries.length < 2;
  const prontos = t ? duelosProntos().length : 0;
  $("btn-rolar").disabled = prontos === 0;
  $("btn-rodada").disabled = prontos === 0;
  // Rolar tudo: também serve para um torneio aberto (inicia e já resolve tudo).
  const podeIniciar = t && t.status === "open" && t.entries.length >= 2;
  $("btn-tudo").disabled = !(prontos > 0 || podeIniciar);
  $("btn-reiniciar").disabled = !t || t.status === "open";
}

function duelosProntos() {
  const t = estado.torneio;
  if (!t || t.status !== "running") return [];
  const abertos = t.matches.filter((m) => m.winner_id === null && m.entry_a_id && m.entry_b_id);
  if (!abertos.length) return [];
  const rodada = Math.min(...abertos.map((m) => m.round_no));
  return abertos.filter((m) => m.round_no === rodada);
}

function desenhar() {
  desenharCartas();
  desenharChave();
  desenharParticipantes();
  atualizarBotoes();
}

/* ---------- Ações ---------- */
async function carregarLista(selecionar) {
  const lista = await api("/api/tournaments");
  const select = $("torneio-select");
  select.replaceChildren(h("option", { value: "" }, "— selecione —"));
  for (const t of lista) {
    select.append(h("option", { value: t.id }, `${t.name} (${t.status})`));
  }
  if (selecionar) select.value = String(selecionar);
}

async function abrirTorneio(id) {
  if (String(id) !== String(estado.torneioId)) estado.vendoId = null;
  estado.torneioId = id || null;
  estado.torneio = id ? await api(`/api/tournaments/${id}`) : null;
  desenhar();
}

// Enter em um campo de texto aciona o botão ao lado dele (mesma .linha).
// Se o botão estiver desabilitado, click() não faz nada.
document.querySelectorAll(".linha input").forEach((campo) => {
  campo.addEventListener("keydown", (ev) => {
    if (ev.key !== "Enter" || ev.isComposing) return;
    ev.preventDefault();
    campo.closest(".linha").querySelector("button")?.click();
  });
});

$("torneio-select").addEventListener("change", (ev) =>
  tentar(() => abrirTorneio(ev.target.value)));

$("btn-criar").addEventListener("click", () => tentar(async () => {
  const nome = $("torneio-nome").value.trim();
  if (!nome) return avisar("Digite um nome para o torneio.", true);
  const t = await api("/api/tournaments", "POST", { name: nome });
  $("torneio-nome").value = "";
  await carregarLista(t.id);
  await abrirTorneio(t.id);
  avisar(`Torneio "${t.name}" criado.`);
}));

$("btn-entrar").addEventListener("click", () => tentar(async () => {
  const nome = $("jogador-nome").value.trim();
  if (!nome) return avisar("Digite o seu nome.", true);
  const entrada = await api(`/api/tournaments/${estado.torneioId}/join`, "POST", { name: nome });
  localStorage.setItem(`d20.eu.${estado.torneioId}`, entrada.id);
  $("jogador-nome").value = "";
  await abrirTorneio(estado.torneioId);
  avisar(`${entrada.name} recebeu a carta ${entrada.class_name}!`);
}));

$("btn-iniciar").addEventListener("click", () => tentar(async () => {
  await api(`/api/tournaments/${estado.torneioId}/start`, "POST");
  await carregarLista(estado.torneioId);
  await abrirTorneio(estado.torneioId);
  avisar("Torneio iniciado. Boa sorte!");
}));

async function rolar(partida) {
  await api(`/api/matches/${partida.id}/roll`, "POST");
}

$("btn-rolar").addEventListener("click", () => tentar(async () => {
  await rolar(duelosProntos()[0]);
  await abrirTorneio(estado.torneioId);
  avisar("Duelo decidido.");
}));

$("btn-rodada").addEventListener("click", () => tentar(async () => {
  for (const partida of duelosProntos()) await rolar(partida);
  await carregarLista(estado.torneioId);
  await abrirTorneio(estado.torneioId);
  avisar("Rodada concluída.");
}));

$("btn-tudo").addEventListener("click", () => tentar(async () => {
  const botoes = document.querySelectorAll("#sec-acoes button");
  botoes.forEach((b) => { b.disabled = true; });  // evita clique duplo no meio
  avisar("Rolando todos os duelos...");
  try {
    if (estado.torneio.status === "open") {
      estado.torneio = await api(`/api/tournaments/${estado.torneioId}/start`, "POST");
    }
    // Rola rodada por rodada até sair o campeão.
    let prontos = duelosProntos();
    while (prontos.length) {
      for (const partida of prontos) await rolar(partida);
      estado.torneio = await api(`/api/tournaments/${estado.torneioId}`);
      prontos = duelosProntos();
    }
  } finally {
    await carregarLista(estado.torneioId);
    await abrirTorneio(estado.torneioId);
  }
  const campeao = nomeEntrada(estado.torneio.champion_id);
  avisar(campeao ? `Torneio concluído! Campeão: ${campeao.name}.` : "Duelos concluídos.");
}));

$("btn-reiniciar").addEventListener("click", () => tentar(async () => {
  const ok = confirm("Reiniciar o torneio? Os participantes e as classes continuam, "
    + "mas o chaveamento e as habilidades desbloqueadas serão apagados.");
  if (!ok) return;
  await api(`/api/tournaments/${estado.torneioId}/reset`, "POST");
  await carregarLista(estado.torneioId);
  await abrirTorneio(estado.torneioId);
  avisar("Torneio reiniciado. Inscreva mais jogadores ou inicie de novo.");
}));

tentar(async () => {
  estado.classes = await api("/api/classes");
  await carregarLista();
  desenhar();
});
