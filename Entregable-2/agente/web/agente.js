/* AUDITA-PIMS · panel del agente autónomo (JavaScript puro, sin frameworks). */
"use strict";

const $ = (sel) => document.querySelector(sel);
const estado = { ejecuciones: [], seleccionada: null, firma: "", temporizador: null, bitacora: "decisiones" };
const ORDEN = ["Cubierto", "Parcial", "Desactualizada", "Comprometida", "Sin evidencia", "No aplica"];
const NOMBRES_ESTADO = { en_curso: "En curso", esperando_aprobacion: "Esperando aprobación", completada: "Completada",
  rechazada: "Rechazada", error: "Error", pendiente: "Pendiente", ok: "OK", omitido: "Omitido" };
const TIPOS = { auditoria_interna: "Auditoría interna", incidente: "Incidente", bandeja: "Bandeja de entrada" };
/* Flujo de referencia si aún no hay ninguna ejecución de auditoría interna. */
const FLUJO_POR_DEFECTO = [
  ["integridad", "Verificar integridad"], ["cobertura", "Matriz de cobertura"], ["hallazgos", "Redactar hallazgos"],
  ["pertinencia", "Evaluar pertinencia"], ["aprobacion", "Aprobación del auditor (HITL)"],
  ["informe", "Generar informe"], ["plan_accion", "Plan de acción"]];
const PRELIMINAR = '<span class="preliminar">PRELIMINAR — requiere validación del auditor</span>';

function clase(texto) {
  return String(texto ?? "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9_]+/g, "-");
}
function esc(t) {
  return String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
async function api(ruta, opciones = {}) {
  const r = await fetch(ruta, opciones);
  const datos = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(datos.error || `Error ${r.status}`);
  return datos;
}
function json(cuerpo) {
  return { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo) };
}
function fecha(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return isNaN(d) ? String(iso) : d.toLocaleString("es-PE", { dateStyle: "short", timeStyle: "medium" });
}
function insignia(est) {
  return `<span class="insignia x-${clase(est)}">${esc(NOMBRES_ESTADO[est] || est)}</span>`;
}
function aviso(err) { alert(err.message || err); }

/* Markdown mínimo (se escapa primero todo el HTML): encabezados, negrita, código, listas y tablas. */
function md(texto) {
  const lineas = esc(texto).split("\n");
  let html = "", tabla = [], lista = null;
  const enLinea = (s) => s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>")
    .replace(/(^|\W)_(.+?)_(?=\W|$)/g, "$1<em>$2</em>").replace(/`(.+?)`/g, "<code>$1</code>");
  const cerrarTabla = () => {
    if (!tabla.length) return;
    const filas = tabla.filter((f) => !/^\s*\|?\s*:?-{2,}/.test(f));
    html += '<div class="tabla-envoltura"><table>' + filas.map((f, i) => {
      const celdas = f.trim().replace(/^\||\|$/g, "").split("|");
      const t = i === 0 ? "th" : "td";
      return "<tr>" + celdas.map((c) => `<${t}>${enLinea(c.trim())}</${t}>`).join("") + "</tr>";
    }).join("") + "</table></div>";
    tabla = [];
  };
  const cerrarLista = () => { if (lista) { html += `</${lista}>`; lista = null; } };
  for (const l of lineas) {
    if (/^\s*\|/.test(l)) { cerrarLista(); tabla.push(l); continue; }
    cerrarTabla();
    let m;
    if ((m = l.match(/^(#{1,4})\s+(.*)/))) { cerrarLista(); const n = Math.min(m[1].length + 1, 4); html += `<h${n}>${enLinea(m[2])}</h${n}>`; }
    else if ((m = l.match(/^\s*[-*]\s+(.*)/))) { if (lista !== "ul") { cerrarLista(); html += "<ul>"; lista = "ul"; } html += `<li>${enLinea(m[1])}</li>`; }
    else if ((m = l.match(/^\s*\d+[.)]\s+(.*)/))) { if (lista !== "ol") { cerrarLista(); html += "<ol>"; lista = "ol"; } html += `<li>${enLinea(m[1])}</li>`; }
    else if (l.trim()) { cerrarLista(); html += `<p>${enLinea(l)}</p>`; }
    else cerrarLista();
  }
  cerrarTabla(); cerrarLista();
  return html;
}

/* ---------------------------------------------------------------- pestañas */
document.querySelectorAll(".pestana").forEach((b) => b.addEventListener("click", () => {
  document.querySelectorAll(".pestana").forEach((x) => x.classList.toggle("activa", x === b));
  document.querySelectorAll(".vista").forEach((v) => v.classList.toggle("activa", v.id === "vista-" + b.dataset.vista));
  if (b.dataset.vista === "bitacoras") cargarBitacora().catch(aviso);
  if (b.dataset.vista === "herramientas") cargarHerramientas().catch(aviso);
}));

/* ------------------------------------------------------------------ resumen */
async function cargarResumen() {
  const r = await api("/api/agente/resumen");
  $("#k-cobertura").textContent = `${r.porcentaje_cobertura}%`;
  $("#k-barra").style.width = `${Math.max(0, Math.min(100, Number(r.porcentaje_cobertura) || 0))}%`;
  $("#k-evidencias").textContent = r.evidencias;
  const i = r.integridad, malas = i.resultados.ALTERADA.length + i.resultados.FALTANTE.length;
  const ki = $("#k-integridad");
  ki.textContent = i.integro ? "Íntegro" : `${malas || "Cadena"} con fallo`;
  ki.className = "cifra " + (i.integro ? "bien" : "mal");
  const pi = $("#p-integridad");
  pi.textContent = i.integro ? `Expediente íntegro (${i.total})` : "Alerta de integridad";
  pi.className = "pastilla " + (i.integro ? "bien" : "mal");
  const claves = Object.keys(r.conteo_estados).sort((a, b) => (ORDEN.indexOf(a) + 99) % 99 - (ORDEN.indexOf(b) + 99) % 99);
  $("#k-estados").innerHTML = claves.map((k) =>
    `<span class="insignia e-${clase(k).replace(/_/g, "-")}">${esc(k)}: ${esc(r.conteo_estados[k])}</span>`).join("") +
    `<small>de ${esc(r.controles_aplicables)} aplicables · rol ${esc(r.rol)} · corte ${esc(r.fecha_corte)}</small>`;
}

/* ------------------------------------------------------------- ejecuciones */
async function cargarEjecuciones() {
  estado.ejecuciones = await api("/api/agente/ejecuciones?proyecto=unsa");
  pintarLista();
  if (!estado.seleccionada) pintarFlujo(null);
}

function pintarLista() {
  const ul = $("#lista-ejecuciones");
  if (!estado.ejecuciones.length) { ul.innerHTML = '<li class="nota">Aún no hay ejecuciones. Inicia una auditoría interna.</li>'; return; }
  ul.innerHTML = estado.ejecuciones.map((e) => `
    <li><button type="button" data-id="${esc(e.id)}" class="${e.id === estado.seleccionada ? "activa" : ""}">
      <span class="cab"><strong>${esc(TIPOS[e.tipo] || e.tipo)}</strong>${insignia(e.estado)}</span>
      <small class="mono">${esc(e.id)} · ${esc(fecha(e.creado))}</small>
    </button></li>`).join("");
}
$("#lista-ejecuciones").addEventListener("click", (ev) => {
  const b = ev.target.closest("button[data-id]");
  if (b) seleccionar(b.dataset.id).catch(aviso);
});
$("#btn-refrescar").addEventListener("click", () => {
  Promise.all([cargarEjecuciones(), cargarResumen()]).catch(aviso);
  if (estado.seleccionada) seleccionar(estado.seleccionada, true).catch(aviso);
});

async function seleccionar(id, forzar = false) {
  clearTimeout(estado.temporizador);
  if (estado.seleccionada !== id) { estado.firma = ""; estado.seleccionada = id; }
  const e = await api(`/api/agente/ejecuciones/${encodeURIComponent(id)}`);
  if (estado.seleccionada !== id) return;
  const i = estado.ejecuciones.findIndex((x) => x.id === id);
  if (i >= 0) estado.ejecuciones[i] = e; else estado.ejecuciones.unshift(e);
  pintarLista();
  const firma = `${e.estado}|${e.actualizado}|${e.paso_actual}`;
  if (forzar || firma !== estado.firma) {
    const antes = estado.firma.split("|")[0];
    estado.firma = firma;
    pintarDetalle(e);
    pintarFlujo(e);
    if (antes === "en_curso" && e.estado !== "en_curso") cargarResumen().catch(() => {});
  }
  if (e.estado === "en_curso") estado.temporizador = setTimeout(() => seleccionar(id).catch(() => {}), 2000);
}

function pintarDetalle(e) {
  const par = Object.entries(e.parametros || {}).map(([k, v]) => `${esc(k)}=${esc(JSON.stringify(v))}`).join(" · ");
  let html = `
    <div class="cab-ejecucion"><h2>${esc(TIPOS[e.tipo] || e.tipo)}</h2>${insignia(e.estado)}
      <small class="mono">${esc(e.id)}</small></div>
    <div class="parametros">Creada ${esc(fecha(e.creado))} · actualizada ${esc(fecha(e.actualizado))}${par ? " · " + par : ""}</div>
    <ol class="linea-tiempo">${(e.pasos || []).map((p) => `
      <li class="p-${clase(p.estado)}">
        <div class="titulo-paso">${esc(p.titulo || p.nodo)} ${insignia(p.estado)} <small class="mono">${esc(p.nodo)}</small></div>
        ${p.resumen ? `<div class="resumen">${esc(p.resumen)}</div>` : ""}
        ${p.inicio ? `<small>${esc(fecha(p.inicio))}${p.fin ? " → " + esc(fecha(p.fin)) : ""}</small>` : ""}
      </li>`).join("")}</ol>`;
  if (e.error) html += `<div class="alerta error-ej">Error: ${esc(e.error)}</div>`;
  if (e.estado === "esperando_aprobacion" && e.aprobacion) html += panelHitl(e);
  else if (e.aprobacion && (e.aprobacion.hallazgos || []).length && e.estado !== "completada") html += listaHallazgos(e.aprobacion.hallazgos);
  if (e.resultado) html += resultado(e);
  const cont = $("#detalle");
  cont.innerHTML = html;
  if (e.estado === "esperando_aprobacion") conectarHitl(e);
  if (e.informe_nombre) cargarInforme(e.informe_nombre);
}

function listaHallazgos(hallazgos) {
  return `<h3>Hallazgos (${hallazgos.length}) ${PRELIMINAR}</h3><ul class="hallazgos">${hallazgos.map((h) => `
    <li><span class="ref">${esc(h.ref)}</span> <span class="insignia e-${clase(h.estado)}">${esc(h.estado)}</span>
      <div class="md">${md(h.texto || "")}</div></li>`).join("")}</ul>`;
}

function panelHitl(e) {
  const a = e.aprobacion, props = a.propuestas || [];
  return `<div class="hitl" id="hitl">
    <h3>Aprobación del auditor (human-in-the-loop)</h3>
    ${PRELIMINAR}
    <p class="pregunta">${esc(a.pregunta || "¿Apruebas los resultados preliminares del agente?")}</p>
    ${listaHallazgos(a.hallazgos || [])}
    <h3>Propuestas de pertinencia (${props.length})</h3>
    ${props.length ? `<ul class="hallazgos">${props.map((p, i) => `
      <li class="propuesta">
        <span><span class="ref">${esc(p.ref)}</span><br><span class="insignia v-${clase(p.veredicto)}">${esc(p.veredicto)}</span></span>
        <span>${esc(p.justificacion)}</span>
        <span class="decision-control">
          <label><input type="radio" name="dc-${i}" value="aceptada" data-ref="${esc(p.ref)}"> Aceptar</label>
          <label><input type="radio" name="dc-${i}" value="rechazada" data-ref="${esc(p.ref)}"> Rechazar</label>
        </span>
      </li>`).join("")}</ul>` : '<p class="nota">Sin propuestas (modo rápido o ningún control evaluable).</p>'}
    <div class="fila-campos">
      <label>Auditor que valida<input type="text" id="hitl-auditor" placeholder="Nombre del auditor" autocomplete="name"></label>
      <label>Comentario<input type="text" id="hitl-comentario" placeholder="Observaciones (opcional)"></label>
    </div>
    <div class="acciones">
      <button class="boton" type="button" data-decision="aprobada">Aprobar</button>
      <button class="boton rechazar" type="button" data-decision="rechazada">Rechazar</button>
    </div></div>`;
}

function conectarHitl(e) {
  const hitl = $("#hitl");
  try { $("#hitl-auditor").value = localStorage.getItem("agente.auditor") || ""; } catch (_) { /* sin almacenamiento */ }
  hitl.querySelectorAll("button[data-decision]").forEach((b) => b.addEventListener("click", async () => {
    const auditor = $("#hitl-auditor").value.trim();
    if (!auditor) { $("#hitl-auditor").focus(); return aviso(new Error("Indica el nombre del auditor que valida")); }
    const decisiones = {};
    hitl.querySelectorAll('input[type=radio][data-ref]:checked').forEach((r) => { decisiones[r.dataset.ref] = r.value; });
    const faltan = (e.aprobacion.propuestas || []).length - Object.keys(decisiones).length;
    if (b.dataset.decision === "aprobada" && faltan > 0 &&
        !confirm(`Quedan ${faltan} propuesta(s) sin decidir; no se registrará decisión sobre ellas. ¿Continuar?`)) return;
    try { localStorage.setItem("agente.auditor", auditor); } catch (_) { /* sin almacenamiento */ }
    hitl.querySelectorAll("button").forEach((x) => { x.disabled = true; });
    try {
      await api(`/api/agente/ejecuciones/${encodeURIComponent(e.id)}/aprobar`, json({
        decision: b.dataset.decision, auditor, comentario: $("#hitl-comentario").value.trim(),
        decisiones_controles: decisiones }));
      await seleccionar(e.id, true);
      cargarResumen().catch(() => {});
    } catch (err) {
      hitl.querySelectorAll("button").forEach((x) => { x.disabled = false; });
      aviso(err);
    }
  }));
}

function resultado(e) {
  const r = e.resultado || {}, plan = r.plan_accion || [];
  let html = "";
  if (plan.length) {
    const columnas = [...new Set(plan.flatMap((p) => (p && typeof p === "object" ? Object.keys(p) : ["acción"])))];
    html += `<h3>Plan de acción (${plan.length})</h3><div class="tabla-envoltura"><table class="tabla"><thead><tr>
      ${columnas.map((c) => `<th>${esc(c.replace(/_/g, " "))}</th>`).join("")}</tr></thead><tbody>
      ${plan.map((p) => `<tr>${columnas.map((c) => {
        const v = p && typeof p === "object" ? p[c] : p;
        return `<td${c === "ref" ? ' class="ref"' : ""}>${esc(v && typeof v === "object" ? JSON.stringify(v) : v)}</td>`;
      }).join("")}</tr>`).join("")}</tbody></table></div>`;
  }
  if (e.informe_nombre) {
    html += `<div class="informe"><div class="tarjeta-cab"><h3>Informe: <span class="mono">${esc(e.informe_nombre)}</span></h3>
      <a class="boton mini secundario" target="_blank" rel="noopener"
         href="/api/agente/informe/${encodeURIComponent(e.informe_nombre)}">Ver JSON</a></div>
      <div id="informe-aviso"></div><div class="md" id="informe-md"><p class="nota">Cargando informe…</p></div></div>`;
  } else if (r.informe && typeof r.informe === "object") {
    html += `<pre class="documento">${esc(JSON.stringify(r.informe, null, 2))}</pre>`;
  }
  return html;
}

async function cargarInforme(nombre) {
  try {
    const d = await api(`/api/agente/informe/${encodeURIComponent(nombre)}`);
    const caja = $("#informe-md");
    if (!caja) return;
    caja.innerHTML = md(d.contenido);
    if (!/Validado por el auditor/i.test(d.contenido)) $("#informe-aviso").innerHTML = PRELIMINAR;
  } catch (err) {
    const caja = $("#informe-md");
    if (caja) caja.innerHTML = `<p class="alerta">${esc(err.message)}</p>`;
  }
}

/* ------------------------------------------------------------------- flujo */
function pintarFlujo(e) {
  let ej = e && e.tipo === "auditoria_interna" ? e : estado.ejecuciones.find((x) => x.tipo === "auditoria_interna");
  const pasos = ej && ej.pasos && ej.pasos.length ? ej.pasos
    : FLUJO_POR_DEFECTO.map(([nodo, titulo]) => ({ nodo, titulo, estado: "pendiente" }));
  const actual = ej ? ej.paso_actual : null;
  $("#flujo-nota").textContent = ej ? `Ejecución ${ej.id} · ${NOMBRES_ESTADO[ej.estado] || ej.estado}` : "Flujo de referencia";
  $("#flujo").innerHTML = pasos.map((p, i) => {
    const hitl = /aprob|hitl|humano|auditor/i.test(p.nodo + " " + (p.titulo || ""));
    const cls = ["nodo-flujo", `f-${clase(p.estado)}`, hitl ? "f-hitl" : "",
      p.nodo === actual && ej && ej.estado !== "completada" ? "actual" : ""].join(" ");
    return (i ? '<span class="flecha" aria-hidden="true">→</span>' : "") +
      `<div class="${cls}" title="${esc(NOMBRES_ESTADO[p.estado] || p.estado)}"><b>${esc(p.nodo)}</b>${esc(p.titulo || p.nodo)}</div>`;
  }).join("");
}

/* ------------------------------------------------------------- lanzadores */
document.querySelectorAll('input[name=modo]').forEach((r) => r.addEventListener("change", () => {
  const ia = document.querySelector('input[name=modo]:checked').value === "ia";
  $("#max-hallazgos").disabled = !ia; $("#max-pertinencia").disabled = !ia;
}));

$("#btn-auditoria").addEventListener("click", async (ev) => {
  const b = ev.currentTarget;
  const rapido = document.querySelector('input[name=modo]:checked').value === "rapido";
  const parametros = { modo_rapido: rapido };
  if (!rapido) {
    parametros.max_hallazgos = Math.max(0, parseInt($("#max-hallazgos").value, 10) || 0);
    parametros.max_pertinencia = Math.max(0, parseInt($("#max-pertinencia").value, 10) || 0);
  }
  b.disabled = true;
  try {
    const e = await api("/api/agente/ejecuciones", json({ tipo: "auditoria_interna", proyecto: "unsa", parametros }));
    await cargarEjecuciones();
    await seleccionar(e.id);
  } catch (err) { aviso(err); } finally { b.disabled = false; }
});

$("#btn-incidente").addEventListener("click", async (ev) => {
  const b = ev.currentTarget, descripcion = $("#incidente").value.trim();
  if (!descripcion) { $("#incidente").focus(); return; }
  b.disabled = true;
  try {
    const r = await api("/api/agente/incidente", json({ descripcion }));
    $("#incidente").value = "";
    await cargarEjecuciones();
    const id = r && (r.id || (r.ejecucion && r.ejecucion.id));
    if (id) await seleccionar(id);
    else alert("Incidente notificado al agente.");
  } catch (err) { aviso(err); } finally { b.disabled = false; }
});

/* ---------------------------------------------------------------- bandeja */
const zona = $("#zona-bandeja");
["dragenter", "dragover"].forEach((t) => zona.addEventListener(t, (e) => { e.preventDefault(); zona.classList.add("encima"); }));
["dragleave", "drop"].forEach((t) => zona.addEventListener(t, (e) => { e.preventDefault(); zona.classList.remove("encima"); }));
zona.addEventListener("drop", (e) => subirBandeja(e.dataTransfer.files));
$("#archivo-bandeja").addEventListener("change", (e) => { subirBandeja(e.target.files); e.target.value = ""; });

async function subirBandeja(archivos) {
  if (!archivos || !archivos.length) return;
  const fd = new FormData();
  [...archivos].forEach((a) => fd.append("archivo", a));
  const nota = $("#estado-bandeja");
  nota.textContent = "Subiendo…";
  try {
    const r = await api("/api/agente/bandeja", { method: "POST", body: fd });
    nota.textContent = `Dejado(s) en la bandeja: ${r.guardados.join(", ")}`;
    await cargarBandeja();
    setTimeout(() => cargarEjecuciones().catch(() => {}), 3000);
  } catch (err) { nota.textContent = err.message; }
}

async function cargarBandeja() {
  const d = await api("/api/agente/bandeja");
  $("#tabla-bandeja tbody").innerHTML = d.archivos.length ? d.archivos.map((a) => `
    <tr><td>${esc(a.carpeta ? a.carpeta + "/" : "")}<strong>${esc(a.nombre)}</strong><br>
      <small>${esc((a.bytes / 1024).toFixed(1))} KB · ${esc(fecha(a.modificado))}</small></td></tr>`).join("")
    : '<tr><td class="nota">La bandeja está vacía.</td></tr>';
  if (!d.automatizacion) $("#estado-bandeja").textContent ||= "La automatización de la bandeja no está activa.";
}

/* -------------------------------------------------------------- bitácoras */
const CAMPOS_FECHA = ["fecha", "momento", "ts", "timestamp", "hora", "creado", "cuando"];
const CAMPOS_TIPO = ["tipo", "evento", "accion", "herramienta", "decision", "nodo"];

$("#subpestanas").addEventListener("click", (e) => {
  const b = e.target.closest("[data-bitacora]");
  if (!b) return;
  estado.bitacora = b.dataset.bitacora;
  document.querySelectorAll("#subpestanas .chip-tab").forEach((x) => x.classList.toggle("activa", x === b));
  cargarBitacora().catch(aviso);
});

async function cargarBitacora() {
  const d = await api(`/api/agente/bitacora?tipo=${encodeURIComponent(estado.bitacora)}`);
  $("#tabla-bitacora thead").innerHTML = "<tr><th>Fecha</th><th>Tipo</th><th>Detalle</th></tr>";
  $("#tabla-bitacora tbody").innerHTML = d.registros.length ? d.registros.map((r) => {
    const resto = { ...r };
    const kf = CAMPOS_FECHA.find((k) => k in r), kt = CAMPOS_TIPO.find((k) => k in r);
    if (kf) delete resto[kf];
    if (kt) delete resto[kt];
    return `<tr><td class="mono sin-corte">${esc(kf ? fecha(r[kf]) : "")}</td>
      <td><strong>${esc(kt ? r[kt] : "")}</strong></td>
      <td><pre>${esc(JSON.stringify(resto, null, 1))}</pre></td></tr>`;
  }).join("") : '<tr><td colspan="3" class="nota">Sin registros todavía.</td></tr>';
}

/* ----------------------------------------------------------- herramientas */
async function cargarHerramientas() {
  const lista = await api("/api/agente/herramientas");
  $("#tabla-herramientas tbody").innerHTML = lista.map((h) => `
    <tr><td><span class="ref">${esc(h.nombre)}</span><br><small class="mono">${esc(h.firma)}</small></td>
      <td><span class="insignia ${h.ia ? "ia" : "det"}">${h.ia ? "Con IA local" : "Determinista"}</span></td>
      <td><pre>${esc(h.doc)}</pre></td></tr>`).join("");
}

/* ------------------------------------------------------------------ inicio */
pintarFlujo(null);
Promise.all([cargarResumen(), cargarEjecuciones(), cargarBandeja()]).then(() => {
  const pendiente = estado.ejecuciones.find((e) => e.estado === "en_curso" || e.estado === "esperando_aprobacion");
  if (pendiente) return seleccionar(pendiente.id);
}).catch(aviso);
/* La lista se refresca sola: el agente también trabaja en segundo plano (bandeja, incidentes). */
setInterval(() => { if (!document.hidden) cargarEjecuciones().catch(() => {}); }, 10000);
