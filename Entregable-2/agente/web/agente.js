/* Agente de Evidencia y Auditoría · panel (JavaScript puro, sin frameworks). */
"use strict";

const $ = (sel) => document.querySelector(sel);
const estado = { ejecuciones: [], seleccionada: null, firma: "", temporizador: null, bitacora: "decisiones", cobertura: null, vista: "panel" };
const ORDEN = ["Cubierto", "Parcial", "Desactualizada", "Comprometida", "Sin evidencia", "No aplica"];
const NOMBRES_ESTADO = { en_curso: "En curso", esperando_aprobacion: "Esperando aprobación", completada: "Completada", rechazada: "Rechazada",
  error: "Error", pendiente: "Pendiente", ok: "OK", omitido: "Omitido", interrumpida: "Interrumpida", interrumpido: "Interrumpido",
  cancelada: "Cancelada", cancelado: "Cancelado", pausada: "Pausada" };
const ABIERTAS = ["en_curso", "esperando_aprobacion", "pausada"];
const REANUDABLES = ["pausada", "interrumpida", "error"];
const TIPOS = { auditoria_interna: "Auditoría interna", incidente: "Incidente", bandeja: "Bandeja de entrada" };
const TITULOS = { panel: "Panel", auditorias: "Auditorías", expediente: "Expediente de evidencias", cobertura: "Cobertura de controles",
  bitacoras: "Bitácoras", herramientas: "Herramientas", sistema: "Datos y sistema" };
const PRELIMINAR = '<span class="preliminar">PRELIMINAR · requiere validación del auditor</span>';

function clase(t) { return String(t ?? "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9_]+/g, "-").replace(/_/g, "-"); }
function esc(t) { return String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
async function api(ruta, op = {}) {
  const r = await fetch(ruta, op);
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(d.error || `Error ${r.status}`);
  return d;
}
const json = (cuerpo) => ({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo) });
function fecha(iso) { if (!iso) return ""; const d = new Date(iso); return isNaN(d) ? String(iso) : d.toLocaleString("es-PE", { dateStyle: "short", timeStyle: "medium" }); }
function insignia(est) { return `<span class="insignia x-${clase(est)}">${esc(NOMBRES_ESTADO[est] || est)}</span>`; }
function aviso(msg, tipo = "mal") {
  const t = document.createElement("div");
  t.className = "aviso-toast " + tipo; t.textContent = msg.message || msg;
  $("#avisos").appendChild(t); setTimeout(() => t.remove(), tipo === "mal" ? 7000 : 4000);
}
const error = (e) => aviso(e);
const recordar = (k, v) => { try { if (v !== undefined) localStorage.setItem(k, v); return localStorage.getItem(k) || ""; } catch (_) { return v || ""; } };

/* Markdown mínimo (se escapa primero todo el HTML). */
function md(texto) {
  const lineas = esc(texto).split("\n");
  let html = "", tabla = [], lista = null;
  const li = (s) => s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>").replace(/`(.+?)`/g, "<code>$1</code>");
  const cerrarTabla = () => {
    if (!tabla.length) return;
    const filas = tabla.filter((f) => !/^\s*\|?\s*:?-{2,}/.test(f));
    html += '<div class="tabla-envoltura"><table>' + filas.map((f, i) => {
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

/* ------------------------------------------------------------- navegación */
function irA(vista) {
  estado.vista = vista;
  document.querySelectorAll(".item").forEach((x) => x.classList.toggle("activa", x.dataset.vista === vista));
  document.querySelectorAll(".vista").forEach((v) => v.classList.toggle("activa", v.id === "vista-" + vista));
  $("#titulo-vista").textContent = TITULOS[vista] || vista;
  $("#lateral").classList.remove("abierto");
  const cargas = { panel: cargarPanel, auditorias: cargarEjecuciones, expediente: cargarExpediente, cobertura: cargarCobertura,
    bitacoras: cargarBitacora, herramientas: cargarHerramientas, sistema: cargarSistema };
  (cargas[vista] || (() => {}))().catch(error);
}
document.querySelectorAll(".item").forEach((b) => b.addEventListener("click", () => irA(b.dataset.vista)));
document.querySelectorAll("[data-ir]").forEach((b) => b.addEventListener("click", () => irA(b.dataset.ir)));
$("#btn-menu").addEventListener("click", () => $("#lateral").classList.toggle("abierto"));

/* Cuadro de diálogo que pide quién actúa (y, a veces, un motivo). Devuelve {actor, motivo} o null. */
function pedirMotivo({ titulo, texto, boton = "Confirmar", peligro = false, conMotivo = true }) {
  return new Promise((resolver) => {
    const dlg = $("#dlg-motivo");
    $("#motivo-titulo").textContent = titulo; $("#motivo-texto").textContent = texto;
    $("#motivo-actor").value = recordar("agente.auditor"); $("#motivo-motivo").value = "";
    $("#motivo-fila").hidden = !conMotivo;
    const b = $("#motivo-enviar"); b.textContent = boton; b.className = "boton " + (peligro ? "peligro" : "primario");
    dlg.onclose = () => {
      if (dlg.returnValue !== "ok") return resolver(null);
      const actor = $("#motivo-actor").value.trim(); recordar("agente.auditor", actor);
      resolver({ actor, motivo: $("#motivo-motivo").value.trim() });
    };
    dlg.returnValue = ""; dlg.showModal(); $("#motivo-actor").focus();
  });
}

/* ---------------------------------------------------------------- estado */
async function cargarServicios() {
  const s = await api("/api/agente/sistema");
  const bd = $("#p-bd"), ia = $("#p-ia");
  bd.textContent = s.base_datos.ok ? "BD conectada" : "BD sin conexión"; bd.className = "pastilla " + (s.base_datos.ok ? "bien" : "mal");
  const modelos = s.ollama.modelos.length;
  ia.textContent = s.ollama.ok ? `IA local · ${modelos} modelo${modelos === 1 ? "" : "s"}` : "IA local apagada";
  ia.className = "pastilla " + (s.ollama.ok ? "bien" : "aviso");
  return s;
}

async function cargarResumen() {
  const r = await api("/api/agente/resumen");
  $("#k-cobertura").textContent = `${r.porcentaje_cobertura}%`;
  $("#k-barra").style.width = `${Math.max(0, Math.min(100, Number(r.porcentaje_cobertura) || 0))}%`;
  $("#k-cobertura-nota").textContent = `${r.controles_aplicables} controles aplicables · rol ${r.rol}`;
  $("#k-evidencias").textContent = r.evidencias;
  const i = r.integridad, malas = i.resultados.ALTERADA.length + i.resultados.FALTANTE.length;
  const ki = $("#k-integridad");
  ki.textContent = r.evidencias === 0 ? "—" : i.integro ? "Íntegro" : "Alerta";
  ki.className = "cifra " + (r.evidencias === 0 ? "" : i.integro ? "bien" : "mal");
  $("#k-integridad-nota").textContent = r.evidencias === 0 ? "sin evidencias" : i.integro ? `${i.total} evidencias verificadas` : `${malas || "Cadena"} con fallo`;
  const pi = $("#p-integridad");
  pi.textContent = r.evidencias === 0 ? "Expediente vacío" : i.integro ? "Expediente íntegro" : "Alerta de integridad";
  pi.className = "pastilla " + (r.evidencias === 0 ? "" : i.integro ? "bien" : "mal");
  const claves = Object.keys(r.conteo_estados).sort((a, b) => ORDEN.indexOf(a) - ORDEN.indexOf(b));
  $("#k-estados").innerHTML = claves.map((k) => `<span class="insignia e-${clase(k)}">${esc(k)}: ${esc(r.conteo_estados[k])}</span>`).join("");
  $("#k-estados-nota").textContent = `corte ${r.fecha_corte}`;
}

async function cargarPanel() {
  await Promise.all([cargarResumen(), cargarEjecuciones(), cargarBandeja(), cargarServicios()]);
  const n = estado.ejecuciones.length;
  $("#k-auditorias").textContent = n;
  const ab = estado.ejecuciones.filter((e) => ABIERTAS.includes(e.estado)).length;
  $("#k-auditorias-nota").textContent = ab ? `${ab} abierta${ab === 1 ? "" : "s"}` : "ninguna abierta";
}

/* ------------------------------------------------------------ ejecuciones */
function itemEjecucion(e) {
  return `<li><button type="button" data-id="${esc(e.id)}" class="${e.id === estado.seleccionada ? "activa" : ""}">
    <span class="cab"><strong>${esc(TIPOS[e.tipo] || e.tipo)}</strong>${insignia(e.pausa_solicitada && e.estado === "en_curso" ? "pausada" : e.estado)}</span>
    <small class="mono">${esc(e.id)} · ${esc(fecha(e.creado))}</small></button></li>`;
}
async function cargarEjecuciones() {
  estado.ejecuciones = await api("/api/agente/ejecuciones?proyecto=unsa");
  pintarListas();
}
function pintarListas() {
  const vacio = '<li class="nota">Aún no hay ejecuciones. Inicia una auditoría desde el Panel.</li>';
  $("#lista-ejecuciones").innerHTML = estado.ejecuciones.length ? estado.ejecuciones.map(itemEjecucion).join("") : vacio;
  $("#lista-reciente").innerHTML = estado.ejecuciones.length ? estado.ejecuciones.slice(0, 5).map(itemEjecucion).join("") : vacio;
  const ab = estado.ejecuciones.filter((e) => ABIERTAS.includes(e.estado) || e.estado === "interrumpida").length;
  const c = $("#c-abiertas"); c.hidden = !ab; c.textContent = ab;
}
["#lista-ejecuciones", "#lista-reciente"].forEach((s) => $(s).addEventListener("click", (ev) => {
  const b = ev.target.closest("button[data-id]");
  if (!b) return;
  irA("auditorias"); seleccionar(b.dataset.id, true).catch(error);
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
  if (forzar || firma !== estado.firma) {
    const antes = estado.firma.split("|")[0];
    estado.firma = firma; pintarDetalle(e);
    if (antes && antes !== e.estado) { cargarResumen().catch(() => {}); cargarServicios().catch(() => {}); }
  }
  if (e.estado === "en_curso") estado.temporizador = setTimeout(() => seleccionar(id).catch(() => {}), 2000);
}

function barraAcciones(e) {
  const b = [];
  if (e.estado === "en_curso") {
    b.push(e.pausa_solicitada ? '<button class="boton" disabled>Pausando al terminar el paso…</button>'
      : '<button class="boton aviso" data-accion="pausar">⏸ Pausar</button>');
  }
  if (REANUDABLES.includes(e.estado)) b.push(`<button class="boton exito" data-accion="reanudar">▶ ${e.estado === "error" ? "Reintentar" : "Reanudar"}</button>`);
  if (ABIERTAS.includes(e.estado) || ["interrumpida", "error"].includes(e.estado)) b.push('<button class="boton peligro" data-accion="cancelar">Cancelar auditoría</button>');
  b.push('<span class="espacio"></span>');
  if (e.tipo === "auditoria_interna" && e.estado === "completada") b.push('<a class="boton" href="/api/agente/gestitel/exportar" download>Exportar Excel GESTITEL</a>');
  return `<div class="barra-acciones">${b.join("")}</div>`;
}

function pintarDetalle(e) {
  const par = Object.entries(e.parametros || {}).map(([k, v]) => `${esc(k)}=${esc(JSON.stringify(v))}`).join(" · ");
  let html = `<div class="cab-ejecucion"><h2>${esc(TIPOS[e.tipo] || e.tipo)}</h2>${insignia(e.estado)}<small class="mono">${esc(e.id)}</small></div>
    <div class="parametros">Creada ${esc(fecha(e.creado))} · actualizada ${esc(fecha(e.actualizado))}${par ? " · " + par : ""}</div>
    ${barraAcciones(e)}`;
  if (e.estado === "pausada" && e.pausa) html += `<div class="alerta info">Pausada por <b>${esc(e.pausa.actor || "")}</b> el ${esc(fecha(e.pausa.fecha))}${e.pausa.motivo ? ": " + esc(e.pausa.motivo) : ""}.
    ${e.pausa.siguiente_paso ? `Al reanudar continúa en <span class="mono">${esc(e.pausa.siguiente_paso)}</span>, sin repetir lo ya hecho.` : ""}</div>`;
  if (e.estado === "interrumpida") html += `<div class="alerta">Se interrumpió${e.interrupcion ? ` (${esc(e.interrupcion.motivo)})` : ""}. Puedes reanudarla desde el último paso guardado.</div>`;
  if (e.error) html += `<div class="alerta mal">Error: ${esc(e.error)}</div>`;
  if (e.cancelacion) html += `<div class="alerta mal">Cancelada el ${esc(fecha(e.cancelacion.fecha))} por ${esc(e.cancelacion.actor)}: ${esc(e.cancelacion.motivo)}. No genera informe ni plan de acción.</div>`;
  html += `<ol class="linea-tiempo">${(e.pasos || []).map((p) => `<li class="p-${clase(p.estado)}">
      <div class="titulo-paso">${esc(p.titulo || p.nodo)} ${insignia(p.estado)}</div>
      ${p.resumen ? `<div class="resumen">${esc(p.resumen)}</div>` : ""}
      ${p.inicio ? `<small>${esc(fecha(p.inicio))}${p.fin ? " → " + esc(fecha(p.fin)) : ""}</small>` : ""}</li>`).join("")}</ol>`;
  if (e.estado === "esperando_aprobacion" && e.aprobacion) html += panelHitl(e);
  else if (e.aprobacion && (e.aprobacion.hallazgos || []).length && e.estado !== "completada") html += listaHallazgos(e.aprobacion.hallazgos);
  html += resultado(e);
  $("#detalle").innerHTML = html;
  $("#detalle").querySelectorAll("[data-accion]").forEach((b) => b.addEventListener("click", () => accion(e, b.dataset.accion, b)));
  if (e.estado === "esperando_aprobacion") conectarHitl(e);
  if (e.informe_nombre) cargarInforme(e.informe_nombre);
}

async function accion(e, nombre, boton) {
  const cfg = {
    pausar: { titulo: "Pausar auditoría", texto: "Se detendrá al terminar el paso actual. El avance queda guardado y podrás reanudarla.", boton: "Pausar" },
    reanudar: { titulo: e.estado === "error" ? "Reintentar" : "Reanudar auditoría", texto: "Continúa desde el último paso guardado, sin repetir lo ya hecho.", boton: "Reanudar", conMotivo: false },
    cancelar: { titulo: "Cancelar auditoría", texto: "Se descarta: no genera informe ni plan de acción y no se podrá reanudar.", boton: "Cancelar auditoría", peligro: true },
  }[nombre];
  const r = await pedirMotivo(cfg);
  if (!r) return;
  if (!r.actor) return aviso("Indica quién realiza la acción");
  boton.disabled = true;
  try {
    await api(`/api/agente/ejecuciones/${encodeURIComponent(e.id)}/${nombre}`, json({ actor: r.actor, motivo: r.motivo }));
    aviso({ pausar: "Pausa solicitada", reanudar: "Auditoría reanudada", cancelar: "Auditoría cancelada" }[nombre], "ok");
    await seleccionar(e.id, true); cargarResumen().catch(() => {});
  } catch (err) { boton.disabled = false; error(err); }
}

function listaHallazgos(h) {
  return `<h3>Hallazgos (${h.length}) ${PRELIMINAR}</h3><ul class="hallazgos">${h.map((x) => `<li><span class="ref">${esc(x.ref)}</span>
    <span class="insignia e-${clase(x.estado)}">${esc(x.estado)}</span><div class="md">${md(x.texto || "")}</div></li>`).join("")}</ul>`;
}

function panelHitl(e) {
  const a = e.aprobacion, props = a.propuestas || [];
  return `<div class="hitl" id="hitl"><h3 style="margin-top:0">Aprobación del auditor ${PRELIMINAR}</h3>
    <p class="pregunta">${esc(a.pregunta || "¿Apruebas los resultados preliminares del agente?")}</p>
    ${listaHallazgos(a.hallazgos || [])}
    <h3>Propuestas de pertinencia (${props.length})</h3>
    ${props.length ? `<ul class="hallazgos">${props.map((p, i) => `<li class="propuesta">
      <span><span class="ref">${esc(p.ref)}</span><br><span class="insignia v-${clase(p.veredicto)}">${esc(p.veredicto)}</span></span><span>${esc(p.justificacion)}</span>
      <span class="decision-control"><label><input type="radio" name="dc-${i}" value="aceptada" data-ref="${esc(p.ref)}"> Aceptar</label>
      <label><input type="radio" name="dc-${i}" value="rechazada" data-ref="${esc(p.ref)}"> Rechazar</label></span></li>`).join("")}</ul>`
      : '<p class="nota">Sin propuestas (modo rápido o ningún control evaluable).</p>'}
    <div class="fila-campos"><label>Auditor que valida<input type="text" id="hitl-auditor" placeholder="Nombre del auditor" autocomplete="name"></label>
      <label>Comentario<input type="text" id="hitl-comentario" placeholder="Observaciones (opcional)"></label></div>
    <div class="acciones-cab"><button class="boton exito" data-decision="aprobada" type="button">Aprobar y generar informe</button>
      <button class="boton peligro" data-decision="rechazada" type="button">Rechazar</button></div></div>`;
}

function conectarHitl(e) {
  const hitl = $("#hitl");
  $("#hitl-auditor").value = recordar("agente.auditor");
  hitl.querySelectorAll("button[data-decision]").forEach((b) => b.addEventListener("click", async () => {
    const auditor = $("#hitl-auditor").value.trim();
    if (!auditor) { $("#hitl-auditor").focus(); return aviso("Indica el nombre del auditor que valida"); }
    const dec = {};
    hitl.querySelectorAll("input[type=radio][data-ref]:checked").forEach((r) => { dec[r.dataset.ref] = r.value; });
    const faltan = (e.aprobacion.propuestas || []).length - Object.keys(dec).length;
    if (b.dataset.decision === "aprobada" && faltan > 0 && !confirm(`Quedan ${faltan} propuesta(s) sin decidir; no se registrará decisión sobre ellas. ¿Continuar?`)) return;
    recordar("agente.auditor", auditor);
    hitl.querySelectorAll("button").forEach((x) => { x.disabled = true; });
    try {
      await api(`/api/agente/ejecuciones/${encodeURIComponent(e.id)}/aprobar`, json({ decision: b.dataset.decision, auditor,
        comentario: $("#hitl-comentario").value.trim(), decisiones_controles: dec }));
      aviso(b.dataset.decision === "aprobada" ? "Aprobada: generando informe" : "Rechazada", "ok");
      await seleccionar(e.id, true); cargarResumen().catch(() => {});
    } catch (err) { hitl.querySelectorAll("button").forEach((x) => { x.disabled = false; }); error(err); }
  }));
}

function resultado(e) {
  const r = e.resultado || {}, plan = r.plan_accion || [];
  let html = "";
  if (plan.length) {
    const cols = [...new Set(plan.flatMap((p) => (p && typeof p === "object" ? Object.keys(p) : ["acción"])))];
    html += `<h3>Plan de acción (${plan.length})</h3><div class="tabla-envoltura"><table class="tabla"><thead><tr>${cols.map((c) => `<th>${esc(c.replace(/_/g, " "))}</th>`).join("")}</tr></thead><tbody>
      ${plan.map((p) => `<tr>${cols.map((c) => { const v = p && typeof p === "object" ? p[c] : p;
        return `<td${c === "ref" ? ' class="ref"' : ""}>${esc(v && typeof v === "object" ? JSON.stringify(v) : v)}</td>`; }).join("")}</tr>`).join("")}</tbody></table></div>`;
  }
  if (e.informe_nombre) html += `<div class="informe"><div class="tarjeta-cab"><h3 style="margin:0">Informe <span class="mono">${esc(e.informe_nombre)}</span></h3></div>
    <div id="informe-aviso"></div><div class="md" id="informe-md"><p class="nota">Cargando informe…</p></div></div>`;
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

/* --------------------------------------------------------------- lanzadores */
document.querySelectorAll("input[name=modo]").forEach((r) => r.addEventListener("change", () => {
  const ia = document.querySelector("input[name=modo]:checked").value === "ia";
  $("#max-hallazgos").disabled = !ia; $("#max-pertinencia").disabled = !ia;
}));
$("#btn-auditoria").addEventListener("click", async (ev) => {
  const b = ev.currentTarget, rapido = document.querySelector("input[name=modo]:checked").value === "rapido";
  const parametros = { modo_rapido: rapido };
  if (!rapido) { parametros.max_hallazgos = Math.max(0, parseInt($("#max-hallazgos").value, 10) || 0); parametros.max_pertinencia = Math.max(0, parseInt($("#max-pertinencia").value, 10) || 0); }
  b.disabled = true;
  try {
    const e = await api("/api/agente/ejecuciones", json({ tipo: "auditoria_interna", proyecto: "unsa", parametros }));
    irA("auditorias"); await cargarEjecuciones(); await seleccionar(e.id, true);
  } catch (err) { error(err); } finally { b.disabled = false; }
});
$("#btn-incidente").addEventListener("click", async (ev) => {
  const b = ev.currentTarget, descripcion = $("#incidente").value.trim();
  if (!descripcion) { $("#incidente").focus(); return; }
  b.disabled = true;
  try {
    const r = await api("/api/agente/incidente", json({ descripcion }));
    $("#incidente").value = ""; const id = r && (r.id || (r.ejecucion && r.ejecucion.id));
    irA("auditorias"); await cargarEjecuciones();
    if (id) await seleccionar(id, true); else aviso("Incidente notificado al agente", "ok");
  } catch (err) { error(err); } finally { b.disabled = false; }
});

/* ----------------------------------------------------------------- bandeja */
const zona = $("#zona-bandeja");
["dragenter", "dragover"].forEach((t) => zona.addEventListener(t, (e) => { e.preventDefault(); zona.classList.add("encima"); }));
["dragleave", "drop"].forEach((t) => zona.addEventListener(t, (e) => { e.preventDefault(); zona.classList.remove("encima"); }));
zona.addEventListener("drop", (e) => subirBandeja(e.dataTransfer.files));
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
  $("#lista-bandeja").innerHTML = d.archivos.length ? d.archivos.slice(0, 8).map((a) => `<li>${esc(a.nombre)} <small>· ${esc((a.bytes / 1024).toFixed(1))} KB</small></li>`).join("") : '<li class="nota">La bandeja está vacía.</li>';
}

/* -------------------------------------------------------------- expediente */
async function cargarExpediente() {
  const d = await api("/api/agente/expediente");
  const ev = d.evidencias;
  $("#exp-nota").textContent = `${ev.length} evidencia${ev.length === 1 ? "" : "s"}`;
  $("#tabla-expediente tbody").innerHTML = ev.length ? ev.map((x) => `<tr><td class="ref">${esc(x.id)}</td><td><strong>${esc(x.titulo)}</strong><br><small>${esc(x.archivo)}</small></td>
    <td><span class="insignia">${esc(x.tipo)}</span></td><td>${(x.controles || []).map((c) => `<span class="ref">${esc(c)}</span>`).join(", ") || "—"}</td>
    <td class="sin-corte">${esc(x.fecha_documento || "—")}</td><td class="mono" title="${esc(x.sha256)}">${esc((x.sha256 || "").slice(0, 12))}…</td></tr>`).join("")
    : '<tr><td colspan="6" class="vacio">El expediente está vacío. Registra la primera evidencia.</td></tr>';
}
$("#btn-verificar").addEventListener("click", async (ev) => {
  const b = ev.currentTarget; b.disabled = true;
  try {
    const r = await api("/api/agente/expediente/verificar", { method: "POST" });
    const malas = ["ALTERADA", "FALTANTE"].reduce((n, k) => n + ((r.resultados || {})[k] || []).length, 0);
    aviso(r.integro ? `Integridad verificada: ${r.total} evidencias íntegras` : `Atención: ${malas || "cadena de custodia"} con fallo`, r.integro ? "ok" : "mal");
    cargarResumen().catch(() => {});
  } catch (err) { error(err); } finally { b.disabled = false; }
});
$("#btn-nueva-evidencia").addEventListener("click", async () => {
  if (!$("#ev-tipo").options.length) {
    const c = await api("/api/agente/catalogo");
    $("#ev-tipo").innerHTML = c.tipos.map((t) => `<option>${esc(t)}</option>`).join("");
    $("#lista-controles").innerHTML = c.controles.map((x) => `<option value="${esc(x.ref)}">${esc(x.titulo)}</option>`).join("");
  }
  $("#form-evidencia").elements.responsable.value = recordar("agente.auditor");
  $("#dlg-evidencia").showModal();
});
$("#dlg-evidencia").addEventListener("close", async (ev) => {
  const dlg = ev.currentTarget; if (dlg.returnValue !== "ok") return;
  const form = $("#form-evidencia"), fd = new FormData(form);
  recordar("agente.auditor", fd.get("responsable"));
  try {
    const r = await api("/api/agente/expediente", { method: "POST", body: fd });
    aviso(`Evidencia ${r.id} registrada`, "ok"); form.reset();
    cargarExpediente().catch(() => {}); cargarResumen().catch(() => {});
  } catch (err) { error(err); }
});

/* ---------------------------------------------------------------- cobertura */
async function cargarCobertura() {
  const c = estado.cobertura = await api("/api/agente/cobertura");
  $("#cob-nota").textContent = `${c.porcentaje_cobertura}% · ${c.controles_aplicables} controles aplicables`;
  const sel = $("#filtro-cobertura");
  if (sel.options.length < 2) Object.keys(c.conteo_estados).sort((a, b) => ORDEN.indexOf(a) - ORDEN.indexOf(b))
    .forEach((k) => sel.insertAdjacentHTML("beforeend", `<option>${esc(k)}</option>`));
  pintarCobertura();
}
function pintarCobertura() {
  const filtro = $("#filtro-cobertura").value, filas = (estado.cobertura?.controles || []).filter((f) => !filtro || f.estado === filtro);
  $("#tabla-cobertura tbody").innerHTML = filas.length ? filas.map((f) => `<tr><td class="ref">${esc(f.ref)}</td><td>${esc(f.titulo || "")}</td>
    <td><span class="insignia e-${clase(f.estado)}">${esc(f.estado)}</span></td><td>${esc((f.evidencias || []).length ?? f.n_evidencias ?? "")}</td>
    <td class="nota">${esc(f.nota || "")}</td></tr>`).join("") : '<tr><td colspan="5" class="vacio">Sin controles en este estado.</td></tr>';
}
$("#filtro-cobertura").addEventListener("change", pintarCobertura);

/* --------------------------------------------------------------- bitácoras */
const CAMPOS_FECHA = ["fecha", "momento", "ts", "timestamp", "hora", "creado"], CAMPOS_TIPO = ["decision", "tipo", "evento", "herramienta", "accion", "nodo"];
$("#subpestanas").addEventListener("click", (e) => {
  const b = e.target.closest("[data-bitacora]"); if (!b) return;
  estado.bitacora = b.dataset.bitacora;
  document.querySelectorAll("#subpestanas button").forEach((x) => x.classList.toggle("activa", x === b));
  cargarBitacora().catch(error);
});
async function cargarBitacora() {
  const d = await api(`/api/agente/bitacora?tipo=${encodeURIComponent(estado.bitacora)}`);
  $("#tabla-bitacora thead").innerHTML = "<tr><th>Fecha</th><th>Tipo</th><th>Detalle</th></tr>";
  $("#tabla-bitacora tbody").innerHTML = d.registros.length ? d.registros.map((r) => {
    const resto = { ...r }, kf = CAMPOS_FECHA.find((k) => k in r), kt = CAMPOS_TIPO.find((k) => k in r);
    if (kf) delete resto[kf]; if (kt) delete resto[kt];
    return `<tr><td class="mono sin-corte">${esc(kf ? fecha(r[kf]) : "")}</td><td><strong>${esc(kt ? r[kt] : "")}</strong></td><td><pre>${esc(JSON.stringify(resto, null, 1))}</pre></td></tr>`;
  }).join("") : '<tr><td colspan="3" class="vacio">Sin registros todavía.</td></tr>';
}

async function cargarHerramientas() {
  const lista = await api("/api/agente/herramientas");
  $("#tabla-herramientas tbody").innerHTML = lista.map((h) => `<tr><td><span class="ref">${esc(h.nombre)}</span><br><small class="mono">${esc(h.firma)}</small></td>
    <td><span class="insignia ${h.ia ? "ia" : ""}">${h.ia ? "Con IA local" : "Determinista"}</span></td><td><pre>${esc(h.doc)}</pre></td></tr>`).join("");
}

/* ------------------------------------------------------------ datos y sistema */
async function cargarSistema() {
  const s = await cargarServicios();
  $("#lista-servicios").innerHTML = [
    ["PostgreSQL", s.base_datos.ok, s.base_datos.detalle], ["Ollama (IA local)", s.ollama.ok, s.ollama.ok ? s.ollama.modelos.join(", ") || "sin modelos" : "no responde en el puerto 11434"],
    ["Orquestador LangGraph", s.orquestador_real, s.orquestador_real ? "activo" : "sustituto provisional"]]
    .map(([n, ok, d]) => `<li><span class="punto ${ok ? "ok" : ""}"></span><div><b>${esc(n)}</b><small>${esc(d)}</small></div></li>`).join("");
  const filas = s.base_datos.filas || {}, claves = Object.keys(filas);
  $("#tabla-filas tbody").innerHTML = claves.length ? claves.map((k) => `<tr><td class="mono">${esc(k)}</td><td>${esc(filas[k])}</td></tr>`).join("") : '<tr><td class="vacio">Sin datos</td></tr>';
  return s;
}
$("#btn-refrescar-sistema").addEventListener("click", () => cargarSistema().catch(error));

$("#btn-vaciar").addEventListener("click", async () => {
  const s = await api("/api/agente/sistema");
  const filas = Object.entries(s.base_datos.filas || {}).filter(([, n]) => n > 0);
  $("#vaciar-resumen").innerHTML = (filas.length ? filas.map(([k, n]) => `<li>${esc(n)} fila(s) de <span class="mono">${esc(k)}</span></li>`).join("") : "<li>La base ya está vacía</li>") +
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
    aviso(`Base vaciada: ${n} filas y ${r.carpetas.length} carpetas/archivos borrados`, "ok");
    estado.seleccionada = null; $("#detalle").innerHTML = '<p class="nota">Selecciona una ejecución para ver su avance y las acciones disponibles.</p>';
    await Promise.all([cargarSistema(), cargarResumen(), cargarEjecuciones(), cargarBandeja()]);
  } catch (err) { error(err); }
});

/* -------------------------------------------------------------------- inicio */
cargarPanel().then(() => {
  const abierta = estado.ejecuciones.find((e) => ["en_curso", "esperando_aprobacion"].includes(e.estado));
  if (abierta) { irA("auditorias"); return seleccionar(abierta.id, true); }
}).catch(error);
setInterval(() => { if (!document.hidden) { cargarEjecuciones().catch(() => {}); cargarServicios().catch(() => {}); } }, 10000);
