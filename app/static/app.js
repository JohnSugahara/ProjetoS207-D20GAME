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

function desenharLado(id, venceu, decidido) {
  const e = id ? nomeEntrada(id) : null;
  const lado = h("div", { class: `lado${decidido ? (venceu ? " vencedor" : " perdedor") : ""}` });
  if (!e) {
    lado.append(h("span", {}, "a definir"));
    return lado;
  }
  lado.append(h("span", {}, e.name), h("span", { class: "classe" }, e.class_name));
  return lado;
}

function desenharChave() {
  const t = estado.torneio;
  const chave = $("chave");
  chave.replaceChildren();
  $("campeao").textContent = "";
  $("titulo-chave").textContent = t ? `Chaveamento · ${t.name}` : "Chaveamento";
  if (!t) return;

  if (t.status === "finished") {
    const campeao = nomeEntrada(t.champion_id);
    $("campeao").textContent = `Campeão: ${campeao.name} (${campeao.class_name})`;
  }
  if (t.status === "open") {
    chave.append(h("p", { class: "vazio" }, "O chaveamento aparece quando o torneio for iniciado."));
    return;
  }
  for (let r = 1; r <= t.rounds; r++) {
    const coluna = h("div", { class: "rodada" },
      h("h3", {}, r === t.rounds ? "Final" : `Rodada ${r}`));
    for (const m of t.matches.filter((x) => x.round_no === r)) {
      const decidido = m.winner_id !== null;
      const pronto = !decidido && m.entry_a_id && m.entry_b_id;
      const duelo = h("div", { class: `duelo${pronto ? " pronto" : ""}` },
        desenharLado(m.entry_a_id, m.winner_id === m.entry_a_id, decidido),
        desenharLado(m.entry_b_id, m.winner_id === m.entry_b_id, decidido && !m.is_bye));
      if (m.log.length) {
        const detalhes = h("details", {}, h("summary", {}, "Ver rolagens"));
        for (const linha of m.log) detalhes.append(h("p", {}, linha));
        duelo.append(detalhes);
      }
      coluna.append(duelo);
    }
    chave.append(coluna);
  }
}

function desenharParticipantes() {
  const lista = $("participantes");
  lista.replaceChildren();
  if (!estado.torneio) return;
  for (const e of estado.torneio.entries) {
    const info = e.eliminated ? "eliminado" : e.ability_unlocked ? "habilidade ativa" : "habilidade bloqueada";
    const link = h("a", { href: "#titulo-carta", class: "link-classe" }, e.name);
    link.addEventListener("click", (ev) => {
      ev.preventDefault();
      estado.vendoId = e.id;
      desenharCartas();
      $("titulo-carta").scrollIntoView({ behavior: "smooth", block: "start" });
    });
    lista.append(h("li", { class: e.eliminated ? "eliminado" : "" },
      h("strong", {}, link), h("span", {}, e.class_name), h("span", {}, info)));
  }
}

function atualizarBotoes() {
  const t = estado.torneio;
  $("btn-entrar").disabled = !t || t.status !== "open";
  $("btn-iniciar").disabled = !t || t.status !== "open" || t.entries.length < 2;
  const prontos = t ? duelosProntos().length : 0;
  $("btn-rolar").disabled = prontos === 0;
  $("btn-rodada").disabled = prontos === 0;
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
