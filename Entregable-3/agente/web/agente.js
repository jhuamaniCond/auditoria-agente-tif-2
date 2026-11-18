/* Agente de Evidencia y Auditoría · mesa de trabajo del auditor (JavaScript puro). */
"use strict";

const $ = (s, raiz = document) => raiz.querySelector(s);
const $$ = (s, raiz = document) => [...raiz.querySelectorAll(s)];
const estado = { ejecuciones: [], seleccionada: null, firma: "", temporizador: null, bitacora: "decisiones", pasosVistos: new Map(),
  cobertura: null, filtro: "", vista: "panel", resaltar: null, documentos: null, archivoDoc: null };
const ORDEN = ["Cubierto", "Parcial", "Desactualizada", "Comprometida", "Sin evidencia", "No aplica"];
const COLOR = { "Cubierto": "--e-cubierto", "Parcial": "--e-parcial", "Desactualizada": "--e-desactualizada",
  "Comprometida": "--e-comprometida", "Sin evidencia": "--e-sin", "No aplica": "--e-na" };
const NOMBRES = { en_curso: "En curso", esperando_aprobacion: "Espera tu decisión", completada: "Completada", rechazada: "Rechazada",
  error: "Error", pendiente: "Pendiente", ok: "Hecho", omitido: "Omitido", interrumpida: "Interrumpida", interrumpido: "Interrumpido",
  cancelada: "Cancelada", cancelado: "Cancelado", pausada: "Pausada", conforme: "Conforme", observaciones: "Con observaciones",
  no_conforme: "No conforme", sin_verificar: "Sin verificar", sin_archivo: "Sin archivo" };
const ABIERTAS = ["en_curso", "esperando_aprobacion", "pausada"];
const REANUDABLES = ["pausada", "interrumpida", "error"];
const TIPOS = { auditoria_interna: "Auditoría interna", bandeja: "Bandeja de entrada" };   // solo flujos de este agente
const VISTAS = {
  panel: ["Panel", "Estado del PIMS de la UNSA y lo que conviene hacer ahora."],
  auditorias: ["Auditorías", "Cada ejecución del agente, paso a paso, con la decisión del auditor."],
  documentos: ["Documentos PIMS", "Procedimientos y registros de evidencia y auditoría guardados en la base de datos."],
  expediente: ["Expediente de evidencias", "Todo lo registrado como evidencia, con su huella y la cadena de custodia."],
  cobertura: ["Cobertura de controles", "Qué requisitos de ISO/IEC 27701:2025 tienen evidencia y qué falta."],
  grafo: ["Grafo de conocimiento", "Lo que sabe el agente (norma, skill, expediente y documentos PIMS) y cómo lo relaciona."],
  bitacoras: ["Bitácoras", "Decisiones humanas, llamadas MCP y eventos del agente."],
  herramientas: ["Herramientas", "Lo que el agente sabe hacer."],
  sistema: ["Datos y sistema", "Servicios de los que depende el agente y datos guardados."],
};
const ACCIONES_CUSTODIA = { REGISTRO: "Registro de evidencia", VERIFICACION: "Verificación de integridad", REVISION_PERTINENCIA: "Revisión de pertinencia" };
const PRELIMINAR = '<span class="preliminar">preliminar, requiere tu validación</span>';

function clase(t) { return String(t ?? "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""); }
function esc(t) { return String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
async function api(ruta, op = {}) {
  const r = await fetch(ruta, op);
  const d = await r.json().catch(() => ({}));
  if (r.status === 401 && d.login) { location.href = "/login?siguiente=" + encodeURIComponent(location.pathname); throw new Error(d.error); }
  if (!r.ok) throw new Error(d.error || `Error ${r.status}`);
  return d;
}
const json = (cuerpo) => ({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo) });
function fecha(iso, corta = false) {
  if (!iso) return ""; const d = new Date(iso);
  return isNaN(d) ? String(iso) : d.toLocaleString("es-PE", corta ? { dateStyle: "medium" } : { dateStyle: "short", timeStyle: "short" });
}
function chip(est, prefijo = "x") { return `<span class="estado ${prefijo}-${clase(est)}">${esc(NOMBRES[est] || est)}</span>`; }
const ICONO_AVISO = { ok: '<svg class="i" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.7 2.7L16 9.5"/></svg>',
  mal: '<svg class="i" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.5M12 16.5v.01"/></svg>' };
function aviso(msg, tipo = "mal") {
  const t = document.createElement("div"), dur = tipo === "mal" ? 7000 : 4000;
  t.className = "aviso-toast " + tipo; t.style.setProperty("--dur", dur + "ms");
  t.innerHTML = (ICONO_AVISO[tipo] || ICONO_AVISO.mal) + "<span></span>";
  t.lastChild.textContent = msg.message || msg;
  $("#avisos").appendChild(t);
  setTimeout(() => { t.classList.add("sale"); setTimeout(() => t.remove(), 260); }, dur);
}
const error = (e) => aviso(e);
const recordar = (k, v) => { try { if (v !== undefined) localStorage.setItem(k, v); return localStorage.getItem(k) || ""; } catch (_) { return v || ""; } };
const plural = (n, s, p) => `${n} ${n === 1 ? s : (p || s + "s")}`;

/* --------------------------------------------------------------------- movimiento */
const movimientoReducido = window.matchMedia("(prefers-reduced-motion: reduce)");
const espera = (ms) => new Promise((r) => setTimeout(r, ms));
/* Reinicia una animación CSS quitando y volviendo a poner la clase. */
function reanimar(el, cls) { if (!el) return; el.classList.remove(cls); void el.offsetWidth; el.classList.add(cls); }
/* Cifra que sube de 0 a su valor con desaceleración. */
function contar(el, hasta, dur = 1100) {
  const fin = Number(hasta) || 0;
  if (movimientoReducido.matches || !fin) { el.textContent = fin; return; }
  const t0 = performance.now(), dec = Number.isInteger(fin) ? 0 : 1;
  const paso = (t) => {
    const p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - p, 3);
    el.textContent = (fin * e).toFixed(dec);
    if (p < 1) requestAnimationFrame(paso);
  };
  requestAnimationFrame(paso);
}
function contarTodo(raiz) { $$("[data-contar]", raiz).forEach((el) => contar(el, el.dataset.contar)); }
/* La huella SHA-256 aparece "descifrándose": hexadecimal al azar que se fija de izquierda a derecha. */
function descifrar(el, final, retraso = 0, dur = 650) {
  if (movimientoReducido.matches) { el.textContent = final; return; }
  const HEX = "0123456789abcdef";
  el.textContent = final.replace(/./g, () => HEX[Math.random() * 16 | 0]);
  setTimeout(() => {
    const t0 = performance.now();
    const paso = (t) => {
      const p = Math.min(1, (t - t0) / dur), fijos = Math.floor(p * final.length);
      el.textContent = final.slice(0, fijos) + final.slice(fijos).replace(/./g, () => HEX[Math.random() * 16 | 0]);
      if (p < 1) requestAnimationFrame(paso);
    };
    requestAnimationFrame(paso);
  }, retraso);
}
/* Sello que cae sobre la pantalla cuando el auditor aprueba o rechaza. */
function estampar(titulo, detalle, rechazo = false) {
  if (movimientoReducido.matches) return;
  $$(".estampa").forEach((x) => x.remove());
  const e = document.createElement("div");
  e.className = "estampa" + (rechazo ? " rechazo" : ""); e.setAttribute("aria-hidden", "true");
  e.innerHTML = `<div class="disco"><svg viewBox="0 0 200 200">
      <defs><path id="estampa-arco" d="M100,100 m-78,0 a78,78 0 1,1 156,0 a78,78 0 1,1 -156,0"/></defs>
      <circle cx="100" cy="100" r="96" stroke-width="3.5"/><circle cx="100" cy="100" r="90" stroke-width="1.2"/><circle cx="100" cy="100" r="62" stroke-width="1.2"/>
      <text><textPath href="#estampa-arco" textLength="485" lengthAdjust="spacing">UNSA · AUDITORÍA INTERNA · ISO/IEC 27701:2025 ·</textPath></text>
    </svg><div class="centro-estampa"><b></b><small></small></div></div>`;
  e.querySelector("b").textContent = titulo; e.querySelector("small").textContent = detalle;
  document.body.appendChild(e);
  setTimeout(() => e.remove(), 2100);
}

/* Markdown mínimo (todo el HTML se escapa antes). */
function md(texto) {
  const lineas = esc(texto).split("\n");
  let html = "", tabla = [], lista = null;
  const li = (s) => s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>").replace(/`(.+?)`/g, "<code>$1</code>").replace(/(^|\s)_(.+?)_(\s|$)/g, "$1<em>$2</em>$3");
  const cerrarTabla = () => {
    if (!tabla.length) return;
    const filas = tabla.filter((f) => !/^\s*\|?\s*:?-{2,}/.test(f));
    html += '<div class="envoltura"><table>' + filas.map((f, i) => {
      const t = i === 0 ? "th" : "td";
      return "<tr>" + f.trim().replace(/^\||\|$/g, "").split("|").map((c) => `<${t}>${li(c.trim())}</${t}>`).join("") + "</tr>";
    }).join("") + "</table></div>";
    tabla = [];
  };
  const cerrarLista = () => { if (lista) { html += `</${lista}>`; lista = null; } };
  for (const l of lineas) {
    if (/^\s*\|/.test(l)) { cerrarLista(); tabla.push(l); continue; }
    cerrarTabla();
    let m;
    if ((m = l.match(/^(#{1,4})\s+(.*)/))) { cerrarLista(); const n = Math.min(m[1].length + 1, 4); html += `<h${n}>${li(m[2])}</h${n}>`; }
    else if ((m = l.match(/^\s*[-*]\s+(.*)/))) { if (lista !== "ul") { cerrarLista(); html += "<ul>"; lista = "ul"; } html += `<li>${li(m[1])}</li>`; }
    else if ((m = l.match(/^\s*\d+[.)]\s+(.*)/))) { if (lista !== "ol") { cerrarLista(); html += "<ol>"; lista = "ol"; } html += `<li>${li(m[1])}</li>`; }
    else if (l.trim()) { cerrarLista(); html += `<p>${li(l)}</p>`; } else cerrarLista();
  }
  cerrarTabla(); cerrarLista();
  return html;
}

/* ----------------------------------------------------------------- navegación */
function irA(vista) {
  if (estado.vista && estado.vista !== vista) window.scrollTo({ top: 0 });
  estado.vista = vista;
  $$(".item").forEach((x) => x.classList.toggle("activa", x.dataset.vista === vista));
  $$(".vista").forEach((v) => v.classList.toggle("activa", v.id === "vista-" + vista));
  const [t, b] = VISTAS[vista] || [vista, ""];
  $("#titulo-vista").textContent = t; $("#bajada-vista").textContent = b;
  reanimar($("#titulo-vista"), "cambia"); moverIndicador();
  document.title = `${t} · Agente de Evidencia`;
  $("#riel").classList.remove("abierto");
  const cargas = { panel: cargarPanel, auditorias: cargarEjecuciones, documentos: cargarDocumentos, expediente: cargarExpediente,
    cobertura: cargarCobertura, grafo: cargarGrafo, bitacoras: cargarBitacora, herramientas: cargarHerramientas, sistema: cargarSistema };
  (cargas[vista] || (() => Promise.resolve()))().catch(error);
  try { history.replaceState(null, "", "#" + vista); } catch (_) { /* sin historial */ }
}
document.addEventListener("click", (ev) => {
  const b = ev.target.closest("[data-vista],[data-ir]");
  if (b) irA(b.dataset.vista || b.dataset.ir);
});
$("#btn-menu").addEventListener("click", () => { $("#riel").classList.toggle("abierto"); moverIndicador(); });
/* Barra guinda que se desliza hasta la sección activa del menú. */
function moverIndicador() {
  const ind = $("#indicador"), item = $(".item.activa");
  if (!ind || !item || !item.offsetHeight) return;
  ind.style.transform = `translateY(${item.offsetTop + 8}px)`; ind.style.height = item.offsetHeight - 16 + "px";
  if (!ind.classList.contains("listo")) requestAnimationFrame(() => ind.classList.add("listo"));
}
window.addEventListener("resize", moverIndicador);
window.addEventListener("scroll", () => $(".barra").classList.toggle("elevada", scrollY > 6), { passive: true });

/* Diálogo que pide quién actúa (y a veces un motivo). Devuelve {actor, motivo} o null. */
function pedirMotivo({ titulo, texto, boton = "Confirmar", peligro = false, conMotivo = true }) {
  return new Promise((resolver) => {
    const dlg = $("#dlg-motivo");
    $("#motivo-titulo").textContent = titulo; $("#motivo-texto").textContent = texto;
    $("#motivo-actor").value = recordar("agente.auditor"); $("#motivo-motivo").value = "";
    $("#motivo-fila").hidden = !conMotivo;
    const b = $("#motivo-enviar"); b.textContent = boton; b.className = "boton " + (peligro ? "peligro lleno" : "primario");
    dlg.onclose = () => {
      if (dlg.returnValue !== "ok") return resolver(null);
      const actor = $("#motivo-actor").value.trim(); recordar("agente.auditor", actor);
      resolver({ actor, motivo: $("#motivo-motivo").value.trim() });
    };
    dlg.returnValue = ""; dlg.showModal(); $("#motivo-actor").focus();
  });
}

/* --------------------------------------------------------------------- señales */
async function cargarServicios() {
  const s = await api("/api/agente/sistema");
  const bd = $("#p-bd"), ia = $("#p-ia");
  bd.textContent = s.base_datos.ok ? "Base de datos conectada" : "Base de datos sin conexión"; bd.className = "senal " + (s.base_datos.ok ? "bien" : "mal");
  const n = s.ollama.modelos.length;
  const preparando = s.indices && s.indices.estado === "preparando";
  ia.textContent = !s.ollama.ok ? "IA local apagada" : preparando ? "IA local, preparando índices…" : `IA local, ${plural(n, "modelo")}`;
  ia.className = "senal " + (s.ollama.ok && !preparando ? "bien" : "aviso");
  ia.title = preparando ? "La búsqueda y las funciones con IA estarán listas en unos minutos; el resto ya funciona." : "Modelos locales (Ollama)";
  return s;
}

/* ----------------------------------------------------------------------- PANEL */
const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
function arco(cx, cy, r1, r2, a0, a1) {
  const p = (r, a) => [cx + r * Math.cos(a), cy + r * Math.sin(a)];
  const [x1, y1] = p(r2, a0), [x2, y2] = p(r2, a1), [x3, y3] = p(r1, a1), [x4, y4] = p(r1, a0);
  const g = a1 - a0 > Math.PI ? 1 : 0;
  return `M${x1.toFixed(2)},${y1.toFixed(2)} A${r2},${r2} 0 ${g} 1 ${x2.toFixed(2)},${y2.toFixed(2)} L${x3.toFixed(2)},${y3.toFixed(2)} A${r1},${r1} 0 ${g} 0 ${x4.toFixed(2)},${y4.toFixed(2)}Z`;
}
function pintarSello(cob, animar = false) {
  const filas = (cob.controles || []).filter((f) => f.estado !== "No aplica");
  const grupos = []; filas.forEach((f) => { const g = grupos.find((x) => x.g === f.grupo); g ? g.f.push(f) : grupos.push({ g: f.grupo, f: [f] }); });
  const total = filas.length, huecoG = 0.10, hueco = 0.022, util = Math.PI * 2 - huecoG * grupos.length;
  const paso = util / Math.max(1, total);
  let a = -Math.PI / 2 + huecoG / 2, segs = "", i = 0;
  grupos.forEach((g) => {
    g.f.forEach((f) => {
      const color = css(COLOR[f.estado] || "--e-sin");
      segs += `<path class="seg" tabindex="0" style="--i:${i++}" data-ref="${esc(f.ref)}" d="${arco(130, 130, 92, 118, a + hueco / 2, a + paso - hueco / 2)}" fill="${color}"><title>${esc(f.ref)} ${esc(f.titulo)}: ${esc(f.estado)}</title></path>`;
      a += paso;
    });
    a += huecoG;
  });
  const cubiertos = cob.conteo_estados?.Cubierto ?? 0, pct = Math.round(Number(cob.porcentaje_cobertura) || 0);
  const sello = $("#sello");
  sello.innerHTML = `<svg viewBox="0 0 260 260" aria-hidden="false">
      <defs><path id="anillo" d="M130,130 m-123,0 a123,123 0 1,1 246,0 a123,123 0 1,1 -246,0"/></defs>
      <g class="anillo-texto"><text class="texto-anillo"><textPath href="#anillo" textLength="768" lengthAdjust="spacing">UNIVERSIDAD NACIONAL DE SAN AGUSTÍN DE AREQUIPA · ISO/IEC 27701:2025 · EVIDENCIA Y AUDITORÍA ·</textPath></text></g>
      <circle cx="130" cy="130" r="84" fill="none" stroke="${css("--filete")}" stroke-width="1"/>
      <circle class="onda" cx="130" cy="130" r="118"/>
      ${segs}
    </svg>
    <div class="centro"><span class="cifra"><span id="sello-cifra">${pct}</span><sup>%</sup></span><small>${cubiertos} de ${total} controles</small></div>`;
  if (animar) { reanimar(sello, "animar"); contar($("#sello-cifra"), pct, 1300); }
  else sello.classList.remove("animar");
  $$("#sello .seg").forEach((s) => {
    const f = filas.find((x) => x.ref === s.dataset.ref);
    s.addEventListener("mouseenter", (e) => globo(e, f)); s.addEventListener("mousemove", (e) => globo(e, f));
    s.addEventListener("mouseleave", () => { $("#globo").hidden = true; });
    s.addEventListener("focus", (e) => { const r = e.target.getBoundingClientRect(); globo({ clientX: r.right, clientY: r.top }, f); });
    s.addEventListener("blur", () => { $("#globo").hidden = true; });
    const abrir = () => { $("#globo").hidden = true; estado.resaltar = f.ref; estado.filtro = ""; irA("cobertura"); };
    s.addEventListener("click", abrir); s.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); abrir(); } });
  });
}
function globo(e, f) {
  const g = $("#globo");
  g.innerHTML = `<b>${esc(f.ref)}</b>${esc(f.titulo)}<br>${esc(f.estado)}${f.evidencias?.length ? `, ${plural(f.evidencias.length, "evidencia")}` : ""}`;
  g.hidden = false;
  const x = Math.min(e.clientX + 14, innerWidth - g.offsetWidth - 10), y = Math.min(e.clientY + 14, innerHeight - g.offsetHeight - 10);
  g.style.left = x + "px"; g.style.top = y + "px";
}
function pintarDictamen(cob) {
  const c = cob.conteo_estados || {}, total = cob.controles_aplicables;
  const cub = c.Cubierto || 0, sin = c["Sin evidencia"] || 0, des = c.Desactualizada || 0, comp = c.Comprometida || 0, par = c.Parcial || 0;
  $("#dictamen-titulo").textContent = `${cub} de ${total} controles tienen evidencia vigente`;
  $("#dictamen-titulo").classList.remove("leyendo");
  const urgentes = (cob.controles || []).filter((f) => ["Comprometida", "Sin evidencia"].includes(f.estado) && f.grupo === "clausula").slice(0, 4).map((f) => f.ref);
  const partes = [];
  if (comp) partes.push(`${plural(comp, "control")} con evidencia alterada o faltante`);
  if (sin) partes.push(`${sin} sin evidencia`);
  if (des) partes.push(`${des} con evidencia vencida`);
  if (par) partes.push(`${par} con evidencia incompleta`);
  $("#dictamen-texto").textContent = (partes.length ? `Quedan ${partes.join(", ")}. ` : "Todos los controles aplicables están cubiertos. ") +
    (urgentes.length ? `Cláusulas por atender primero: ${urgentes.join(", ")}.` : "");
  $("#leyenda").innerHTML = ORDEN.filter((k) => k in c && k !== "No aplica").map((k) =>
    `<li><span class="muestra" style="background:var(${COLOR[k]})"></span>${esc(k)}<b data-contar="${esc(c[k])}">${esc(c[k])}</b></li>`).join("");
  if (estado.selloAnimar) contarTodo($("#leyenda"));
  $("#dictamen-corte").textContent = `Fecha de corte ${cob.fecha_corte}`;
  $("#dictamen-rol").textContent = `UNSA como ${cob.rol} del tratamiento`;
}
async function cargarIntegridad(animar = false) {
  const [r, c] = await Promise.all([api("/api/agente/resumen"), api("/api/agente/custodia?n=6")]);
  const i = r.integridad, malas = i.resultados.ALTERADA.length + i.resultados.FALTANTE.length;
  const cifra = $("#integ-cifra");
  cifra.textContent = r.evidencias === 0 ? "Vacío" : i.integro ? "Íntegro" : "Alerta";
  cifra.className = "cifra-grande " + (r.evidencias === 0 ? "" : i.integro ? "bien" : "mal");
  $("#integ-nota").textContent = r.evidencias === 0 ? "Todavía no hay evidencias." : i.integro ? `${plural(i.total, "evidencia")} con su huella intacta.`
    : `${malas ? plural(malas, "evidencia") + " alterada o faltante" : "La cadena de custodia tiene una rotura"}.`;
  const p = $("#p-integridad");
  p.textContent = r.evidencias === 0 ? "Expediente vacío" : i.integro ? "Expediente íntegro" : "Alerta de integridad";
  p.className = "senal " + (r.evidencias === 0 ? "" : i.integro ? "bien" : "mal");
  const cadena = $("#cadena");
  cadena.innerHTML = c.eslabones.slice().reverse().map((e, k) => `<li style="--i:${k}"><span class="eslabon">${esc(e.n)}</span>
    <span class="accion">${esc(ACCIONES_CUSTODIA[e.accion] || e.accion || "")} ${e.evidencia ? `<span class="ref">${esc(e.evidencia)}</span>` : ""}<small>${esc(fecha(e.fecha))}</small></span>
    <span class="huella" title="${esc(e.hash_linea)}" data-hash="${esc((e.hash_linea || "").slice(0, 10))}">${esc((e.hash_linea || "").slice(0, 10))}</span></li>`).join("") || '<li class="vacio">Sin eslabones todavía.</li>';
  if (animar && estado.vista === "panel") {
    reanimar(cadena, "entra");
    $$(".huella[data-hash]", cadena).forEach((h, k) => descifrar(h, h.dataset.hash, k * 90 + 120));
  }
  return r;
}
async function cargarResumenDocumentos() {
  try {
    const d = estado.documentos = await api("/api/agente/documentos-pims");
    const vig = d.conteo.Vigente || 0;
    const propios = d.lista_maestra.filter((f) => f.propio);
    $("#maestra-texto").textContent = `Lista maestra PIMS-RG-01: ${vig} de ${d.total} documentos de los ocho equipos vigentes y verificados con PIMS-PR-01. Abajo, los ${propios.length} del Grupo 6.`;
    const flecha = '<svg class="i flecha" viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg>';
    $("#docs-panel").innerHTML = propios.map((f) => {
      const dentro = `<span class="ref">${esc(f.codigo)}</span><span>${esc(f.titulo)}</span>${chip(f.situacion, "s")}`;
      return f.documento ? `<li><button type="button" class="doc-fila" data-doc="${esc(f.documento.id)}" title="Ver la ficha de ${esc(f.codigo)}">${dentro}${flecha}</button></li>`
        : `<li><div class="doc-fila">${dentro}<span></span></div></li>`;
    }).join("");
  } catch (err) { $("#maestra-texto").textContent = err.message; $("#docs-panel").innerHTML = ""; }
}
$("#docs-panel").addEventListener("click", (e) => { const b = e.target.closest("button[data-doc]"); if (b) abrirFicha(b.dataset.doc); });
async function cargarPanel() {
  const cob = estado.cobertura = await api("/api/agente/cobertura");
  /* El sello se estampa la primera vez y cuando cambia la cobertura; no en cada visita. */
  const firma = `${cob.porcentaje_cobertura}|${JSON.stringify(cob.conteo_estados || {})}`;
  estado.selloAnimar = firma !== estado.selloFirma; estado.selloFirma = firma;
  pintarSello(cob, estado.selloAnimar); pintarDictamen(cob);
  await Promise.all([cargarIntegridad(estado.selloAnimar), cargarEjecuciones(), cargarBandeja(), cargarServicios(), cargarResumenDocumentos()]);
  const ult = estado.ejecuciones.find((e) => e.tipo === "auditoria_interna");
  $("#ultima-auditoria").innerHTML = ult ? `Última: <button type="button" data-ejecucion="${esc(ult.id)}">${esc(fecha(ult.creado))}</button>, ${esc((NOMBRES[ult.estado] || ult.estado).toLowerCase())}.` : "Aún no se ha hecho ninguna auditoría.";
}
$("#ultima-auditoria").addEventListener("click", (e) => { const b = e.target.closest("[data-ejecucion]"); if (b) { irA("auditorias"); seleccionar(b.dataset.ejecucion, true).catch(error); } });
$("#btn-verificar-panel").addEventListener("click", (e) => verificarIntegridad(e.currentTarget));

/* ---------------------------------------------------------------- ejecuciones */
function itemEjecucion(e) {
  const est = e.pausa_solicitada && e.estado === "en_curso" ? "pausada" : e.estado;
  return `<li><button type="button" data-id="${esc(e.id)}" class="${e.id === estado.seleccionada ? "activa" : ""}">
    <strong>${esc(TIPOS[e.tipo] || e.tipo)}</strong>${chip(est)}<small>${esc(fecha(e.creado))}, <span class="huella">${esc(e.id)}</span></small></button></li>`;
}
async function cargarEjecuciones() {
  estado.ejecuciones = (await api("/api/agente/ejecuciones?proyecto=unsa")).filter((e) => e.tipo in TIPOS);
  pintarListas();
}
function pintarListas() {
  const vacio = '<li class="vacio">Aún no hay ejecuciones. Empieza con una auditoría desde el Panel.</li>';
  $("#lista-ejecuciones").innerHTML = estado.ejecuciones.length ? estado.ejecuciones.map(itemEjecucion).join("") : vacio;
  $("#lista-reciente").innerHTML = estado.ejecuciones.length ? estado.ejecuciones.slice(0, 5).map(itemEjecucion).join("") : vacio;
  const ab = estado.ejecuciones.filter((e) => ABIERTAS.includes(e.estado) || e.estado === "interrumpida").length;
  const c = $("#c-abiertas"); c.hidden = !ab; c.textContent = ab;
}
["#lista-ejecuciones", "#lista-reciente"].forEach((s) => $(s).addEventListener("click", (ev) => {
  const b = ev.target.closest("button[data-id]"); if (!b) return;
  if (estado.vista !== "auditorias") irA("auditorias");
  seleccionar(b.dataset.id, true).catch(error);
}));
$("#btn-refrescar").addEventListener("click", () => { cargarEjecuciones().catch(error); if (estado.seleccionada) seleccionar(estado.seleccionada, true).catch(error); });

async function seleccionar(id, forzar = false) {
  clearTimeout(estado.temporizador);
  if (estado.seleccionada !== id) { estado.firma = ""; estado.seleccionada = id; }
  const e = await api(`/api/agente/ejecuciones/${encodeURIComponent(id)}`);
  if (estado.seleccionada !== id) return;
  const i = estado.ejecuciones.findIndex((x) => x.id === id);
  if (i >= 0) estado.ejecuciones[i] = e; else estado.ejecuciones.unshift(e);
  pintarListas();
  const firma = `${e.estado}|${e.actualizado}|${e.paso_actual}|${!!e.pausa_solicitada}`;
  if (forzar || firma !== estado.firma) { estado.firma = firma; pintarDetalle(e); }
  if (e.estado === "en_curso") estado.temporizador = setTimeout(() => seleccionar(id).catch(() => {}), 2000);
}

function barraAcciones(e) {
  const b = [];
  if (e.estado === "en_curso") b.push(e.pausa_solicitada ? '<button class="boton" disabled>Pausando al terminar el paso…</button>' : '<button class="boton" data-accion="pausar">Pausar</button>');
  if (REANUDABLES.includes(e.estado)) b.push(`<button class="boton primario" data-accion="reanudar">${e.estado === "error" ? "Reintentar" : "Reanudar"}</button>`);
  if (ABIERTAS.includes(e.estado) || ["interrumpida", "error"].includes(e.estado)) b.push('<button class="boton peligro" data-accion="cancelar">Cancelar</button>');
  return b.length ? `<div class="barra-acciones">${b.join("")}</div>` : "";
}

function pintarDetalle(e) {
  let html = `<div class="cab-ejecucion"><h2>${esc(TIPOS[e.tipo] || e.tipo)}</h2>${chip(e.estado)}</div>
    <div class="meta"><span>Iniciada ${esc(fecha(e.creado))}</span><span>Actualizada ${esc(fecha(e.actualizado))}</span><span class="huella">${esc(e.id)}</span>
    ${e.parametros?.modo_rapido ? "<span>Modo rápido</span>" : e.tipo === "auditoria_interna" ? "<span>Con IA local</span>" : ""}</div>
    ${barraAcciones(e)}`;
  if (e.estado === "pausada" && e.pausa) html += `<div class="alerta info">Pausada por ${esc(e.pausa.actor || "")} el ${esc(fecha(e.pausa.fecha))}${e.pausa.motivo ? ": " + esc(e.pausa.motivo) : ""}. Al reanudar continúa en el paso siguiente, sin repetir lo hecho.</div>`;
  if (e.estado === "interrumpida") html += `<div class="alerta">Se interrumpió${e.interrupcion ? ` (${esc(e.interrupcion.motivo)})` : ""}. Puedes reanudarla desde el último paso guardado.</div>`;
  if (e.error) html += `<div class="alerta mal">Error: ${esc(e.error)}</div>`;
  if (e.cancelacion) html += `<div class="alerta mal">Cancelada el ${esc(fecha(e.cancelacion.fecha))} por ${esc(e.cancelacion.actor)}${e.cancelacion.motivo ? ": " + esc(e.cancelacion.motivo) : ""}. No genera informe.</div>`;
  if (e.estado === "esperando_aprobacion" && e.aprobacion) html += panelDecision(e);
  html += emitidos(e);
  /* Pasos que se completaron desde el último repintado: su marca aparece con un pequeño salto. */
  const vistos = estado.pasosVistos.get(e.id), okAhora = new Set();
  (e.pasos || []).forEach((p, i) => { if (p.estado === "ok") okAhora.add(i); });
  estado.pasosVistos.set(e.id, okAhora);
  html += `<h3>Pasos</h3><ol class="pasos${vistos ? "" : " entra"}">${(e.pasos || []).map((p, i) => {
    const est = p.estado === "en_curso" && e.estado === "esperando_aprobacion" ? "esperando" : p.estado;
    const recien = vistos && okAhora.has(i) && !vistos.has(i) ? " recien" : "";
    return `<li class="p-${clase(est)}${recien}" style="--i:${i}"><div class="titulo-paso">${esc(p.titulo || p.nodo)} ${p.estado !== "ok" ? chip(est === "esperando" ? "esperando_aprobacion" : p.estado) : ""}</div>
      ${p.resumen ? `<div class="resumen">${esc(p.resumen)}</div>` : ""}${p.inicio ? `<small>${esc(fecha(p.inicio))}</small>` : ""}</li>`;
  }).join("")}</ol>`;
  if (e.estado !== "esperando_aprobacion" && e.aprobacion?.hallazgos?.length && e.estado !== "completada") html += listaHallazgos(e.aprobacion.hallazgos);
  html += resultado(e);
  const det = $("#detalle"); det.innerHTML = html;
  $$("[data-accion]", det).forEach((b) => b.addEventListener("click", () => accion(e, b.dataset.accion, b)));
  if (e.estado === "esperando_aprobacion") conectarDecision(e);
  if (e.informe_nombre) cargarInforme(e.informe_nombre);
}

async function accion(e, nombre, boton) {
  const cfg = {
    pausar: { titulo: "Pausar", texto: "Se detiene al terminar el paso actual. El avance queda guardado.", boton: "Pausar" },
    reanudar: { titulo: e.estado === "error" ? "Reintentar" : "Reanudar", texto: "Continúa desde el último paso guardado, sin repetir lo hecho.", boton: e.estado === "error" ? "Reintentar" : "Reanudar", conMotivo: false },
    cancelar: { titulo: "Cancelar la ejecución", texto: "Se descarta: no genera informe ni plan de acción y no se podrá reanudar.", boton: "Cancelar ejecución", peligro: true },
  }[nombre];
  const r = await pedirMotivo(cfg);
  if (!r) return;
  if (!r.actor) return aviso("Escribe quién realiza la acción");
  boton.disabled = true;
  try {
    await api(`/api/agente/ejecuciones/${encodeURIComponent(e.id)}/${nombre}`, json({ actor: r.actor, motivo: r.motivo }));
    aviso({ pausar: "Pausa solicitada", reanudar: "Reanudada", cancelar: "Ejecución cancelada" }[nombre], "ok");
    await seleccionar(e.id, true);
  } catch (err) { boton.disabled = false; error(err); }
}

function listaHallazgos(h) {
  return `<h3>Hallazgos (${h.length}) ${PRELIMINAR}</h3><ul class="hallazgos">${h.map((x) => `<li><details>
    <summary><span class="ref">${esc(x.ref)}</span>${chip(x.estado, "e")}<span>${esc(String(x.clasificacion || "").split("(")[0])}</span></summary>
    <div class="md">${md(x.texto || "")}</div></details></li>`).join("")}</ul>`;
}

function panelDecision(e) {
  const a = e.aprobacion, props = a.propuestas || [];
  return `<div class="decision" id="decision"><h3>Tu decisión como auditor</h3>
    <p>${esc(a.pregunta || "Revisa los hallazgos preliminares y decide si se emite el informe.")}</p>
    ${props.length ? `<h3>Pertinencia de la evidencia (${props.length})</h3><p class="nota">El agente propone si la evidencia demuestra el requisito. Acepta o rechaza cada propuesta.</p>
      <ul class="hallazgos">${props.map((p, i) => `<li class="propuesta"><span><span class="ref">${esc(p.ref)}</span><br>${chip(p.veredicto, "v")}</span>
        <span class="nota">${esc(p.justificacion)}</span>
        <span class="eleccion"><label><input type="radio" name="dc-${i}" value="aceptada" data-ref="${esc(p.ref)}">Aceptar</label>
        <label><input type="radio" name="dc-${i}" value="rechazada" data-ref="${esc(p.ref)}">Rechazar</label></span></li>`).join("")}</ul>` : ""}
    ${listaHallazgos(a.hallazgos || [])}
    <div class="campos"><label>Auditor que valida<input type="text" id="dec-auditor" placeholder="Nombre del auditor" autocomplete="name"></label>
      <label>Comentario<input type="text" id="dec-comentario" placeholder="Opcional"></label></div>
    <div class="barra-acciones" style="border-bottom:0;margin-bottom:0"><button class="boton firma" data-decision="aprobada" type="button">Aprobar y emitir informe</button>
      <button class="boton peligro" data-decision="rechazada" type="button">Rechazar</button></div></div>`;
}

function conectarDecision(e) {
  const caja = $("#decision");
  $("#dec-auditor").value = recordar("agente.auditor");
  $$("button[data-decision]", caja).forEach((b) => b.addEventListener("click", async () => {
    const auditor = $("#dec-auditor").value.trim();
    if (!auditor) { $("#dec-auditor").focus(); return aviso("Escribe el nombre del auditor que valida"); }
    const dec = {};
    $$("input[type=radio][data-ref]:checked", caja).forEach((r) => { dec[r.dataset.ref] = r.value; });
    const faltan = (e.aprobacion.propuestas || []).length - Object.keys(dec).length;
    if (b.dataset.decision === "aprobada" && faltan > 0 && !confirm(`Quedan ${faltan} propuesta(s) de pertinencia sin decidir y no se registrará decisión sobre ellas. ¿Continuar?`)) return;
    recordar("agente.auditor", auditor);
    $$("button", caja).forEach((x) => { x.disabled = true; });
    try {
      await api(`/api/agente/ejecuciones/${encodeURIComponent(e.id)}/aprobar`, json({ decision: b.dataset.decision, auditor,
        comentario: $("#dec-comentario").value.trim(), decisiones_controles: dec }));
      const aprobada = b.dataset.decision === "aprobada";
      estampar(aprobada ? "Aprobado" : "Rechazado", `${auditor}, ${new Date().toLocaleDateString("es-PE", { dateStyle: "medium" })}`, !aprobada);
      aviso(aprobada ? "Aprobada: el agente está emitiendo el informe y el formulario PIMS-FO-01" : "Rechazada", "ok");
      await seleccionar(e.id, true);
    } catch (err) { $$("button", caja).forEach((x) => { x.disabled = false; }); error(err); }
  }));
}

function emitidos(e) {
  const r = e.resultado || {}, descargas = [];
  if (r.formulario_fo01?.ruta) descargas.push(`<a class="descarga" href="/api/agente/salidas/${encodeURIComponent(r.formulario_fo01.ruta)}" download><span class="tipo">DOCX</span>
    <span><strong>PIMS-FO-01</strong><small>${plural(r.formulario_fo01.registros, "no conformidad", "no conformidades")} con su acción correctiva</small></span></a>`);
  if (e.tipo === "auditoria_interna" && e.estado === "completada") descargas.push(`<a class="descarga" href="/api/agente/gestitel/exportar" download><span class="tipo">XLSX</span>
    <span><strong>Excel para GESTITEL</strong><small>Módulo Auditorías, listo para importar</small></span></a>`);
  return descargas.length ? `<h3>Documentos emitidos</h3><div class="descargas">${descargas.join("")}</div>` : "";
}

function resultado(e) {
  const r = e.resultado || {}, plan = r.plan_accion || [];
  let html = "";
  const cd = r.control_documental;
  if (cd?.resumen) html += `<h3>Control documental (PIMS-PR-01)</h3><p class="nota">${plural(cd.resumen.documentos, "documento PIMS revisado", "documentos PIMS revisados")}: ${cd.resumen.conformes} conformes, ${cd.resumen.con_observaciones} con observaciones y ${cd.resumen.no_conformes} no conformes. ${cd.pendientes?.length ? `Aún sin registrar: ${cd.pendientes.join(", ")}.` : ""}</p>`;
  if (plan.length) {
    html += `<h3>Plan de acción (${plan.length})</h3><div class="envoltura"><table class="tabla"><thead><tr><th>#</th><th>Control</th><th>Acción</th><th>Responsable</th><th>Fecha límite</th></tr></thead><tbody>
      ${plan.map((p) => `<tr><td class="num">${esc(p.prioridad ?? "")}</td><td><span class="ref">${esc(p.ref)}</span><br>${chip(p.estado, "e")}</td><td>${esc(p.accion)}</td><td>${esc(p.responsable)}</td><td class="mono">${esc(p.fecha_limite || "")}</td></tr>`).join("")}</tbody></table></div>`;
  }
  if (e.informe_nombre) html += `<div class="informe"><div class="cab"><h2>Informe de auditoría</h2><span class="huella">${esc(e.informe_nombre)}</span></div>
    <div id="informe-aviso"></div><div class="md" id="informe-md"><p class="tenue">Cargando informe…</p></div></div>`;
  return html;
}

async function cargarInforme(nombre) {
  try {
    const d = await api(`/api/agente/informe/${encodeURIComponent(nombre)}`);
    const caja = $("#informe-md"); if (!caja) return;
    caja.innerHTML = md(d.contenido);
    if (!/Validado por el auditor/i.test(d.contenido)) $("#informe-aviso").innerHTML = PRELIMINAR;
  } catch (err) { const c = $("#informe-md"); if (c) c.innerHTML = `<p class="alerta mal">${esc(err.message)}</p>`; }
}

/* ----------------------------------------------------------------- lanzadores */
$$("input[name=modo]").forEach((r) => r.addEventListener("change", () => {
  $("#opciones-ia").hidden = $("input[name=modo]:checked").value !== "ia";
}));
$("#btn-auditoria").addEventListener("click", async (ev) => {
  const b = ev.currentTarget, rapido = $("input[name=modo]:checked").value === "rapido";
  const parametros = { modo_rapido: rapido };
  if (!rapido) { parametros.max_hallazgos = Math.max(0, parseInt($("#max-hallazgos").value, 10) || 0); parametros.max_pertinencia = Math.max(0, parseInt($("#max-pertinencia").value, 10) || 0); }
  b.disabled = true; b.textContent = "Iniciando…"; b.classList.add("cargando");
  try {
    const e = await api("/api/agente/ejecuciones", json({ tipo: "auditoria_interna", proyecto: "unsa", parametros }));
    irA("auditorias"); await cargarEjecuciones(); await seleccionar(e.id, true);
  } catch (err) { error(err); } finally { b.disabled = false; b.textContent = "Iniciar auditoría"; b.classList.remove("cargando"); }
});
/* ---------------------------------------------------------------------- bandeja */
function zonaArrastre(zona, alSoltar) {
  ["dragenter", "dragover"].forEach((t) => zona.addEventListener(t, (e) => { e.preventDefault(); zona.classList.add("encima"); }));
  ["dragleave", "drop"].forEach((t) => zona.addEventListener(t, (e) => { e.preventDefault(); zona.classList.remove("encima"); }));
  zona.addEventListener("drop", (e) => alSoltar(e.dataTransfer.files));
}
zonaArrastre($("#zona-bandeja"), (f) => subirBandeja(f));
$("#archivo-bandeja").addEventListener("change", (e) => { subirBandeja(e.target.files); e.target.value = ""; });
async function subirBandeja(archivos) {
  if (!archivos || !archivos.length) return;
  const fd = new FormData(); [...archivos].forEach((a) => fd.append("archivo", a));
  $("#estado-bandeja").textContent = "Subiendo…";
  try {
    const r = await api("/api/agente/bandeja", { method: "POST", body: fd });
    $("#estado-bandeja").textContent = `En la bandeja: ${r.guardados.join(", ")}`;
    await cargarBandeja(); setTimeout(() => cargarEjecuciones().catch(() => {}), 3000);
  } catch (err) { $("#estado-bandeja").textContent = err.message; }
}
async function cargarBandeja() {
  const d = await api("/api/agente/bandeja");
  $("#lista-bandeja").innerHTML = d.archivos.length ? d.archivos.slice(0, 5).map((a) => `<li>${esc(a.nombre)} <small>${esc((a.bytes / 1024).toFixed(0))} KB</small></li>`).join("") : '<li class="tenue">La bandeja está vacía.</li>';
}

/* ------------------------------------------------------------ DOCUMENTOS PIMS */
function controlCelda(c) {
  if (!c) return '<span class="tenue">—</span>';
  const fallas = (c.reglas || []).filter((r) => !r.ok).length;
  return `${chip(c.resultado, "c")}${fallas ? `<br><small>${plural(fallas, "regla")} sin cumplir</small>` : ""}`;
}
async function cargarDocumentos() {
  const d = estado.documentos = await api("/api/agente/documentos-pims");
  const n = (k) => d.conteo[k] || 0;
  const conFallas = d.lista_maestra.filter((f) => f.documento && f.documento.control?.resultado && f.documento.control.resultado !== "conforme").length;
  $("#resumen-maestra").innerHTML = [["Vigentes", n("Vigente")], ["En borrador o vencidos", n("Borrador") + n("Vencido")],
    ["Sin registrar", n("Pendiente")], ["Con fallas de control", conFallas]].map(([t, v]) => `<div><b data-contar="${v}">${v}</b><small>${t}</small></div>`).join("");
  contarTodo($("#resumen-maestra"));
  $("#tabla-maestra tbody").innerHTML = d.lista_maestra.map((f) => `<tr class="${f.documento ? "clic" : ""}" ${f.documento ? `data-doc="${f.documento.id}" tabindex="0"` : ""}>
    <td><span class="ref">${esc(f.codigo)}</span>${f.documento ? `<br><small>versión ${esc(f.documento.version)}</small>` : ""}</td>
    <td class="titulo-celda"><strong>${esc(f.titulo)}</strong>${f.documento?.evidencia ? `<small>Evidencia ${esc(f.documento.evidencia)}</small>` : ""}${f.fuera_de_lista ? "<small>Fuera de la lista acordada</small>" : ""}</td>
    <td><small>${esc(f.agente_autor || "—")}</small>${f.expedientes?.length ? `<br><small class="tenue">${esc(f.expedientes.join(", "))}</small>` : ""}</td>
    <td>${(f.requisitos || []).map((r) => `<span class="ref">${esc(r)}</span>`).join(" ")}</td>
    <td>${chip(f.situacion, "s")}</td>
    <td>${f.documento ? controlCelda(f.documento.control) : '<span class="tenue">Sin entregar</span>'}</td></tr>`).join("");
}
$("#tabla-maestra").addEventListener("click", (e) => { const tr = e.target.closest("tr[data-doc]"); if (tr) abrirFicha(tr.dataset.doc); });
$("#tabla-maestra").addEventListener("keydown", (e) => { const tr = e.target.closest("tr[data-doc]"); if (tr && e.key === "Enter") abrirFicha(tr.dataset.doc); });

function listaReglas(reglas) {
  return `<ul class="reglas">${(reglas || []).map((r) => `<li class="${r.ok ? "" : "falla " + r.gravedad}"><span>${esc(r.regla)} <small>${esc(r.requisito)}${r.ok ? "" : r.gravedad === "mayor" ? ", impide usarlo como evidencia" : ", observación"}: ${esc(r.detalle)}</small></span></li>`).join("")}</ul>`;
}
function portada(m) {
  const filas = [["Código", m.codigo], ["Versión", m.version], ["Fecha de la versión", m.fecha_version], ["Creado por", m.creado_por],
    ["Aprobado por", m.aprobado_por], ["Nivel de confidencialidad", m.confidencialidad], ["Propietario", m.propietario], ["Válido hasta", m.valido_hasta]];
  return `<dl class="portada">${filas.map(([k, v]) => `<dt>${k}</dt><dd>${esc(v || "—")}</dd>`).join("")}</dl>`;
}
async function abrirFicha(id) {
  const f = $("#ficha"); f.innerHTML = '<p class="tenue">Cargando…</p>'; $("#dlg-ficha").showModal();
  try {
    const d = await api(`/api/agente/documentos-pims/${encodeURIComponent(id)}`);
    const hist = d.historial || [];
    f.innerHTML = `<div class="cab"><h2>${esc(d.titulo)}</h2><button class="boton mini" type="button" id="cerrar-ficha">Cerrar</button></div>
      <p>${chip(d.vigente ? "Vigente" : d.estado === "obsoleto" ? "Obsoleto" : "Borrador", "s")} ${chip(d.control?.resultado || "sin_verificar", "c")}</p>
      <p class="nota">Respalda ${(d.requisitos || []).map((r) => `<span class="ref">${esc(r)}</span>`).join(" ")}${d.expedientes?.length ? `, expediente ${esc(d.expedientes.join(", "))} de la guía` : ""}.</p>
      <div class="descargas"><a class="descarga" href="/api/agente/documentos-pims/${encodeURIComponent(d.id)}/archivo" download><span class="tipo">DOCX</span><span><strong>${esc(d.archivo)}</strong><small class="huella">${esc((d.sha256 || "").slice(0, 16))}…</small></span></a></div>
      <h3>Portada leída por el agente</h3>${portada(d)}
      <h3>Reglas de PIMS-PR-01</h3>${listaReglas(d.control?.reglas)}
      ${hist.length ? `<h3>Historial de modificaciones</h3><div class="envoltura"><table class="tabla"><thead><tr><th>Fecha</th><th>Versión</th><th>Autor</th><th>Cambio</th></tr></thead><tbody>${hist.map((h) => `<tr><td class="mono">${esc(h.fecha)}</td><td>${esc(h.version)}</td><td>${esc(h.autor)}</td><td>${esc(h.descripcion)}</td></tr>`).join("")}</tbody></table></div>` : ""}
      <h3>Contenido en la base de datos</h3><p class="tenue">${plural((d.secciones || []).length, "sección", "secciones")}, ${esc(d.caracteres)} caracteres. Es el texto que usan la búsqueda y la IA.</p>
      <div class="secciones">${(d.secciones || []).map((s) => `<details><summary>${esc(s.texto.split("\n")[0].slice(0, 90))}</summary><pre>${esc(s.texto)}</pre></details>`).join("")}</div>`;
    $("#cerrar-ficha").addEventListener("click", () => $("#dlg-ficha").close());
  } catch (err) { f.innerHTML = `<p class="alerta mal">${esc(err.message)}</p>`; }
}
$("#dlg-ficha").addEventListener("click", (e) => { if (e.target.id === "dlg-ficha") e.target.close(); });

$("#btn-subir-doc").addEventListener("click", async () => {
  estado.archivoDoc = null; $("#doc-previa").innerHTML = ""; $("#doc-campos").hidden = true; $("#doc-enviar").disabled = true;
  $("#doc-archivo-nombre").textContent = "Arrastra el .docx o elige"; $("#doc-por").value = recordar("agente.auditor");
  await cargarCatalogo().catch(() => {});
  $("#dlg-documento").showModal();
});
zonaArrastre($("#zona-doc"), (f) => previsualizarDoc(f[0]));
$("#doc-archivo").addEventListener("change", (e) => { previsualizarDoc(e.target.files[0]); e.target.value = ""; });
async function previsualizarDoc(archivo) {
  if (!archivo) return;
  estado.archivoDoc = archivo; $("#doc-archivo-nombre").textContent = archivo.name;
  $("#doc-previa").innerHTML = '<p class="tenue">Leyendo la portada…</p>';
  const fd = new FormData(); fd.append("archivo", archivo);
  try {
    const r = await api("/api/agente/documentos-pims/previsualizar", { method: "POST", body: fd });
    const c = r.control, m = r.metadatos;
    const veredicto = c.resultado === "conforme" ? '<div class="alerta bien">Cumple todas las reglas de PIMS-PR-01.</div>'
      : c.resultado === "observaciones" ? `<div class="alerta">Se puede registrar, con ${plural(c.fallas_menores, "observación", "observaciones")}.</div>`
        : `<div class="alerta mal">Tiene ${plural(c.fallas_mayores, "falla mayor", "fallas mayores")}: se registrará como ${c.estado === "borrador" ? "borrador" : "documento no conforme"} y la auditoría lo informará en la cláusula 7.5.</div>`;
    $("#doc-previa").innerHTML = `${veredicto}<h3>${esc(m.codigo || "Sin código")} ${esc(m.titulo || "")}</h3>${portada(m)}<details><summary>Reglas revisadas</summary>${listaReglas(c.reglas)}</details>`;
    $("#doc-requisitos").value = (r.sugerencia.requisitos || []).join(", ");
    $("#doc-campos").hidden = false; $("#doc-enviar").disabled = !m.codigo;
  } catch (err) { $("#doc-previa").innerHTML = `<div class="alerta mal">${esc(err.message)}</div>`; $("#doc-enviar").disabled = true; }
}
$("#dlg-documento").addEventListener("close", async (ev) => {
  if (ev.currentTarget.returnValue !== "ok" || !estado.archivoDoc) return;
  const por = $("#doc-por").value.trim();
  if (!por) return aviso("Escribe quién registra el documento");
  recordar("agente.auditor", por);
  const fd = new FormData(); fd.append("archivo", estado.archivoDoc); fd.append("registrado_por", por);
  fd.append("requisitos", $("#doc-requisitos").value);
  try {
    const d = await api("/api/agente/documentos-pims", { method: "POST", body: fd });
    aviso(d.ya_registrado ? `${d.codigo} versión ${d.version} ya estaba registrado` : `${d.codigo} versión ${d.version} registrado en la base de datos`, "ok");
    await cargarDocumentos();
  } catch (err) { error(err); }
});
$("#btn-reverificar").addEventListener("click", async (e) => {
  const b = e.currentTarget; b.disabled = true;
  try {
    const r = await api("/api/agente/documentos-pims/verificar", { method: "POST" });
    const malos = r.resultados.filter((x) => x.resultado !== "conforme").length;
    aviso(malos ? `${plural(malos, "documento")} con fallas de control` : `Los ${r.resultados.length} documentos cumplen PIMS-PR-01`, malos ? "mal" : "ok");
    await cargarDocumentos();
  } catch (err) { error(err); } finally { b.disabled = false; }
});

/* ------------------------------------------------------------------ expediente */
async function cargarExpediente() {
  const d = await api("/api/agente/expediente");
  const ev = d.evidencias;
  $("#exp-nota").textContent = plural(ev.length, "evidencia");
  $("#tabla-expediente tbody").innerHTML = ev.length ? ev.map((x) => `<tr><td><span class="ref">${esc(x.id)}</span></td>
    <td class="titulo-celda"><strong>${esc(x.titulo)}</strong><small>${esc(x.archivo)}</small></td>
    <td>${esc(x.tipo)}</td><td>${(x.controles || []).map((c) => `<span class="ref">${esc(c)}</span>`).join(" ") || "—"}</td>
    <td class="mono">${esc(x.fecha_documento || "—")}</td><td class="huella" title="${esc(x.sha256)}">${esc((x.sha256 || "").slice(0, 16))}…</td></tr>`).join("")
    : '<tr><td colspan="6" class="vacio">El expediente está vacío. Registra la primera evidencia o sube un documento PIMS.</td></tr>';
}
async function verificarIntegridad(b) {
  b.disabled = true; b.classList.add("cargando");
  const cadena = $("#cadena"), enPanel = estado.vista === "panel";
  if (enPanel) { cadena.style.setProperty("--alto", cadena.offsetHeight + "px"); cadena.classList.add("escaneando"); }
  try {
    /* El escaneo dura al menos un barrido completo para que se vea qué se está revisando. */
    const [r] = await Promise.all([api("/api/agente/expediente/verificar", { method: "POST" }), espera(enPanel && !movimientoReducido.matches ? 900 : 0)]);
    const malas = ["ALTERADA", "FALTANTE"].reduce((n, k) => n + ((r.resultados || {})[k] || []).length, 0);
    aviso(r.integro ? `${plural(r.total, "evidencia")} verificadas: todas íntegras` : `Atención: ${malas ? plural(malas, "evidencia") + " con fallo" : "la cadena de custodia tiene una rotura"}`, r.integro ? "ok" : "mal");
    if (enPanel) { cadena.classList.remove("escaneando"); await cargarIntegridad(true).catch(() => {}); reanimar($("#integ-cifra"), "pop"); }
    if (estado.vista === "expediente") $$("#tabla-expediente tbody tr").forEach((tr, i) => { tr.style.setProperty("--i", i); tr.classList.remove("verificada", "fallida"); reanimar(tr, r.integro ? "verificada" : "fallida"); });
  } catch (err) { error(err); } finally { b.disabled = false; b.classList.remove("cargando"); cadena.classList.remove("escaneando"); }
}
$("#btn-verificar").addEventListener("click", (e) => verificarIntegridad(e.currentTarget));
async function cargarCatalogo() {
  if ($("#ev-tipo").options.length) return;
  const c = await api("/api/agente/catalogo");
  $("#ev-tipo").innerHTML = c.tipos.map((t) => `<option>${esc(t)}</option>`).join("");
  $("#lista-controles").innerHTML = c.controles.map((x) => `<option value="${esc(x.ref)}">${esc(x.titulo)}</option>`).join("");
}
$("#btn-nueva-evidencia").addEventListener("click", async () => {
  await cargarCatalogo().catch(error);
  $("#form-evidencia").elements.responsable.value = recordar("agente.auditor");
  $("#dlg-evidencia").showModal();
});
$("#dlg-evidencia").addEventListener("close", async (ev) => {
  if (ev.currentTarget.returnValue !== "ok") return;
  const form = $("#form-evidencia"), fd = new FormData(form);
  recordar("agente.auditor", fd.get("responsable"));
  try {
    const r = await api("/api/agente/expediente", { method: "POST", body: fd });
    aviso(`Evidencia ${r.id} registrada`, "ok"); form.reset(); cargarExpediente().catch(() => {});
  } catch (err) { error(err); }
});

/* ------------------------------------------------------------------- cobertura */
async function cargarCobertura() {
  const c = estado.cobertura = await api("/api/agente/cobertura");
  $("#cob-nota").textContent = `${c.porcentaje_cobertura} % de ${c.controles_aplicables} controles`;
  const claves = Object.keys(c.conteo_estados).filter((k) => c.conteo_estados[k]).sort((a, b) => ORDEN.indexOf(a) - ORDEN.indexOf(b));
  $("#filtro-cobertura").innerHTML = [["", `Todos`]].concat(claves.map((k) => [k, `${k} (${c.conteo_estados[k]})`]))
    .map(([v, t]) => `<button type="button" data-filtro="${esc(v)}" class="${estado.filtro === v ? "activa" : ""}">${esc(t)}</button>`).join("");
  pintarCobertura();
}
function pintarCobertura() {
  const filas = (estado.cobertura?.controles || []).filter((f) => !estado.filtro || f.estado === estado.filtro);
  $("#tabla-cobertura tbody").innerHTML = filas.length ? filas.map((f) => `<tr id="fila-${clase(f.ref)}" class="${estado.resaltar === f.ref ? "resaltada" : ""}">
    <td><span class="ref">${esc(f.ref)}</span></td><td>${esc(f.titulo || "")}</td><td>${chip(f.estado, "e")}</td>
    <td class="num">${esc((f.evidencias || []).length)}</td><td class="nota">${esc(f.nota || "")}</td></tr>`).join("") : '<tr><td colspan="5" class="vacio">No hay controles en este estado.</td></tr>';
  if (estado.resaltar) { const fila = $(`#fila-${clase(estado.resaltar)}`); if (fila) fila.scrollIntoView({ block: "center" }); estado.resaltar = null; }
}
$("#filtro-cobertura").addEventListener("click", (e) => {
  const b = e.target.closest("[data-filtro]"); if (!b) return;
  estado.filtro = b.dataset.filtro;
  $$("#filtro-cobertura button").forEach((x) => x.classList.toggle("activa", x === b));
  pintarCobertura();
});

/* ------------------------------------------------------------------- bitácoras */
const CAMPOS_FECHA = ["fecha", "momento", "ts", "timestamp", "hora", "creado"], CAMPOS_TIPO = ["decision", "tipo", "evento", "herramienta", "accion", "nodo"];
$("#subpestanas").addEventListener("click", (e) => {
  const b = e.target.closest("[data-bitacora]"); if (!b) return;
  estado.bitacora = b.dataset.bitacora;
  $$("#subpestanas button").forEach((x) => x.classList.toggle("activa", x === b));
  cargarBitacora().catch(error);
});
async function cargarBitacora() {
  const d = await api(`/api/agente/bitacora?tipo=${encodeURIComponent(estado.bitacora)}`);
  $("#tabla-bitacora thead").innerHTML = "<tr><th>Fecha</th><th>Qué pasó</th><th>Detalle</th></tr>";
  $("#tabla-bitacora tbody").innerHTML = d.registros.length ? d.registros.map((r) => {
    const resto = { ...r }, kf = CAMPOS_FECHA.find((k) => k in r), kt = CAMPOS_TIPO.find((k) => k in r);
    if (kf) delete resto[kf]; if (kt) delete resto[kt];
    return `<tr><td class="mono">${esc(kf ? fecha(r[kf]) : "")}</td><td><strong>${esc(kt ? r[kt] : "")}</strong>${r.actor ? `<br><small>${esc(r.actor)}</small>` : ""}</td><td><pre>${esc(JSON.stringify(resto, null, 1))}</pre></td></tr>`;
  }).join("") : '<tr><td colspan="3" class="vacio">Sin registros todavía.</td></tr>';
}

async function cargarHerramientas() {
  const lista = await api("/api/agente/herramientas");
  $("#tabla-herramientas tbody").innerHTML = lista.map((h) => `<tr><td><span class="ref">${esc(h.nombre)}</span><br><small class="huella">${esc(h.firma)}</small></td>
    <td>${h.ia ? '<span class="estado x-en-curso">Con IA local</span>' : '<span class="estado">Determinista</span>'}</td><td><pre>${esc(h.doc)}</pre></td></tr>`).join("");
}

/* -------------------------------------------------------------- datos y sistema */
async function cargarSistema() {
  const s = await cargarServicios();
  $("#lista-servicios").innerHTML = [
    ["PostgreSQL", s.base_datos.ok, s.base_datos.detalle],
    ["Ollama (IA local)", s.ollama.ok, s.ollama.ok ? s.ollama.modelos.join(", ") || "sin modelos" : "no responde en el puerto 11434"],
    ["Orquestador LangGraph", s.orquestador_real, s.orquestador_real ? "activo" : "sustituto provisional"]]
    .map(([n, ok, d]) => `<li><span class="punto ${ok ? "ok" : ""}"></span><div><b>${esc(n)}</b><small>${esc(d)}</small></div></li>`).join("");
  const filas = s.base_datos.filas || {}, claves = Object.keys(filas);
  $("#tabla-filas tbody").innerHTML = claves.length ? claves.map((k) => `<tr><td class="mono">${esc(k)}</td><td class="num">${esc(filas[k])}</td></tr>`).join("") : '<tr><td class="vacio">Sin datos</td></tr>';
  return s;
}
$("#btn-refrescar-sistema").addEventListener("click", () => cargarSistema().catch(error));
$("#btn-vaciar").addEventListener("click", async () => {
  const s = await api("/api/agente/sistema");
  const filas = Object.entries(s.base_datos.filas || {}).filter(([, n]) => n > 0);
  $("#vaciar-resumen").innerHTML = (filas.length ? filas.map(([k, n]) => `<li>${esc(n)} filas de <span class="mono">${esc(k)}</span></li>`).join("") : "<li>La base ya está vacía</li>") +
    "<li>Archivos del expediente, índices, informes y bandeja</li>";
  $("#vaciar-actor").value = recordar("agente.auditor"); $("#vaciar-confirma").value = ""; $("#vaciar-enviar").disabled = true;
  $("#dlg-vaciar").showModal();
});
$("#vaciar-confirma").addEventListener("input", (e) => { $("#vaciar-enviar").disabled = e.target.value.trim() !== "VACIAR"; });
$("#dlg-vaciar").addEventListener("close", async (ev) => {
  if (ev.currentTarget.returnValue !== "ok") return;
  const actor = $("#vaciar-actor").value.trim(); recordar("agente.auditor", actor);
  try {
    const r = await api("/api/agente/base/vaciar", json({ confirmar: "VACIAR", actor }));
    const n = Object.values(r.filas || {}).reduce((a, b) => a + b, 0);
    aviso(`Base vaciada: ${n} filas y ${r.carpetas.length} archivos o carpetas`, "ok");
    estado.seleccionada = null; $("#detalle").innerHTML = '<p class="vacio">Elige una ejecución para ver sus pasos.</p>';
    await cargarSistema();
  } catch (err) { error(err); }
});

/* ----------------------------------------------------------------- tema claro/oscuro */
/* Sin preferencia guardada se sigue al sistema; el botón fija claro u oscuro y lo recuerda. */
const oscuroSistema = window.matchMedia("(prefers-color-scheme: dark)");
function temaActual() {
  const t = document.documentElement.dataset.theme;
  return t ? (t === "dark" ? "oscuro" : "claro") : (oscuroSistema.matches ? "oscuro" : "claro");
}
function etiquetaTema() {
  const destino = temaActual() === "oscuro" ? "claro" : "oscuro";
  const b = $("#btn-tema");
  b.setAttribute("aria-label", `Cambiar a modo ${destino}`); b.title = `Cambiar a modo ${destino}`;
}
function repintarTema() {
  etiquetaTema();
  if (estado.cobertura && $("#sello").innerHTML) pintarSello(estado.cobertura);   // el sello lee los colores del tema
}
$("#btn-tema").addEventListener("click", (ev) => {
  const nuevo = temaActual() === "oscuro" ? "claro" : "oscuro";
  const aplicar = () => { document.documentElement.dataset.theme = nuevo === "oscuro" ? "dark" : "light"; recordar("agente.tema", nuevo); repintarTema(); };
  if (!document.startViewTransition || movimientoReducido.matches) return aplicar();
  /* El tema nuevo se revela en un círculo que crece desde el botón. */
  const r = ev.currentTarget.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2;
  const radio = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
  document.startViewTransition(aplicar).ready.then(() => document.documentElement.animate(
    { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${radio}px at ${x}px ${y}px)`] },
    { duration: 560, easing: "cubic-bezier(.4, 0, .2, 1)", pseudoElement: "::view-transition-new(root)" })).catch(() => {});
});
oscuroSistema.addEventListener("change", () => { if (!document.documentElement.dataset.theme) repintarTema(); });
etiquetaTema();

/* --------------------------------------------------------------- GRAFO DE CONOCIMIENTO */
/* Mismo grafo del Entregable 1 (grafo.py): fuentes del RAG, grupos, controles, remisiones de la
   norma, semejanza FAISS y evidencias, más los documentos PIMS de este agente.
   Disposición por fuerzas en SVG, sin librerías; las posiciones se conservan al actualizar. */
const SVG_NS = "http://www.w3.org/2000/svg";
const grafo = { datos: null, nodos: [], aristas: [], porId: new Map(), vecinos: new Map(), pos: new Map(),
  vista: { x: 0, y: 0, k: 1 }, seleccion: null, calor: 0, animando: false,
  filtros: { documentos: true, evidencia: true, semejanza: true, remite: true, estructura: true } };
const RADIO = { agente: 20, proyecto: 15, fuente: 11, grupo: 12, control: 8, evidencia: 7, documento: 9 };
const LARGO = { conoce: 130, audita: 170, organiza: 120, define: 150, incluye: 55, remite: 90, semejanza: 80, aporta: 70,
  respalda: 80, elabora: 120, documenta: 110, registrado: 60 };
const FUERZA = { semejanza: 0.012, remite: 0.02, define: 0.01, aporta: 0.02, documenta: 0.02, registrado: 0.03 };
const ESTRUCTURA = new Set(["conoce", "audita", "organiza", "define", "incluye"]);
const DOCUMENTALES = new Set(["elabora", "documenta", "registrado"]);
const RELACION = {
  conoce: ["conoce", "conocida por"], audita: ["audita", "auditada por"], organiza: ["organiza", "organizado por"],
  define: ["define", "definido en"], incluye: ["incluye", "pertenece a"], remite: ["remite a", "citado por"],
  semejanza: ["semejante a", "semejante a"], aporta: ["aporta", "aportada por"], respalda: ["respalda", "respaldado por"],
  elabora: ["elabora", "elaborado por"],
  documenta: ["documenta", "documentado en"], registrado: ["registrado como", "registro de"],
};
const TIPO_NODO = { agente: "Este agente", fuente: "Fuente de conocimiento", grupo: "Grupo de controles", control: "Control",
  proyecto: "Organización auditada", evidencia: "Evidencia", documento: "Documento PIMS" };

function svgEl(nombre, attrs = {}) {
  const e = document.createElementNS(SVG_NS, nombre);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  return e;
}
async function cargarGrafo() {
  try {
    armarGrafo(await api("/api/agente/grafo"));
  } catch (err) { $("#grafo-vacio").textContent = err.message; $("#grafo-vacio").hidden = false; }
}
function posicionInicial(n, grupos, fuentes, azar) {
  if (n.tipo === "fuente") { const a = Math.PI + (fuentes.indexOf(n.id) + 0.5) / fuentes.length * Math.PI; return { x: 150 * Math.cos(a), y: 150 * Math.sin(a) }; }
  if (n.tipo === "grupo" || n.tipo === "control") {
    const i = grupos.indexOf(n.tipo === "grupo" ? n.id : "grp:" + n.grupo), a = Math.PI + (i + 0.5) / grupos.length * Math.PI;
    const r = n.tipo === "grupo" ? 260 : 340;
    return { x: r * Math.cos(a) + azar() * 90, y: r * Math.sin(a) + azar() * 90 };
  }
  if (n.tipo === "documento") return { x: azar() * 500, y: 320 + azar() * 120 };
  if (n.tipo === "proyecto") return { x: 0, y: 200 };
  if (n.tipo === "evidencia") return { x: azar() * 260, y: 260 + azar() * 60 };
  return { x: 0, y: 0 };
}
function armarGrafo(d) {
  grafo.datos = d;
  let semilla = 7;
  const azar = () => (semilla = (semilla * 16807) % 2147483647) / 2147483647 - 0.5;
  const ids = (t) => d.nodos.filter((n) => n.tipo === t).map((n) => n.id);
  const grupos = ids("grupo"), fuentes = ids("fuente");
  const nuevos = d.nodos.filter((n) => !grafo.pos.has(n.id)).length;
  grafo.nodos = d.nodos.map((n) => ({ ...n, ...(grafo.pos.get(n.id) || posicionInicial(n, grupos, fuentes, azar)),
    vx: 0, vy: 0, r: RADIO[n.tipo] || 8, fijo: n.tipo === "agente" }));
  grafo.porId = new Map(grafo.nodos.map((n) => [n.id, n]));
  grafo.aristas = d.aristas.filter((a) => grafo.porId.has(a.origen) && grafo.porId.has(a.destino))
    .map((a) => ({ ...a, o: grafo.porId.get(a.origen), d: grafo.porId.get(a.destino) }));
  grafo.vecinos = new Map(grafo.nodos.map((n) => [n.id, []]));
  grafo.aristas.forEach((a) => {
    const rel = RELACION[a.tipo] || [a.tipo, a.tipo];
    grafo.vecinos.get(a.origen).push({ a, otro: a.d, rel: rel[0] });
    grafo.vecinos.get(a.destino).push({ a, otro: a.o, rel: rel[1] });
  });
  if (!grafo.porId.has(grafo.seleccion)) grafo.seleccion = null;
  dibujarGrafo();
  if (nuevos) { for (let i = 0; i < 400; i++) pasoFuerzas(Math.max(0.03, 1 - i / 400)); actualizarPosiciones(); encuadrar(); brotar(); }
  else { actualizarPosiciones(); aplicarVista(); }
  aplicarFiltros(); pintarResumenGrafo();
  if (grafo.seleccion) seleccionarNodo(grafo.seleccion, false); else $("#grafo-detalle").innerHTML = '<p class="tenue">Pulsa un nodo para ver qué es y con qué se relaciona.</p>';
  $("#grafo-vacio").hidden = true;
}
/* Primera vez: los nodos brotan desde el agente hacia afuera, en orden de distancia. */
function brotar() {
  const svg = $("#grafo-svg"), centro = grafo.nodos.find((n) => n.tipo === "agente") || { x: 0, y: 0 };
  const dist = (n) => Math.hypot(n.x - centro.x, n.y - centro.y), max = Math.max(1, ...grafo.nodos.map(dist));
  const t = (n) => Math.round(dist(n) / max * 1100);
  grafo.nodos.forEach((n) => n.el.style.setProperty("--t", t(n) + "ms"));
  grafo.aristas.forEach((a) => a.el.style.setProperty("--t", Math.max(t(a.o), t(a.d)) + "ms"));
  reanimar(svg, "brota");
  clearTimeout(grafo.brote); grafo.brote = setTimeout(() => svg.classList.remove("brota"), 1900);
}
function visibleNodo(n) {
  if (n.tipo === "evidencia") return grafo.filtros.evidencia;
  if (n.tipo === "documento") return grafo.filtros.documentos;
  return true;
}
function visibleArista(a) {
  const f = grafo.filtros;
  if (!visibleNodo(a.o) || !visibleNodo(a.d)) return false;
  if (a.tipo === "semejanza") return f.semejanza;
  if (a.tipo === "remite") return f.remite;
  if (ESTRUCTURA.has(a.tipo)) return f.estructura;
  if (DOCUMENTALES.has(a.tipo)) return f.documentos;
  return f.evidencia;
}
function pasoFuerzas(alfa) {
  const ns = grafo.nodos;
  for (let i = 0; i < ns.length; i++) for (let j = i + 1; j < ns.length; j++) {
    const a = ns[i], b = ns[j];
    let dx = b.x - a.x, dy = b.y - a.y; if (!dx && !dy) { dx = 0.5; dy = 0.3; }
    const d2 = Math.max(dx * dx + dy * dy, 64), d = Math.sqrt(d2), f = (2600 + 120 * (a.r + b.r)) * alfa / d2 / d;
    a.vx -= dx * f; a.vy -= dy * f; b.vx += dx * f; b.vy += dy * f;
  }
  for (const a of grafo.aristas) {
    const dx = a.d.x - a.o.x, dy = a.d.y - a.o.y, d = Math.sqrt(dx * dx + dy * dy) || 1;
    const fuerza = (FUERZA[a.tipo] ?? 0.06) * (a.tipo === "semejanza" ? (a.similitud || 0.9) : 1);
    const k = (d - (LARGO[a.tipo] || 80)) / d * fuerza * alfa;
    a.o.vx += dx * k; a.o.vy += dy * k; a.d.vx -= dx * k; a.d.vy -= dy * k;
  }
  for (const n of ns) {
    if (n.fijo) { n.vx = n.vy = 0; continue; }
    n.vx = (n.vx - n.x * 0.003 * alfa) * 0.6; n.vy = (n.vy - n.y * 0.003 * alfa) * 0.6;
    n.x += n.vx; n.y += n.vy;
  }
}
function calentar(c = 0.3) {
  grafo.calor = Math.max(grafo.calor, c);
  if (grafo.animando) return;
  grafo.animando = true;
  const cuadro = () => {
    for (let i = 0; i < 2; i++) pasoFuerzas(grafo.calor);
    actualizarPosiciones(); grafo.calor *= 0.97;
    if (grafo.calor > 0.02) requestAnimationFrame(cuadro); else grafo.animando = false;
  };
  requestAnimationFrame(cuadro);
}
function formaNodo(n) {
  const r = n.r;
  let forma;
  if (n.tipo === "fuente") forma = svgEl("rect", { x: -r, y: -r, width: 2 * r, height: 2 * r, rx: 4 });
  else if (n.tipo === "evidencia") forma = svgEl("rect", { x: -r, y: -r, width: 2 * r, height: 2 * r, rx: 1.5 });
  else if (n.tipo === "grupo") { const q = r * 1.13; forma = svgEl("path", { d: `M0,${-q} L${q},0 L0,${q} L${-q},0Z` }); }   // rombo sin transform: la escala CSS no lo pisa
  else if (n.tipo === "documento") forma = svgEl("path", { d: `M${-r * 0.8},${-r} h${r} l${r * 0.6},${r * 0.6} v${r * 1.4} h${-r * 1.6}z` });
  else forma = svgEl("circle", { r });
  let cls = "forma n-" + n.tipo;
  if (n.tipo === "control") cls += " est-" + clase(n.estado);
  if (n.tipo === "evidencia") cls += " int-" + clase(n.integridad);
  if (n.tipo === "documento") cls += " s-" + clase(n.situacion);
  forma.setAttribute("class", cls);
  return forma;
}
function dibujarGrafo() {
  const svg = $("#grafo-svg"); svg.innerHTML = "";
  const capa = svgEl("g", { id: "grafo-capa" }), capaA = svgEl("g"), capaN = svgEl("g");
  for (const a of grafo.aristas) {
    a.el = svgEl("line", { class: "arista a-" + a.tipo });
    if (a.tipo === "semejanza") a.el.style.setProperty("--op", Math.min(1, 0.35 + (a.similitud - 0.85) * 8));
    const t = svgEl("title"); t.textContent = `${a.o.etiqueta} ${(RELACION[a.tipo] || [a.tipo])[0]} ${a.d.etiqueta}` + (a.similitud ? ` (coseno ${a.similitud})` : "");
    a.el.appendChild(t); capaA.appendChild(a.el);
  }
  for (const n of grafo.nodos) {
    n.el = svgEl("g", { class: "nodo t-" + n.tipo, "data-id": n.id, tabindex: "0" });
    n.el.appendChild(formaNodo(n));
    const texto = svgEl("text", { y: n.r + 12, "text-anchor": "middle" });
    const etq = n.etiqueta;
    texto.textContent = etq.length > 30 ? etq.slice(0, 28) + "…" : etq;
    n.el.appendChild(texto);
    const t = svgEl("title"); t.textContent = n.titulo ? `${n.etiqueta}: ${n.titulo}` : n.etiqueta; n.el.appendChild(t);
    capaN.appendChild(n.el);
  }
  capa.append(capaA, capaN); svg.appendChild(capa);
}
function actualizarPosiciones() {
  for (const a of grafo.aristas) {
    a.el.setAttribute("x1", a.o.x.toFixed(1)); a.el.setAttribute("y1", a.o.y.toFixed(1));
    a.el.setAttribute("x2", a.d.x.toFixed(1)); a.el.setAttribute("y2", a.d.y.toFixed(1));
  }
  for (const n of grafo.nodos) { n.el.setAttribute("transform", `translate(${n.x.toFixed(1)},${n.y.toFixed(1)})`); grafo.pos.set(n.id, { x: n.x, y: n.y }); }
}
function aplicarVista() {
  const svg = $("#grafo-svg"), capa = $("#grafo-capa"); if (!capa) return;
  const v = grafo.vista;
  capa.setAttribute("transform", `translate(${svg.clientWidth / 2 + v.x},${svg.clientHeight / 2 + v.y}) scale(${v.k})`);
}
function encuadrar() {
  const ns = grafo.nodos.filter(visibleNodo), svg = $("#grafo-svg");
  if (!ns.length || !svg.clientWidth) return;
  const xs = ns.map((n) => n.x), ys = ns.map((n) => n.y);
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const k = Math.min(svg.clientWidth / (x1 - x0 + 120), svg.clientHeight / (y1 - y0 + 120), 1.8);
  grafo.vista = { k, x: -((x0 + x1) / 2) * k, y: -((y0 + y1) / 2) * k };
  aplicarVista();
}
function aplicarFiltros() {
  grafo.nodos.forEach((n) => { n.el.style.display = visibleNodo(n) ? "" : "none"; });
  grafo.aristas.forEach((a) => { a.el.style.display = visibleArista(a) ? "" : "none"; });
}
function enfocar(id) {
  const svg = $("#grafo-svg");
  $$(".vecino, .vecina", svg).forEach((e) => e.classList.remove("vecino", "vecina"));
  const n = grafo.porId.get(id);
  svg.classList.toggle("enfocado", !!n);
  if (!n) return;
  n.el.classList.add("vecino");
  for (const { a, otro } of grafo.vecinos.get(id)) { if (!visibleArista(a)) continue; a.el.classList.add("vecina"); otro.el.classList.add("vecino"); }
}
function seleccionarNodo(id, centrar = true) {
  const n = grafo.porId.get(id);
  grafo.seleccion = n ? id : null;
  grafo.nodos.forEach((x) => x.el.classList.toggle("seleccionado", x.id === grafo.seleccion));
  enfocar(grafo.seleccion);
  if (!n) { $("#grafo-detalle").innerHTML = ""; return; }
  if (centrar) { grafo.vista.x = -n.x * grafo.vista.k; grafo.vista.y = -n.y * grafo.vista.k; aplicarVista(); }
  pintarDetalleNodo(n);
}
function pintarDetalleNodo(n) {
  const filas = [], acciones = [];
  const fila = (k, v) => { if (v !== undefined && v !== null && v !== "") filas.push(`<dt>${k}</dt><dd>${v}</dd>`); };
  let titulo = esc(n.etiqueta), texto = "";
  if (n.tipo === "control") {
    titulo = `<span class="ref">${esc(n.etiqueta)}</span> ${esc(n.titulo)}`;
    fila("Estado", chip(n.estado, "e"));
    if (n.nota && n.nota !== "Se espera: " + n.evidencia_esperada) fila("Observación", esc(n.nota));
    fila("Evidencia esperada", esc(n.evidencia_esperada));
    fila("En la norma", (n.norma || []).length ? n.norma.map(esc).join("<br>") : "");
  } else if (n.tipo === "evidencia") {
    titulo = `<span class="ref">${esc(n.etiqueta)}</span> ${esc(n.titulo)}`;
    fila("Integridad", n.integridad === "OK" ? '<span class="estado s-vigente">Íntegra</span>' : `<span class="estado c-no-conforme">${esc(n.integridad)}</span>`);
    fila("Tipo", esc(n.tipo_doc)); fila("Fecha", esc(n.fecha));
    fila("SHA-256", `<span class="huella" title="${esc(n.sha256)}">${esc((n.sha256 || "").slice(0, 16))}…</span>`);
  } else if (n.tipo === "documento") {
    titulo = `<span class="ref">${esc(n.etiqueta)}</span> ${esc(n.titulo)}`;
    fila("Situación", chip(n.situacion, "s"));
    fila("Versión", esc(n.version)); fila("Control PR-01", n.control ? chip(n.control, "c") : "");
    fila("Expediente de la guía", esc((n.expedientes || []).join(", ")));
    fila("Evidencia", n.evidencia ? `<span class="ref">${esc(n.evidencia)}</span>` : "");
    if (n.doc_id) acciones.push(`<button class="boton mini" data-ficha="${esc(n.doc_id)}" type="button">Abrir ficha</button>`);
    else texto = '<p class="nota">Aún no está registrado en la base de datos.</p>';
  } else if (n.tipo === "fuente") {
    texto = n.detalle ? `<p class="nota">${esc(n.detalle)}</p>` : "";
    fila("Fragmentos en FAISS", esc(n.fragmentos)); fila("Archivo", n.archivo ? `<span class="huella">${esc(n.archivo)}</span>` : "");
  } else if (n.tipo === "grupo") {
    const ctl = grafo.vecinos.get(n.id).filter((v) => v.otro.tipo === "control").map((v) => v.otro), cuenta = {};
    ctl.forEach((c) => { cuenta[c.estado] = (cuenta[c.estado] || 0) + 1; });
    fila("Controles", ctl.length);
    fila("Estados", Object.entries(cuenta).map(([e, k]) => `${chip(e, "e")} ${k}`).join("<br>"));
  } else if (n.tipo === "proyecto") {
    texto = n.detalle ? `<p class="nota">${esc(n.detalle)}</p>` : "";
    fila("Rol", esc(n.rol)); fila("Cobertura", `${esc(n.cobertura)} %`);
  } else texto = `<p class="nota">${esc(n.detalle || "")}</p>`;
  const rels = grafo.vecinos.get(n.id).filter((v) => visibleArista(v.a))
    .sort((x, y) => x.rel.localeCompare(y.rel) || x.otro.etiqueta.localeCompare(y.otro.etiqueta, "es", { numeric: true }));
  $("#grafo-detalle").innerHTML = `<small>${esc(TIPO_NODO[n.tipo] || n.tipo)}</small><h3>${titulo}</h3>${texto}
    ${filas.length ? `<dl>${filas.join("")}</dl>` : ""}${acciones.length ? `<div class="acciones">${acciones.join("")}</div>` : ""}
    ${rels.length ? `<h3>Relaciones (${rels.length})</h3><ul class="relaciones">${rels.map((v) => `<li><small>${esc(v.rel)}</small> <button type="button" data-nodo="${esc(v.otro.id)}">${esc(v.otro.etiqueta)}</button>${v.otro.titulo ? ` <small>${esc(v.otro.titulo)}</small>` : ""}${v.a.similitud ? ` <small>(coseno ${v.a.similitud})</small>` : ""}</li>`).join("")}</ul>` : ""}`;
}
function pintarResumenGrafo() {
  const r = grafo.datos.resumen, cifra = (v, t) => `<div><b>${esc(v ?? "–")}</b><small>${t}</small></div>`;
  $("#grafo-resumen").innerHTML = `<h3>Lo que sabe ahora</h3>
    <div class="grafo-cifras">${cifra(r.fragmentos_conocimiento, "fragmentos de conocimiento")}${cifra(r.fragmentos_norma, "de ISO/IEC 27701")}
      ${cifra(r.controles, "controles del catálogo")}${cifra(r.evidencias, "evidencias")}
      ${cifra(`${r.documentos_vigentes ?? 0} / ${r.documentos_pims ?? 0}`, "documentos PIMS vigentes")}${cifra(`${r.cobertura ?? 0} %`, "cobertura de controles")}
      ${cifra(r.semejanzas, "relaciones semánticas")}${cifra(r.remisiones, "remisiones de la norma")}</div>
    ${r.indexado ? "" : '<p class="alerta" style="margin-top:10px">El índice FAISS aún se está preparando (o Ollama está apagado): faltan las relaciones semánticas. Pulsa Actualizar en unos minutos.</p>'}`;
}
(function eventosGrafo() {
  const svg = $("#grafo-svg");
  const aGrafo = (e) => { const r = svg.getBoundingClientRect(), v = grafo.vista;
    return { x: (e.clientX - r.left - svg.clientWidth / 2 - v.x) / v.k, y: (e.clientY - r.top - svg.clientHeight / 2 - v.y) / v.k }; };
  let arrastre = null;
  svg.addEventListener("pointerdown", (e) => {
    const g = e.target.closest(".nodo"), n = g && grafo.porId.get(g.dataset.id);
    arrastre = { n, x0: e.clientX, y0: e.clientY, vx: grafo.vista.x, vy: grafo.vista.y, movido: false };
    if (n) n.fijo = true;
    svg.setPointerCapture(e.pointerId); svg.classList.add("moviendo");
  });
  svg.addEventListener("pointermove", (e) => {
    if (!arrastre) return;
    if (Math.abs(e.clientX - arrastre.x0) + Math.abs(e.clientY - arrastre.y0) > 4) arrastre.movido = true;
    if (!arrastre.movido) return;
    if (arrastre.n) { Object.assign(arrastre.n, aGrafo(e), { vx: 0, vy: 0 }); actualizarPosiciones(); calentar(0.25); }
    else { grafo.vista.x = arrastre.vx + e.clientX - arrastre.x0; grafo.vista.y = arrastre.vy + e.clientY - arrastre.y0; aplicarVista(); }
  });
  const soltar = () => {
    if (!arrastre) return;
    const { n, movido } = arrastre;
    if (n && n.tipo !== "agente") n.fijo = false;
    if (!movido) seleccionarNodo(n ? n.id : null, false);
    arrastre = null; svg.classList.remove("moviendo");
  };
  svg.addEventListener("pointerup", soltar); svg.addEventListener("pointercancel", soltar);
  svg.addEventListener("wheel", (e) => {
    e.preventDefault();
    const v = grafo.vista, p = aGrafo(e), k = Math.min(4, Math.max(0.2, v.k * Math.exp(-e.deltaY * 0.0015)));
    v.x += p.x * (v.k - k); v.y += p.y * (v.k - k); v.k = k; aplicarVista();
  }, { passive: false });
  svg.addEventListener("pointerover", (e) => { const g = e.target.closest(".nodo"); if (g && !arrastre) enfocar(g.dataset.id); });
  svg.addEventListener("pointerout", (e) => { const g = e.target.closest(".nodo"); if (g && !arrastre && !g.contains(e.relatedTarget)) enfocar(grafo.seleccion); });
  svg.addEventListener("keydown", (e) => { const g = e.target.closest(".nodo"); if (g && e.key === "Enter") seleccionarNodo(g.dataset.id); });
  $("#grafo-filtros").addEventListener("change", (e) => {
    const f = e.target.dataset.filtro; if (!f) return;
    grafo.filtros[f] = e.target.checked;
    if (!grafo.datos) return;
    aplicarFiltros(); enfocar(grafo.seleccion);
    if (grafo.seleccion) pintarDetalleNodo(grafo.porId.get(grafo.seleccion));
  });
  $("#grafo-buscar").addEventListener("input", (e) => {
    const q = e.target.value.trim().toLowerCase();
    grafo.nodos.forEach((n) => n.el.classList.toggle("coincide", !!q && `${n.etiqueta} ${n.titulo || ""}`.toLowerCase().includes(q)));
  });
  $("#grafo-buscar").addEventListener("keydown", (e) => {
    if (e.key !== "Enter") return;
    const n = grafo.nodos.find((x) => x.el.classList.contains("coincide")); if (n) seleccionarNodo(n.id);
  });
  $("#btn-grafo-encuadrar").addEventListener("click", encuadrar);
  $("#btn-grafo-recargar").addEventListener("click", () => cargarGrafo());
  $("#grafo-detalle").addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    if (b.dataset.nodo) seleccionarNodo(b.dataset.nodo);
    else if (b.dataset.ficha) abrirFicha(b.dataset.ficha);
  });
  window.addEventListener("resize", () => { if (estado.vista === "grafo") aplicarVista(); });
})();

/* ------------------------------------------------------------- CHAT CON LA IA LOCAL */
/* Panel lateral derecho. La respuesta llega en NDJSON a medida que Ollama la genera;
   la conversación se recuerda en este navegador (solo como comodidad). */
const chat = { historial: [], control: null, sesion: 0 };
const ICONO_ESCUDO = '<svg class="i" viewBox="0 0 24 24"><path d="M12 3l8 3v6c0 4.5-3.2 8-8 9-4.8-1-8-4.5-8-9V6l8-3z"/><path d="M8.5 12l2.5 2.5L15.5 10"/></svg>';
const ICONO_COPIAR = '<svg class="i" viewBox="0 0 24 24"><rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V6a2 2 0 00-2-2H6a2 2 0 00-2 2v8a2 2 0 002 2h2"/></svg>';
const SUGERENCIAS = [
  "¿Qué controles críticos siguen sin evidencia y qué debería registrar primero?",
  "Resume el resultado de la última auditoría interna y su plan de acción.",
  "¿Qué exige la cláusula 7.5 sobre la información documentada y cómo la cubre PIMS-PR-01?",
  "¿Para qué sirve el formulario PIMS-FO-01 y qué campos de la cláusula 10.2 recoge?",
];
function guardarChat() { try { localStorage.setItem("agente.chat", JSON.stringify(chat.historial.slice(-30))); } catch (_) { /* sin almacenamiento */ } }
function leerChat() { try { const h = JSON.parse(localStorage.getItem("agente.chat") || "[]"); return Array.isArray(h) ? h : []; } catch (_) { return []; } }
function cajaChat() { return $("#chat-mensajes"); }
function alFondo(forzar = false) {
  const c = cajaChat();
  if (forzar || c.scrollHeight - c.scrollTop - c.clientHeight < 120) c.scrollTop = c.scrollHeight;
}
function bienvenidaChat() {
  cajaChat().innerHTML = `<div class="chat-bienvenida"><h3>Pregunta sobre el proyecto</h3>
    <p>Conozco el expediente de evidencias, los documentos PIMS de Evidencia y Auditoría, la última auditoría y el texto de ISO/IEC 27701:2025. Todo corre en tu computadora.</p>
    <div class="sugerencias">${SUGERENCIAS.map((s, i) => `<button type="button" style="--i:${i}">${esc(s)}</button>`).join("")}</div></div>`;
}
function pieRespuesta(texto, fuentes) {
  const unicas = [...new Set((fuentes || []).map((f) => f.fuente || f.ref))].filter(Boolean);
  return `<div class="msj-pie">${unicas.length ? `<details class="chat-fuentes"><summary>${plural(unicas.length, "fuente")} consultadas</summary><ul>${unicas.map((u) => `<li>${esc(u)}</li>`).join("")}</ul></details>` : ""}
    ${texto ? `<button type="button" class="copiar">${ICONO_COPIAR}Copiar</button>` : ""}</div>`;
}
function mensajeChat(rol, texto = "", fuentes = null) {
  const m = document.createElement("div");
  if (rol === "user") { m.className = "msj usuario"; m.textContent = texto; }
  else {
    m.className = "msj ia";
    m.innerHTML = `<span class="mini-avatar" aria-hidden="true">${ICONO_ESCUDO}</span><div><div class="cuerpo">${texto ? md(texto) : ""}</div>${texto ? pieRespuesta(texto, fuentes) : ""}</div>`;
    m.dataset.texto = texto;
  }
  cajaChat().appendChild(m);
  return m;
}
function pintarChat() {
  if (!chat.historial.length) return bienvenidaChat();
  cajaChat().innerHTML = "";
  chat.historial.forEach((t) => mensajeChat(t.role, t.content, t.fuentes));
  alFondo(true);
}
function abrirChat(abrir = true) {
  const panel = $("#chat");
  panel.classList.toggle("abierto", abrir); panel.inert = !abrir;
  document.body.classList.toggle("chat-abierto", abrir);
  $("#chat-fab").setAttribute("aria-expanded", String(abrir));
  recordar("agente.chat.abierto", abrir ? "1" : "0");
  if (abrir) { setTimeout(() => $("#chat-texto").focus(), 60); estadoIA(); } else $("#chat-fab").focus({ preventScroll: true });
  setTimeout(() => window.dispatchEvent(new Event("resize")), 400);   // el grafo y el indicador se reubican
}
async function estadoIA() {
  try {
    const s = await api("/api/agente/sistema");
    const lista = s.ollama.ok && !(s.indices && s.indices.estado === "preparando");
    $("#chat").classList.toggle("ia-lista", !!s.ollama.ok);
    if (!chat.control) $("#chat-modelo").textContent = !s.ollama.ok ? "IA local apagada: inicia Ollama" : lista ? "IA local lista" : "IA local, preparando índices";
  } catch (_) { /* se verá al preguntar */ }
}
function ajustarEntrada() { const t = $("#chat-texto"); t.style.height = "auto"; t.style.height = Math.min(t.scrollHeight, 160) + "px"; t.style.overflowY = t.scrollHeight > 160 ? "auto" : "hidden"; }

async function enviarChat(texto) {
  texto = (texto || "").trim();
  if (!texto || chat.control) return;
  if (!chat.historial.length) cajaChat().innerHTML = "";
  mensajeChat("user", texto); alFondo(true);
  const previo = chat.historial.slice(-6).map(({ role, content }) => ({ role, content }));
  chat.historial.push({ role: "user", content: texto }); guardarChat();
  $("#chat-texto").value = ""; ajustarEntrada();

  const m = mensajeChat("assistant");
  const cuerpo = $(".cuerpo", m);
  cuerpo.innerHTML = '<div class="chat-estado"><span class="puntos"><i></i><i></i><i></i></span><span>Preparando</span></div>';
  m.classList.add("escribiendo");
  const panel = $("#chat"); panel.classList.add("ocupado");
  chat.control = new AbortController();
  const sesion = chat.sesion;
  let respuesta = "", fuentes = [], error = "", pendiente = false;
  const repintar = () => {
    if (pendiente) return; pendiente = true;
    requestAnimationFrame(() => { pendiente = false; cuerpo.innerHTML = md(respuesta); alFondo(); });
  };
  const procesar = (ev) => {
    if (ev.modelo) $("#chat-modelo").textContent = `IA local, ${ev.modelo}`;
    if (ev.tipo === "estado" && !respuesta) { const s = $(".chat-estado span:last-child", cuerpo); if (s) s.textContent = ev.texto; }
    else if (ev.tipo === "fuentes") fuentes = ev.fuentes || [];
    else if (ev.tipo === "texto") { respuesta += ev.texto; repintar(); }
    else if (ev.tipo === "error") error = ev.texto;
  };
  try {
    const r = await fetch("/api/agente/chat", { method: "POST", headers: { "Content-Type": "application/json" }, signal: chat.control.signal,
      body: JSON.stringify({ mensaje: texto, historial: previo, vista: $("#titulo-vista").textContent }) });
    if (r.status === 401) { location.href = "/login?siguiente=" + encodeURIComponent(location.pathname); return; }
    if (!r.ok || !r.body) { const d = await r.json().catch(() => ({})); throw new Error(d.error || `Error ${r.status}`); }
    const lector = r.body.getReader(), dec = new TextDecoder();
    let buf = "";
    for (;;) {
      const { value, done } = await lector.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let i;
      while ((i = buf.indexOf("\n")) >= 0) { const linea = buf.slice(0, i).trim(); buf = buf.slice(i + 1); if (linea) procesar(JSON.parse(linea)); }
    }
    if (buf.trim()) procesar(JSON.parse(buf));
  } catch (err) {
    if (err.name !== "AbortError") error = err.message;
  } finally {
    const detenido = chat.control?.signal.aborted;
    chat.control = null; panel.classList.remove("ocupado"); m.classList.remove("escribiendo");
    if (sesion !== chat.sesion) return;   // se empezó una conversación nueva mientras respondía
    cuerpo.innerHTML = (respuesta ? md(respuesta) : "") + (detenido ? '<p class="detenido">Respuesta detenida.</p>' : "")
      + (error ? `<p class="alerta mal">${esc(error)}</p>` : "") + (!respuesta && !error && !detenido ? '<p class="tenue">El modelo no devolvió texto. Vuelve a intentarlo.</p>' : "");
    if (respuesta) {
      m.dataset.texto = respuesta;
      cuerpo.insertAdjacentHTML("afterend", pieRespuesta(respuesta, fuentes));
      chat.historial.push({ role: "assistant", content: respuesta, fuentes: fuentes.map((f) => ({ ref: f.ref, fuente: f.fuente })) });
    } else chat.historial.pop();   // la pregunta sin respuesta no se manda como contexto la próxima vez
    guardarChat(); alFondo(); estadoIA();
    $("#chat-texto").focus();
  }
}

$("#chat-fab").addEventListener("click", () => abrirChat(true));
$("#chat-cerrar").addEventListener("click", () => abrirChat(false));
$("#chat-nuevo").addEventListener("click", () => { chat.sesion++; if (chat.control) chat.control.abort(); chat.historial = []; guardarChat(); bienvenidaChat(); $("#chat-texto").focus(); });
$("#chat-form").addEventListener("submit", (e) => { e.preventDefault(); if (chat.control) chat.control.abort(); else enviarChat($("#chat-texto").value); });
$("#chat-texto").addEventListener("input", ajustarEntrada);
$("#chat-texto").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); $("#chat-form").requestSubmit(); } });
$("#chat-mensajes").addEventListener("click", async (e) => {
  const s = e.target.closest(".sugerencias button");
  if (s) return enviarChat(s.textContent);
  const c = e.target.closest(".copiar");
  if (c) {
    try { await navigator.clipboard.writeText(c.closest(".msj").dataset.texto || ""); c.lastChild.textContent = "Copiado"; setTimeout(() => { c.lastChild.textContent = "Copiar"; }, 1500); }
    catch (_) { aviso("No se pudo copiar al portapapeles"); }
  }
});
document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "/") { e.preventDefault(); abrirChat(!$("#chat").classList.contains("abierto")); }
  else if (e.key === "Escape" && $("#chat").classList.contains("abierto") && !document.querySelector("dialog[open]")) abrirChat(false);
});
chat.historial = leerChat();
pintarChat();
if (recordar("agente.chat.abierto") === "1") abrirChat(true);

/* ------------------------------------------------------------------------ inicio */
const inicial = (location.hash || "").slice(1);
irA(VISTAS[inicial] ? inicial : "panel");
if (VISTAS[inicial] && inicial !== "panel") { cargarServicios().catch(() => {}); cargarIntegridad().catch(() => {}); }
cargarEjecuciones().then(() => {
  const abierta = estado.ejecuciones.find((e) => e.estado === "esperando_aprobacion");
  if (abierta && !VISTAS[inicial]) { irA("auditorias"); return seleccionar(abierta.id, true); }
}).catch(() => {});
setInterval(() => { if (!document.hidden) { cargarEjecuciones().catch(() => {}); cargarServicios().catch(() => {}); } }, 10000);
fetch("/api/sesion").then((r) => r.json()).then((d) => { const a = $("#salir"); if (a && d.login && d.usuario) { a.hidden = false; a.textContent = `Cerrar sesión (${d.usuario})`; } }).catch(() => {});
