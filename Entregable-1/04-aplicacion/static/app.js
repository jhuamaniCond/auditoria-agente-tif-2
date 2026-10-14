/* AUDITA-PIMS - interfaz en JavaScript puro (sin frameworks). */
"use strict";

const $ = (sel) => document.querySelector(sel);
const estado = { catalogo: [], cobertura: null, historial: [], subida: null, controles: [], evaluando: null,
  proyecto: null, proyectos: [] };
const ORDEN = ["Cubierto", "Parcial", "Desactualizada", "Comprometida", "Sin evidencia", "No aplica"];

function clase(texto) {
  return texto.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/\s+/g, "-");
}
function esc(t) {
  return String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
/* Toda petición va al proyecto activo: el servidor solo ve su expediente. */
async function api(ruta, opciones = {}) {
  const headers = { ...(opciones.headers || {}) };
  if (estado.proyecto) headers["X-Proyecto"] = estado.proyecto.id;
  const r = await fetch(ruta, { ...opciones, headers });
  const datos = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(datos.error || `Error ${r.status}`);
  return datos;
}
function json(cuerpo) {
  return { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo) };
}
function hoy() {
  const d = new Date();               // fecha local, no UTC
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}

/* Markdown minimo: encabezados, negrita, codigo, listas y tablas. */
function md(texto) {
  const lineas = esc(texto).split("\n");
  let html = "", tabla = [], lista = null;
  const enLinea = (s) => s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/`(.+?)`/g, "<code>$1</code>");
  const cerrarTabla = () => {
    if (!tabla.length) return;
    const filas = tabla.filter((f) => !/^\s*\|?\s*:?-{2,}/.test(f));
    html += "<table>" + filas.map((f, i) => {
      const celdas = f.trim().replace(/^\||\|$/g, "").split("|");
      const t = i === 0 ? "th" : "td";
      return "<tr>" + celdas.map((c) => `<${t}>${enLinea(c.trim())}</${t}>`).join("") + "</tr>";
    }).join("") + "</table>";
    tabla = [];
  };
  const cerrarLista = () => { if (lista) { html += `</${lista}>`; lista = null; } };
  for (const l of lineas) {
    if (/^\s*\|/.test(l)) { cerrarLista(); tabla.push(l); continue; }
    cerrarTabla();
    let m;
    if ((m = l.match(/^(#{1,4})\s+(.*)/))) { cerrarLista(); html += `<h3>${enLinea(m[2])}</h3>`; }
    else if ((m = l.match(/^\s*[-*]\s+(.*)/))) { if (lista !== "ul") { cerrarLista(); html += "<ul>"; lista = "ul"; } html += `<li>${enLinea(m[1])}</li>`; }
    else if ((m = l.match(/^\s*\d+[.)]\s+(.*)/))) { if (lista !== "ol") { cerrarLista(); html += "<ol>"; lista = "ol"; } html += `<li>${enLinea(m[1])}</li>`; }
    else if (l.trim()) { cerrarLista(); html += `<p>${enLinea(l)}</p>`; }
    else cerrarLista();
  }
  cerrarTabla(); cerrarLista();
  return html;
}

/* ---------------------------------------------------------------- pestañas */
function irA(vista) {
  document.querySelectorAll(".pestana").forEach((x) => x.classList.toggle("activa", x.dataset.vista === vista));
  document.querySelectorAll(".vista").forEach((v) => v.classList.toggle("activa", v.id === "vista-" + vista));
  // Al volver a Cobertura se recarga: la matriz pudo cambiar mientras estabas en otra pestaña.
  if (vista === "cobertura") cargarCobertura().catch((err) => alertaSuave(err));
  // El grafo se recarga al entrar: refleja evidencias y estados recién cambiados.
  if (vista === "grafo") cargarGrafo().catch(errorGrafo);
}
document.querySelectorAll(".pestana").forEach((b) => b.addEventListener("click", () => irA(b.dataset.vista)));

/* ------------------------------------------------------------------ estado */
const idActivo = () => estado.proyecto && estado.proyecto.id;

async function cargarEstado() {
  if (!estado.proyecto) return;
  const pid = idActivo();
  const d = await api("/api/estado");
  if (idActivo() !== pid) return;     // se cambió de proyecto mientras llegaba la respuesta
  Object.assign(estado.proyecto, d.proyecto);
  pintarSelectorProyectos();
  const m = d.modelo;
  const pm = $("#p-modelo");
  pm.textContent = m.listo ? `LLM local: ${m.chat}` : (m.activo ? "Faltan modelos en Ollama" : "Ollama apagado");
  pm.className = "pastilla " + (m.listo ? "bien" : "mal");
  const pr = $("#p-rag");
  pr.textContent = `FAISS · ${m.embeddings} · ${d.rag.fragmentos} fragmentos (${d.rag.norma} de ISO 27701)`;
  pr.title = d.rag.norma ? "La norma de ISOS/texto está indexada" : "Sin texto de la norma: ejecuta python extraer_norma.py";
  pr.className = "pastilla " + (d.rag.fragmentos ? "bien" : "mal");
  const i = d.integridad, malas = [...i.resultados.ALTERADA, ...i.resultados.FALTANTE];
  const pi = $("#p-integridad");
  pi.textContent = i.integro ? `Expediente íntegro (${i.total})` : `Integridad: ${malas.length || "cadena"} con fallo`;
  pi.className = "pastilla " + (i.integro ? "bien" : "mal");

  const alerta = $("#alerta-integridad");
  if (i.integro) alerta.classList.add("oculto");
  else {
    const partes = [];
    if (i.resultados.ALTERADA.length) partes.push(`alterada(s): ${i.resultados.ALTERADA.join(", ")}`);
    if (i.resultados.FALTANTE.length) partes.push(`faltante(s): ${i.resultados.FALTANTE.join(", ")}`);
    if (i.problemas_cadena.length) partes.push(`cadena de custodia rota: ${i.problemas_cadena.join("; ")}`);
    alerta.textContent = "Alerta de integridad — " + partes.join(" · ") + ". Estas evidencias no sirven como prueba hasta aclararlo.";
    alerta.classList.remove("oculto");
  }

  const tbody = $("#tabla-evidencias tbody");
  tbody.innerHTML = d.evidencias.length ? d.evidencias.map((ev) => `
    <tr>
      <td>${botonEvidencia(ev.id)}</td>
      <td>${esc(ev.titulo)}<br><small>${esc(ev.tipo)} · ${esc(ev.fuente || "sin fuente")}</small></td>
      <td class="mono">${ev.controles.map(esc).join(", ")}</td>
      <td class="mono sin-corte">${esc(ev.fecha_documento)}</td>
      <td class="mono" title="${esc(ev.sha256)}">${esc(ev.sha256.slice(0, 12))}…</td>
      <td><span class="insignia i-${clase(ev.integridad)}">${esc(ev.integridad)}</span></td>
    </tr>`).join("") : `<tr><td colspan="6" class="nota">El expediente está vacío. Registra la primera evidencia.</td></tr>`;
}

$("#tabla-evidencias").addEventListener("click", (e) => {
  if (e.target.dataset.evidencia) mostrarEvidencia(e.target.dataset.evidencia);
});

$("#btn-verificar").addEventListener("click", async (e) => {
  e.target.disabled = true;
  try {
    const r = await api("/api/verificar", { method: "POST" });
    $("#nota-verificacion").textContent = `Verificación anotada en la cadena de custodia: ${r.resultados.OK.length} OK, ` +
      `${r.resultados.ALTERADA.length} alteradas, ${r.resultados.FALTANTE.length} faltantes; cadena ${r.problemas_cadena.length ? "ROTA" : "íntegra"}.`;
    await cargarEstado();
  } catch (err) { $("#nota-verificacion").textContent = err.message; }
  e.target.disabled = false;
});

/* ---------------------------------------------------------------- registro */
const zona = $("#zona-archivo");
$("#archivo").addEventListener("change", () => { $("#nombre-archivo").textContent = $("#archivo").files[0]?.name || ""; });
["dragover", "dragenter"].forEach((t) => zona.addEventListener(t, (e) => { e.preventDefault(); zona.classList.add("encima"); }));
["dragleave", "drop"].forEach((t) => zona.addEventListener(t, () => zona.classList.remove("encima")));
zona.addEventListener("drop", (e) => {
  e.preventDefault();
  $("#archivo").files = e.dataTransfer.files;
  $("#nombre-archivo").textContent = e.dataTransfer.files[0]?.name || "";
});

function pintarChips() {
  $("#chips-controles").innerHTML = estado.controles.map((c) => `<button type="button" class="chip" data-ref="${esc(c)}">${esc(c)}</button>`).join("");
}
$("#chips-controles").addEventListener("click", (e) => {
  const ref = e.target.dataset.ref;
  if (ref) { estado.controles = estado.controles.filter((c) => c !== ref); pintarChips(); }
});
$("#agregar-control").addEventListener("change", (e) => {
  const v = e.target.value;
  if (v && !estado.controles.includes(v)) { estado.controles.push(v); pintarChips(); }
  e.target.value = "";
});

$("#form-subir").addEventListener("submit", async (e) => {
  e.preventDefault();
  const archivo = $("#archivo").files[0];
  if (!archivo) return;
  const boton = $("#btn-analizar");
  boton.disabled = true; boton.textContent = "Analizando con el modelo local…";
  $("#nota-registro").textContent = "";
  try {
    const fd = new FormData(); fd.append("archivo", archivo);
    const s = await api("/api/sugerir", { method: "POST", body: fd });
    estado.subida = s;
    estado.controles = [...s.controles];
    pintarChips();
    $("#tipo").value = s.tipo;
    $("#titulo").value = s.titulo;
    $("#fecha").value = s.fecha_documento || "";
    $("#sugerencia").innerHTML = `<strong>Propuesta del asistente:</strong> ${esc(s.justificacion || "sin justificación")}<br>` +
      `<small>Candidatos por similitud: ${s.candidatos.map((c) => `${esc(c.ref)} (${c.similitud})`).join(", ")}</small>`;
    $("#form-subir").classList.add("oculto");
    $("#form-registrar").classList.remove("oculto");
  } catch (err) { $("#nota-registro").textContent = err.message; }
  boton.disabled = false; boton.textContent = "Analizar con IA local";
});

function reiniciarRegistro() {
  estado.subida = null;
  $("#form-registrar").classList.add("oculto");
  $("#form-subir").classList.remove("oculto");
  $("#form-subir").reset();
  $("#nombre-archivo").textContent = "Elige o arrastra un archivo (.md, .txt, .csv, .pdf…)";
}
$("#btn-cancelar").addEventListener("click", reiniciarRegistro);

$("#form-registrar").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!estado.controles.length) { $("#nota-registro").textContent = "Indica al menos un control."; return; }
  try {
    const ev = await api("/api/registrar", json({
      token: estado.subida.token, nombre: estado.subida.nombre, controles: estado.controles,
      tipo: $("#tipo").value, titulo: $("#titulo").value, fecha_documento: $("#fecha").value,
      responsable: $("#responsable").value, fuente: $("#fuente").value,
    }));
    $("#nota-registro").textContent = `${ev.id} registrada · SHA-256 ${ev.sha256.slice(0, 16)}… · anotada en la cadena de custodia.`;
    reiniciarRegistro();
    estado.cobertura = null;
    await cargarEstado();
  } catch (err) { $("#nota-registro").textContent = err.message; }
});

/* --------------------------------------------------------------- cobertura */
function parametros() {
  return { rol: $("#rol").value, vigencia: $("#vigencia").value, fecha: $("#fecha-corte").value || hoy() };
}
async function cargarCobertura() {
  if (!estado.proyecto) return;
  const pid = idActivo();
  const c = await api("/api/cobertura?" + new URLSearchParams(parametros()));
  if (idActivo() !== pid) return;
  estado.cobertura = c;
  const kp = c.conteo_estados;
  const pct = (n) => n.toFixed(1).replace(".", ",");
  const revisada = c.degradados.length
    ? `<div class="rotulo">Automática ${pct(c.porcentaje_automatico)} % · bajados por revisión: ${c.degradados.map(esc).join(", ")}</div>` : "";
  $("#kpis").innerHTML = `
    <div class="kpi principal"><div class="cifra">${pct(c.porcentaje_cobertura)} %</div>
      <div class="rotulo">Cobertura · ${kp.Cubierto} de ${c.controles_aplicables} aplicables</div>${revisada}
      <div class="barra-cob"><span style="width:${c.porcentaje_cobertura}%"></span></div></div>` +
    ORDEN.map((e) => `<div class="kpi"><div class="cifra">${kp[e]}</div><div class="rotulo"><span class="insignia e-${clase(e)}">${e}</span></div></div>`).join("");
  const filtro = $("#filtro-estado");
  if (filtro.options.length === 1) {
    ORDEN.forEach((e) => filtro.add(new Option(e, e)));
    filtro.add(new Option("Revisión IA por decidir", FILTRO_POR_DECIDIR));
  }
  pintarCobertura();
}
const FILTRO_POR_DECIDIR = "__por_decidir";
const porDecidir = (x) => evaluable(x) && x.revision && x.revision.vigente && !x.revision.decision;
function pintarCobertura() {
  const f = $("#filtro-estado").value;
  const filas = estado.cobertura.controles.filter((x) =>
    !f || (f === FILTRO_POR_DECIDIR ? porDecidir(x) : x.estado === f));
  pintarResumenRevision();
  $("#tabla-cobertura tbody").innerHTML = filas.map((x) => `
    <tr>
      <td><button class="ref enlace-norma" data-norma="${esc(x.ref)}" title="Ver el texto de ISO/IEC 27701:2025">${esc(x.ref)}</button></td>
      <td>${esc(x.titulo)}</td>
      <td><span class="insignia e-${clase(x.estado)}">${esc(x.estado)}</span></td>
      <td class="mono">${x.evidencias.map(botonEvidencia).join(", ") || "—"}</td>
      <td><small>${esc(x.nota || "—")}</small></td>
      <td>${celdaRevision(x)}</td>
      <td>${["Cubierto", "No aplica"].includes(x.estado) ? "" : `<button class="boton secundario mini" data-hallazgo="${esc(x.ref)}">Redactar hallazgo</button>`}</td>
    </tr>`).join("");
}

/* ------------------------------------------------- revisión de pertinencia */
const VEREDICTO = { cumple: "Cumple", cumple_parcialmente: "Cumple parcialmente", no_cumple: "No cumple" };
const evaluable = (x) => ["Cubierto", "Parcial"].includes(x.estado);
function celdaRevision(x) {
  const r = x.revision;
  if (!evaluable(x)) return r ? `<small>${esc(VEREDICTO[r.veredicto])} (no aplicada)</small>` : "—";
  if (!r || !r.vigente) {
    return `<button class="boton secundario mini" data-evaluar="${esc(x.ref)}">Evaluar con IA</button>` +
      (r ? `<br><small>Las evidencias cambiaron</small>` : "");
  }
  const decision = r.decision ? (r.decision === "aceptada" ? "✓ aceptada" : "✕ rechazada") : "pendiente";
  return `<button class="insignia v-${r.veredicto} enlace" data-revision="${esc(x.ref)}">${esc(VEREDICTO[r.veredicto])}</button>` +
    `<br><small class="${r.decision ? "" : "pendiente"}">${decision}</small>`;
}
function filaDe(ref) { return estado.cobertura.controles.find((x) => x.ref === ref); }

function mostrarRevision(ref) {
  const x = filaDe(ref), r = x.revision;
  $("#panel-titulo").textContent = `Revisión de pertinencia · ${ref}`;
  const control = estado.catalogo.find((c) => c.ref === ref);
  const citas = r.citas.length ? "<ul class=\"citas\">" + r.citas.map((c) => `
      <li>${botonEvidencia(c.evidencia, { cita: c.texto, volver: ref })} «${esc(c.texto)}»
        <small class="${c.verificada ? "ok" : "mal"}">${c.verificada ? "✓ cita encontrada en el documento" : "✕ no aparece literal en el documento"}</small></li>`).join("") + "</ul>"
    : "<p><small>El modelo no aportó citas.</small></p>";
  const truncadas = r.truncadas.length
    ? `<p class="aviso-panel">Solo se leyó el inicio de ${r.truncadas.map(esc).join(", ")} (documento largo).</p>` : "";
  const decision = r.decision
    ? `<p class="decision">Decisión del auditor: <strong>${esc(r.decision)}</strong> por ${esc(r.auditor)} el ${esc(r.fecha_decision.slice(0, 16).replace("T", " "))}` +
      `${r.comentario ? ` — «${esc(r.comentario)}»` : ""}. Anotada en la cadena de custodia.</p>
       <button class="boton secundario" data-evaluar="${esc(ref)}">Volver a evaluar con IA</button>`
    : `<label>Auditor<input type="text" id="rev-auditor" placeholder="Nombre de quien decide"></label>
       <label>Comentario<textarea id="rev-comentario" rows="2" placeholder="Opcional: por qué aceptas o rechazas"></textarea></label>
       <div class="acciones">
         <button class="boton" data-decidir="aceptada">Aceptar propuesta</button>
         <button class="boton secundario" data-decidir="rechazada">Rechazar</button>
       </div>
       <p class="ayuda">${r.veredicto === "cumple" || x.estado !== "Cubierto"
         ? "Aceptar deja la matriz como está y registra que el contenido fue revisado."
         : "Si aceptas, el control baja de Cubierto a Parcial y podrás redactar su hallazgo."}</p>`;
  $("#panel-cuerpo").innerHTML = `
    <p><span class="insignia v-${r.veredicto}">${esc(VEREDICTO[r.veredicto])}</span>
       <small>propuesta de ${esc(r.modelo)} · ${esc(r.fecha_ia.slice(0, 16).replace("T", " "))} · evidencias ${Object.keys(r.huellas).map(esc).join(", ")}</small></p>
    <p><small>Evidencia esperada: ${esc(control ? control.evidencia_esperada : "")} ·
       <button class="enlace-norma" data-norma="${esc(ref)}">Ver requisito en ISO/IEC 27701:2025</button></small></p>
    <h3>Justificación</h3><p>${esc(r.justificacion || "—")}</p>
    ${r.falta ? `<h3>Qué falta</h3><p>${esc(r.falta)}</p>` : ""}
    <h3>Citas de las evidencias</h3>${citas}${truncadas}
    <hr>${decision}`;
  $("#panel-cuerpo").dataset.ref = ref;
  $("#panel-hallazgo").classList.remove("oculto");
}

async function evaluar(ref) {
  const r = await api("/api/pertinencia", json({ ref, ...parametros() }));
  return r;
}
async function evaluarYMostrar(ref) {
  $("#panel-titulo").textContent = `Revisión de pertinencia · ${ref}`;
  $("#panel-cuerpo").innerHTML = `<p class="pensando">El modelo local está leyendo las evidencias de ${esc(ref)} y comparándolas con la evidencia esperada…</p>`;
  $("#panel-hallazgo").classList.remove("oculto");
  try {
    await evaluar(ref);
    await cargarCobertura();
    mostrarRevision(ref);
  } catch (err) { $("#panel-cuerpo").innerHTML = `<p>${esc(err.message)}</p>`; }
}

/* Evaluación en lote: el progreso se ve en el botón, en la nota y en una pastilla
   de la cabecera, para que se note desde cualquier pestaña. */
function avisoEvaluacion(texto, tipo = "info") {
  const nota = $("#nota-evaluacion");
  nota.className = `nota-evaluacion ${tipo}` + (texto ? "" : " oculto");
  nota.textContent = texto;
}
function pintarProgreso() {
  const ev = estado.evaluando, boton = $("#btn-evaluar-todos"), pastilla = $("#p-evaluacion");
  boton.disabled = !!ev;
  // Mientras la IA evalúa un expediente no se puede cambiar de organización.
  $("#proyecto").disabled = !!ev;
  $("#btn-nuevo-proyecto").disabled = !!ev;
  boton.textContent = ev ? `Evaluando ${ev.hechos + 1} de ${ev.total}…` : "Evaluar pertinencia con IA";
  pastilla.classList.toggle("oculto", !ev);
  if (ev) {
    pastilla.textContent = `IA evaluando ${ev.actual} (${ev.hechos + 1}/${ev.total})`;
    avisoEvaluacion(`Evaluando ${ev.actual} (${ev.hechos + 1} de ${ev.total}) con el modelo local. ` +
      "Tarda unos 10 s por control; puedes cambiar de pestaña, pero no recargues la página.", "trabajando");
  }
}
$("#p-evaluacion").addEventListener("click", () => irA("cobertura"));
window.addEventListener("beforeunload", (e) => { if (estado.evaluando) e.preventDefault(); });

$("#btn-evaluar-todos").addEventListener("click", async () => {
  if (estado.evaluando) return;
  try { await cargarCobertura(); } catch (err) { avisoEvaluacion(err.message, "error"); return; }
  const pendientes = estado.cobertura.controles.filter((x) => evaluable(x) && !(x.revision && x.revision.vigente));
  if (!pendientes.length) {
    avisoEvaluacion("No hay nada nuevo que evaluar: todos los controles con evidencia válida ya tienen su revisión IA. " +
      "Revisa abajo las propuestas que faltan por decidir.", "info");
    $("#resumen-revision").scrollIntoView({ behavior: "smooth", block: "nearest" });
    return;
  }
  estado.evaluando = { hechos: 0, total: pendientes.length, actual: pendientes[0].ref };
  let fallo = null;
  try {
    for (const x of pendientes) {
      estado.evaluando.actual = x.ref;
      pintarProgreso();
      try { await evaluar(x.ref); }
      catch (err) { fallo = `${x.ref}: ${err.message}`; break; }
      estado.evaluando.hechos++;
      await cargarCobertura().catch(() => {});
    }
  } finally {
    const hechos = estado.evaluando.hechos;
    estado.evaluando = null;
    pintarProgreso();
    await cargarCobertura().catch(() => {});
    if (fallo) avisoEvaluacion(`Se evaluaron ${hechos} de ${pendientes.length}. Se detuvo en ${fallo}. ` +
      "Pulsa el botón otra vez para continuar con los que faltan.", "error");
    else avisoEvaluacion(`Listo: ${hechos} propuestas nuevas. Decide cada una en el resumen de abajo.`, "ok");
  }
});

/* Resumen de la revisión IA encima de la tabla, con acceso directo a cada propuesta. */
function pintarResumenRevision() {
  const caja = $("#resumen-revision");
  const evaluables = estado.cobertura.controles.filter(evaluable);
  const vigentes = evaluables.filter((x) => x.revision && x.revision.vigente);
  if (!vigentes.length) { caja.classList.add("oculto"); return; }
  const cuenta = (v) => vigentes.filter((x) => x.revision.veredicto === v).length;
  const decidir = vigentes.filter((x) => !x.revision.decision);
  const sinEvaluar = evaluables.length - vigentes.length;
  caja.classList.remove("oculto");
  caja.innerHTML = `
    <div><strong>Revisión IA:</strong> ${vigentes.length} de ${evaluables.length} controles con evidencia evaluados ·
      <span class="insignia v-cumple">${cuenta("cumple")} cumple</span>
      <span class="insignia v-cumple_parcialmente">${cuenta("cumple_parcialmente")} cumple parcialmente</span>
      <span class="insignia v-no_cumple">${cuenta("no_cumple")} no cumple</span>
      ${sinEvaluar ? ` · <strong>${sinEvaluar} sin evaluar</strong>` : ""}</div>
    ${decidir.length ? `<div class="por-decidir">Por decidir (${decidir.length}): ` +
      decidir.map((x) => `<button class="insignia v-${x.revision.veredicto} enlace" data-revision="${esc(x.ref)}">${esc(x.ref)}</button>`).join(" ") +
      ` <button class="enlace-norma" data-filtro="${FILTRO_POR_DECIDIR}">ver solo estas en la tabla</button></div>`
      : `<div class="por-decidir">Todas las propuestas tienen decisión del auditor.</div>`}`;
}
$("#resumen-revision").addEventListener("click", (e) => {
  if (e.target.dataset.revision) mostrarRevision(e.target.dataset.revision);
  if (e.target.dataset.filtro) { $("#filtro-estado").value = e.target.dataset.filtro; pintarCobertura(); }
});

/* ------------------------------------------- visor de evidencias (solo lectura) */
function botonEvidencia(id, { cita = "", volver = "" } = {}) {
  return `<button class="ref enlace-norma" data-evidencia="${esc(id)}" data-cita="${esc(cita)}" ` +
    `data-volver="${esc(volver)}" title="Ver el documento">${esc(id)}</button>`;
}

/* CSV sencillo (comas y comillas dobles) a filas de celdas. */
function leerCsv(texto) {
  const filas = [];
  let fila = [], celda = "", comillas = false;
  for (let i = 0; i < texto.length; i++) {
    const c = texto[i];
    if (comillas) {
      if (c === '"' && texto[i + 1] === '"') { celda += '"'; i++; }
      else if (c === '"') comillas = false;
      else celda += c;
    } else if (c === '"') comillas = true;
    else if (c === ",") { fila.push(celda); celda = ""; }
    else if (c === "\n") { fila.push(celda.replace(/\r$/, "")); filas.push(fila); fila = []; celda = ""; }
    else celda += c;
  }
  if (celda || fila.length) { fila.push(celda); filas.push(fila); }
  return filas;
}
function tablaCsv(texto) {
  const filas = leerCsv(texto);
  if (!filas.length) return "<p><small>Archivo vacío.</small></p>";
  return `<div class="desplazable"><table><thead><tr>${filas[0].map((c) => `<th>${esc(c)}</th>`).join("")}</tr></thead><tbody>` +
    filas.slice(1).map((f) => `<tr>${f.map((c) => `<td>${esc(c)}</td>`).join("")}</tr>`).join("") +
    `</tbody></table></div><p><small>${filas.length - 1} filas</small></p>`;
}

/* Los enlaces a archivos no llevan cabeceras: el proyecto va en la URL. */
function urlArchivo(id, descargar = false) {
  return `/api/evidencia/${encodeURIComponent(id)}/archivo?proyecto=${encodeURIComponent(estado.proyecto.id)}` +
    (descargar ? "&descargar=1" : "");
}

function contenidoEvidencia(ev) {
  const url = urlArchivo(ev.id);
  if (!ev.existe) return `<p class="aviso-panel">El archivo no está en el expediente (FALTANTE).</p>`;
  if (ev.formato === "pdf") return `<iframe class="visor-archivo" src="${url}" title="${esc(ev.titulo)}"></iframe>`;
  if (["png", "jpg", "jpeg"].includes(ev.formato)) return `<img class="visor-imagen" src="${url}" alt="${esc(ev.titulo)}">`;
  if (!ev.texto) return `<p>Este formato (.${esc(ev.formato)}) no se puede mostrar como texto.</p>`;
  if (ev.formato === "md") return `<div class="documento">${md(ev.texto)}</div>`;
  if (ev.formato === "csv") return tablaCsv(ev.texto);
  return `<pre class="documento">${esc(ev.texto)}</pre>`;
}

/* Resalta la primera aparición de la cita dentro del documento ya pintado. */
function resaltar(contenedor, cita) {
  const buscada = cita.trim().toLowerCase();
  if (!buscada) return false;
  const recorrido = document.createTreeWalker(contenedor, NodeFilter.SHOW_TEXT);
  for (let n = recorrido.nextNode(); n; n = recorrido.nextNode()) {
    const i = n.nodeValue.toLowerCase().indexOf(buscada);
    if (i < 0) continue;
    const marca = document.createElement("mark");
    const resto = n.splitText(i);
    resto.splitText(buscada.length);
    resto.parentNode.replaceChild(marca, resto);
    marca.appendChild(resto);
    marca.scrollIntoView({ block: "center" });
    return true;
  }
  return false;
}

async function mostrarEvidencia(id, { cita = "", volver = "" } = {}) {
  $("#panel-cuerpo").dataset.ref = "";
  $("#panel-titulo").textContent = `Evidencia · ${id}`;
  $("#panel-cuerpo").innerHTML = `<p class="pensando">Abriendo ${esc(id)}…</p>`;
  $("#panel-hallazgo").classList.remove("oculto");
  try {
    const ev = await api(`/api/evidencia/${encodeURIComponent(id)}`);
    const url = urlArchivo(id, true);
    const alterada = ev.integridad !== "OK"
      ? `<p class="aviso-panel">Integridad ${esc(ev.integridad)}: el archivo no coincide con el hash registrado. Lo que ves no es necesariamente lo que se archivó.</p>` : "";
    $("#panel-cuerpo").innerHTML = `
      ${volver ? `<button class="boton secundario mini" data-revision="${esc(volver)}">← Volver a la revisión de ${esc(volver)}</button>` : ""}
      <h3>${esc(ev.titulo)}</h3>
      <p><small>${esc(ev.tipo)} · fecha ${esc(ev.fecha_documento)} · controles ${ev.controles.map(esc).join(", ")} ·
        ${esc(ev.fuente || "sin fuente")} · registrada ${esc(ev.fecha_registro.slice(0, 10))}</small><br>
        <small class="mono" title="${esc(ev.sha256)}">SHA-256 ${esc(ev.sha256.slice(0, 16))}…</small>
        <span class="insignia i-${clase(ev.integridad)}">${esc(ev.integridad)}</span>
        · <a href="${url}">Descargar original</a></p>
      ${alterada}
      <p class="ayuda">Vista de solo lectura: abrir el documento no lo modifica ni se anota en la cadena de custodia.</p>
      <hr>
      <div id="visor-evidencia">${contenidoEvidencia(ev)}</div>
      ${ev.truncado ? `<p class="aviso-panel">Documento largo: se muestra solo el inicio. Descarga el original para verlo completo.</p>` : ""}`;
    if (cita && !resaltar($("#visor-evidencia"), cita)) {
      $("#visor-evidencia").insertAdjacentHTML("beforebegin", `<p class="ayuda">No se pudo resaltar la cita «${esc(cita)}» en esta vista (puede abarcar varias celdas o líneas); búscala en el texto.</p>`);
    }
  } catch (err) { $("#panel-cuerpo").innerHTML = `<p>${esc(err.message)}</p>`; }
}

/* Texto de la norma (ISOS/texto): requisito del Anexo A o cláusula + guía del Anexo B. */
async function mostrarNorma(ref) {
  $("#panel-cuerpo").dataset.ref = "";
  $("#panel-titulo").textContent = `ISO/IEC 27701:2025 · ${ref}`;
  $("#panel-cuerpo").innerHTML = `<p class="pensando">Buscando ${esc(ref)} en la norma…</p>`;
  $("#panel-hallazgo").classList.remove("oculto");
  try {
    const r = await api(`/api/norma/${encodeURIComponent(ref)}`);
    $("#panel-cuerpo").innerHTML =
      `<p class="aviso-panel">Texto oficial en inglés, extraído por OCR del PDF de <code>ISOS/</code>. Es el criterio que usa la IA al evaluar y redactar hallazgos.</p>` +
      r.secciones.map((s) => `<h3>${esc(s.ref)} ${esc(s.titulo)}</h3><p><small>${esc(s.cita)}</small></p>${md(s.texto)}`).join("<hr>");
  } catch (err) { $("#panel-cuerpo").innerHTML = `<p>${esc(err.message)}</p>`; }
}

$("#panel-cuerpo").addEventListener("click", async (e) => {
  const ref = $("#panel-cuerpo").dataset.ref;
  if (e.target.dataset.norma) { mostrarNorma(e.target.dataset.norma); return; }
  if (e.target.dataset.evidencia) { mostrarEvidencia(e.target.dataset.evidencia, e.target.dataset); return; }
  if (e.target.dataset.revision) { mostrarRevision(e.target.dataset.revision); return; }
  if (e.target.dataset.evaluar) { evaluarYMostrar(e.target.dataset.evaluar); return; }
  const decision = e.target.dataset.decidir;
  if (!decision || !ref) return;
  e.target.disabled = true;
  try {
    await api("/api/pertinencia/decision", json({
      ref, decision, auditor: $("#rev-auditor").value, comentario: $("#rev-comentario").value, ...parametros(),
    }));
    await cargarCobertura();
    mostrarRevision(ref);
  } catch (err) {
    e.target.disabled = false;
    $("#panel-cuerpo").insertAdjacentHTML("beforeend", `<p class="aviso-panel">${esc(err.message)}</p>`);
  }
});
$("#form-cobertura").addEventListener("submit", (e) => { e.preventDefault(); cargarCobertura().catch((err) => alertaSuave(err)); });
$("#filtro-estado").addEventListener("change", pintarCobertura);
$("#tabla-cobertura").addEventListener("click", async (e) => {
  if (e.target.dataset.evaluar) { evaluarYMostrar(e.target.dataset.evaluar); return; }
  if (e.target.dataset.revision) { mostrarRevision(e.target.dataset.revision); return; }
  if (e.target.dataset.norma) { mostrarNorma(e.target.dataset.norma); return; }
  if (e.target.dataset.evidencia) { mostrarEvidencia(e.target.dataset.evidencia); return; }
  const ref = e.target.dataset.hallazgo;
  if (!ref) return;
  $("#panel-cuerpo").dataset.ref = "";
  const panel = $("#panel-hallazgo");
  $("#panel-titulo").textContent = `Hallazgo preliminar · ${ref}`;
  $("#panel-cuerpo").innerHTML = `<p class="pensando">El modelo local está redactando el hallazgo con la plantilla de la skill…</p>`;
  panel.classList.remove("oculto");
  try {
    const r = await api("/api/hallazgo", json({ ref, ...parametros() }));
    $("#panel-cuerpo").innerHTML = md(r.hallazgo);
  } catch (err) { $("#panel-cuerpo").innerHTML = `<p>${esc(err.message)}</p>`; }
});
$("#btn-cerrar-panel").addEventListener("click", () => $("#panel-hallazgo").classList.add("oculto"));
function alertaSuave(err) { console.error(err); }

/* ------------------------------------------------------------------- chat */
function agregarMensaje(rol, html) {
  const div = document.createElement("div");
  div.className = "mensaje " + rol;
  div.innerHTML = `<div class="burbuja">${html}</div>`;
  $("#mensajes").appendChild(div);
  $("#mensajes").scrollTop = $("#mensajes").scrollHeight;
  return div;
}
async function preguntar(texto) {
  agregarMensaje("usuario", esc(texto));
  const espera = agregarMensaje("asistente", `<span class="pensando">Buscando en el conocimiento y consultando el modelo local…</span>`);
  const pid = idActivo();
  try {
    const r = await api("/api/chat", json({ mensaje: texto, historial: estado.historial, ...parametros() }));
    if (idActivo() !== pid) return;   // la conversación era de otro proyecto
    const fuentes = [...new Set(r.fuentes.map((f) => f.fuente))].map((f) => `<span>${esc(f)}</span>`).join("");
    const verGrafo = r.nodos && r.nodos.length ? ` · <button class="ver-grafo" data-ir-grafo="1">Ver en el grafo</button>` : "";
    espera.querySelector(".burbuja").innerHTML = md(r.respuesta) + `<div class="fuentes">Fuentes recuperadas: ${fuentes}${verGrafo}</div>`;
    grafo.usados = r.nodos || [];
    grafo.pregunta = texto;
    if (grafo.datos) marcarUsados();
    estado.historial.push({ role: "user", content: texto }, { role: "assistant", content: r.respuesta });
  } catch (err) { espera.querySelector(".burbuja").textContent = err.message; }
}
$("#form-chat").addEventListener("submit", (e) => {
  e.preventDefault();
  const t = $("#pregunta").value.trim();
  if (t) { $("#pregunta").value = ""; preguntar(t); }
});
$("#pregunta").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); $("#form-chat").requestSubmit(); }
});
$("#mensajes").addEventListener("click", (e) => { if (e.target.dataset.irGrafo) irA("grafo"); });
$("#sugeridas").addEventListener("click", (e) => { if (e.target.tagName === "BUTTON") preguntar(e.target.textContent); });

/* ------------------------------------------------------------------- grafo */
/* Grafo de conocimiento: lo que el agente sabe ahora (fuentes del RAG, controles,
   evidencias del proyecto) y cómo se relaciona. Disposición por fuerzas en SVG,
   sin librerías. Las posiciones se conservan entre recargas. */
const SVG_NS = "http://www.w3.org/2000/svg";
const grafo = {
  datos: null, nodos: [], aristas: [], porId: new Map(), vecinos: new Map(), pos: new Map(),
  vista: { x: 0, y: 0, k: 1 }, seleccion: null, usados: [], pregunta: "", calor: 0, animando: false,
  filtros: { semejanza: true, remite: true, evidencia: true, estructura: true },
};
const RADIO = { agente: 20, proyecto: 15, fuente: 11, grupo: 12, control: 8, evidencia: 7 };
const LARGO = { conoce: 130, audita: 170, organiza: 120, define: 150, incluye: 55, remite: 90, semejanza: 80, aporta: 70, respalda: 80 };
const FUERZA = { semejanza: 0.012, remite: 0.02, define: 0.01, aporta: 0.02 };
const ESTRUCTURA = new Set(["conoce", "audita", "organiza", "define", "incluye"]);
const RELACION = {   // [vista desde el origen, vista desde el destino]
  conoce: ["conoce", "conocida por"], audita: ["audita", "auditada por"], organiza: ["organiza", "organizado por"],
  define: ["define", "definido en"], incluye: ["incluye", "pertenece a"], remite: ["remite a", "citado por"],
  semejanza: ["semejante a", "semejante a"], aporta: ["aporta", "aportada por"], respalda: ["respalda", "respaldado por"],
};
const TIPO_NODO = { agente: "Agente", fuente: "Fuente de conocimiento", grupo: "Grupo de controles", control: "Control",
  proyecto: "Organización auditada", evidencia: "Evidencia" };

function svgEl(nombre, attrs = {}) {
  const e = document.createElementNS(SVG_NS, nombre);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  return e;
}

async function cargarGrafo() {
  if (!estado.proyecto) return;
  const pid = idActivo();
  const d = await api("/api/grafo?" + new URLSearchParams(parametros()));
  if (idActivo() !== pid) return;
  armarGrafo(d);
}

/* Posición inicial de un nodo nuevo: cada tipo en su zona, para que la
   disposición por fuerzas parta de algo ordenado. */
function posicionInicial(n, grupos, fuentes, azar) {
  if (n.tipo === "fuente") {
    const a = Math.PI + (fuentes.indexOf(n.id) + 0.5) / fuentes.length * Math.PI;
    return { x: 150 * Math.cos(a), y: 150 * Math.sin(a) };
  }
  if (n.tipo === "grupo" || n.tipo === "control") {
    const i = grupos.indexOf(n.tipo === "grupo" ? n.id : "grp:" + n.grupo);
    const a = Math.PI + (i + 0.5) / grupos.length * Math.PI;
    const r = n.tipo === "grupo" ? 260 : 340;
    return { x: r * Math.cos(a) + azar() * 90, y: r * Math.sin(a) + azar() * 90 };
  }
  if (n.tipo === "proyecto") return { x: 0, y: 220 };
  if (n.tipo === "evidencia") return { x: azar() * 260, y: 300 + azar() * 60 };
  return { x: 0, y: 0 };
}

function armarGrafo(d) {
  grafo.datos = d;
  let semilla = 7;
  const azar = () => (semilla = (semilla * 16807) % 2147483647) / 2147483647 - 0.5;
  const grupos = d.nodos.filter((n) => n.tipo === "grupo").map((n) => n.id);
  const fuentes = d.nodos.filter((n) => n.tipo === "fuente").map((n) => n.id);
  const nuevos = d.nodos.filter((n) => !grafo.pos.has(n.id)).length;
  grafo.nodos = d.nodos.map((n) => ({
    ...n, ...(grafo.pos.get(n.id) || posicionInicial(n, grupos, fuentes, azar)),
    vx: 0, vy: 0, r: RADIO[n.tipo] || 8, fijo: n.tipo === "agente",
  }));
  grafo.porId = new Map(grafo.nodos.map((n) => [n.id, n]));
  grafo.aristas = d.aristas.filter((a) => grafo.porId.has(a.origen) && grafo.porId.has(a.destino))
    .map((a) => ({ ...a, o: grafo.porId.get(a.origen), d: grafo.porId.get(a.destino) }));
  grafo.vecinos = new Map(grafo.nodos.map((n) => [n.id, []]));
  grafo.aristas.forEach((a) => {
    grafo.vecinos.get(a.origen).push({ a, otro: a.d, rel: RELACION[a.tipo][0] });
    grafo.vecinos.get(a.destino).push({ a, otro: a.o, rel: RELACION[a.tipo][1] });
  });
  if (!grafo.porId.has(grafo.seleccion)) grafo.seleccion = null;

  dibujarGrafo();
  if (nuevos) {                       // disposición nueva: se calcula de golpe y se encuadra
    for (let i = 0; i < 400; i++) pasoFuerzas(Math.max(0.03, 1 - i / 400));
    actualizarPosiciones();
    encuadrar();
  } else { actualizarPosiciones(); aplicarVista(); }
  aplicarFiltros();
  marcarUsados();
  pintarResumenGrafo();
  if (grafo.seleccion) seleccionar(grafo.seleccion, false); else $("#grafo-detalle").innerHTML = "";
  $("#grafo-vacio").classList.add("oculto");
}

function visibleNodo(n) { return n.tipo !== "evidencia" || grafo.filtros.evidencia; }
function visibleArista(a) {
  const f = grafo.filtros;
  if (!visibleNodo(a.o) || !visibleNodo(a.d)) return false;
  if (a.tipo === "semejanza") return f.semejanza;
  if (a.tipo === "remite") return f.remite;
  if (ESTRUCTURA.has(a.tipo)) return f.estructura;
  return f.evidencia;
}

function pasoFuerzas(alfa) {
  const ns = grafo.nodos;
  for (let i = 0; i < ns.length; i++) {          // repulsión entre todos los nodos
    for (let j = i + 1; j < ns.length; j++) {
      const a = ns[i], b = ns[j];
      let dx = b.x - a.x, dy = b.y - a.y;
      if (!dx && !dy) { dx = 0.5; dy = 0.3; }
      const d2 = Math.max(dx * dx + dy * dy, 64), d = Math.sqrt(d2);
      const f = (2600 + 120 * (a.r + b.r)) * alfa / d2 / d;
      a.vx -= dx * f; a.vy -= dy * f;
      b.vx += dx * f; b.vy += dy * f;
    }
  }
  for (const a of grafo.aristas) {                // resortes
    const dx = a.d.x - a.o.x, dy = a.d.y - a.o.y, d = Math.sqrt(dx * dx + dy * dy) || 1;
    const fuerza = (FUERZA[a.tipo] ?? 0.06) * (a.tipo === "semejanza" ? (a.similitud || 0.9) : 1);
    const k = (d - (LARGO[a.tipo] || 80)) / d * fuerza * alfa;
    a.o.vx += dx * k; a.o.vy += dy * k; a.d.vx -= dx * k; a.d.vy -= dy * k;
  }
  for (const n of ns) {                           // gravedad al centro y rozamiento
    if (n.fijo) { n.vx = n.vy = 0; continue; }
    n.vx = (n.vx - n.x * 0.003 * alfa) * 0.6;
    n.vy = (n.vy - n.y * 0.003 * alfa) * 0.6;
    n.x += n.vx; n.y += n.vy;
  }
}

function calentar(c = 0.3) {
  grafo.calor = Math.max(grafo.calor, c);
  if (grafo.animando) return;
  grafo.animando = true;
  const cuadro = () => {
    for (let i = 0; i < 2; i++) pasoFuerzas(grafo.calor);
    actualizarPosiciones();
    grafo.calor *= 0.97;
    if (grafo.calor > 0.02) requestAnimationFrame(cuadro); else grafo.animando = false;
  };
  requestAnimationFrame(cuadro);
}

function formaNodo(n) {
  const r = n.r;
  let forma;
  if (n.tipo === "fuente") forma = svgEl("rect", { x: -r, y: -r, width: 2 * r, height: 2 * r, rx: 4 });
  else if (n.tipo === "evidencia") forma = svgEl("rect", { x: -r, y: -r, width: 2 * r, height: 2 * r, rx: 1.5 });
  else if (n.tipo === "grupo") forma = svgEl("rect", { x: -r * 0.8, y: -r * 0.8, width: 1.6 * r, height: 1.6 * r, transform: "rotate(45)" });
  else forma = svgEl("circle", { r });
  let cls = "forma n-" + n.tipo;
  if (n.tipo === "control") cls += " est-" + clase(n.estado);
  if (n.tipo === "evidencia") cls += " int-" + clase(n.integridad);
  forma.setAttribute("class", cls);
  return forma;
}

function dibujarGrafo() {
  const svg = $("#grafo-svg");
  svg.innerHTML = "";
  const capa = svgEl("g", { id: "grafo-capa" });
  const capaAristas = svgEl("g"), capaNodos = svgEl("g");
  for (const a of grafo.aristas) {
    a.el = svgEl("line", { class: "arista a-" + a.tipo });
    if (a.tipo === "semejanza") a.el.style.opacity = Math.min(1, 0.35 + (a.similitud - 0.85) * 8);
    const t = svgEl("title");
    t.textContent = `${a.o.etiqueta} ${RELACION[a.tipo][0]} ${a.d.etiqueta}` + (a.similitud ? ` (coseno ${a.similitud})` : "");
    a.el.appendChild(t);
    capaAristas.appendChild(a.el);
  }
  for (const n of grafo.nodos) {
    n.el = svgEl("g", { class: "nodo t-" + n.tipo, "data-id": n.id });
    n.el.appendChild(svgEl("circle", { class: "halo", r: n.r + 5 }));
    n.el.appendChild(formaNodo(n));
    const texto = svgEl("text", { y: n.r + 12, "text-anchor": "middle" });
    texto.textContent = n.etiqueta.length > 34 ? n.etiqueta.slice(0, 32) + "…" : n.etiqueta;
    n.el.appendChild(texto);
    const t = svgEl("title");
    t.textContent = n.titulo ? `${n.etiqueta} — ${n.titulo}` : n.etiqueta;
    n.el.appendChild(t);
    capaNodos.appendChild(n.el);
  }
  capa.append(capaAristas, capaNodos);
  svg.appendChild(capa);
}

function actualizarPosiciones() {
  for (const a of grafo.aristas) {
    a.el.setAttribute("x1", a.o.x.toFixed(1)); a.el.setAttribute("y1", a.o.y.toFixed(1));
    a.el.setAttribute("x2", a.d.x.toFixed(1)); a.el.setAttribute("y2", a.d.y.toFixed(1));
  }
  for (const n of grafo.nodos) {
    n.el.setAttribute("transform", `translate(${n.x.toFixed(1)},${n.y.toFixed(1)})`);
    grafo.pos.set(n.id, { x: n.x, y: n.y });
  }
}

function aplicarVista() {
  const svg = $("#grafo-svg"), capa = $("#grafo-capa");
  if (!capa) return;
  const v = grafo.vista;
  capa.setAttribute("transform", `translate(${svg.clientWidth / 2 + v.x},${svg.clientHeight / 2 + v.y}) scale(${v.k})`);
}

function encuadrar() {
  const ns = grafo.nodos.filter(visibleNodo);
  const svg = $("#grafo-svg");
  if (!ns.length || !svg.clientWidth) return;
  const xs = ns.map((n) => n.x), ys = ns.map((n) => n.y);
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const k = Math.min(svg.clientWidth / (x1 - x0 + 120), svg.clientHeight / (y1 - y0 + 120), 1.8);
  grafo.vista = { k, x: -((x0 + x1) / 2) * k, y: -((y0 + y1) / 2) * k };
  aplicarVista();
}

function centrarEn(n) {
  grafo.vista.x = -n.x * grafo.vista.k;
  grafo.vista.y = -n.y * grafo.vista.k;
  aplicarVista();
}

function aplicarFiltros() {
  grafo.nodos.forEach((n) => { n.el.style.display = visibleNodo(n) ? "" : "none"; });
  grafo.aristas.forEach((a) => { a.el.style.display = visibleArista(a) ? "" : "none"; });
}

/* Resalta un nodo y sus vecinos visibles; sin id, quita el resalte. */
function enfocar(id) {
  const svg = $("#grafo-svg");
  svg.querySelectorAll(".vecino, .vecina").forEach((e) => e.classList.remove("vecino", "vecina"));
  const n = grafo.porId.get(id);
  svg.classList.toggle("enfocado", !!n);
  if (!n) return;
  n.el.classList.add("vecino");
  for (const { a, otro } of grafo.vecinos.get(id)) {
    if (!visibleArista(a)) continue;
    a.el.classList.add("vecina");
    otro.el.classList.add("vecino");
  }
}

function seleccionar(id, centrar = true) {
  const n = grafo.porId.get(id);
  grafo.seleccion = n ? id : null;
  grafo.nodos.forEach((x) => x.el.classList.toggle("seleccionado", x.id === grafo.seleccion));
  if (n && !visibleNodo(n)) {
    grafo.filtros.evidencia = true;
    $('[data-filtro="evidencia"]').checked = true;
    aplicarFiltros();
  }
  enfocar(grafo.seleccion);
  if (!n) { $("#grafo-detalle").innerHTML = ""; return; }
  if (centrar) centrarEn(n);
  pintarDetalleNodo(n);
}

function pintarDetalleNodo(n) {
  const filas = [], acciones = [];
  const fila = (k, v) => { if (v !== undefined && v !== null && v !== "") filas.push(`<dt>${k}</dt><dd>${v}</dd>`); };
  let titulo = esc(n.etiqueta), texto = "";
  if (n.tipo === "control") {
    titulo = `<span class="ref">${esc(n.etiqueta)}</span> ${esc(n.titulo)}`;
    fila("Estado", `<span class="insignia e-${clase(n.estado)}">${esc(n.estado)}</span>`);
    if (n.nota !== "Se espera: " + n.evidencia_esperada) fila("Observación", esc(n.nota));
    fila("Evidencia esperada", esc(n.evidencia_esperada));
    fila("Mínimo", esc(n.minimo));
    fila("En la norma", n.norma.length ? n.norma.map(esc).join("<br>") : "<small>sin texto en ISOS/texto</small>");
    acciones.push(`<button class="boton mini" data-norma="${esc(n.etiqueta)}">Texto de la norma</button>`);
    acciones.push(`<button class="boton mini secundario" data-preguntar="¿Qué evidencia se espera para ${esc(n.etiqueta)} y cómo está en el expediente?">Preguntar al asistente</button>`);
  } else if (n.tipo === "evidencia") {
    titulo = `<span class="ref">${esc(n.etiqueta)}</span> ${esc(n.titulo)}`;
    fila("Integridad", `<span class="insignia i-${clase(n.integridad)}">${esc(n.integridad)}</span>`);
    fila("Tipo", esc(n.tipo_doc));
    fila("Fecha", esc(n.fecha));
    fila("SHA-256", `<span class="mono" title="${esc(n.sha256)}">${esc(n.sha256.slice(0, 16))}…</span>`);
    acciones.push(`<button class="boton mini" data-evidencia="${esc(n.etiqueta)}">Ver evidencia</button>`);
    acciones.push(`<button class="boton mini secundario" data-preguntar="¿Qué demuestra la evidencia ${esc(n.etiqueta)} y para qué controles sirve?">Preguntar al asistente</button>`);
  } else if (n.tipo === "fuente") {
    texto = n.detalle ? `<p>${esc(n.detalle)}</p>` : "";
    fila("Fragmentos en FAISS", esc(n.fragmentos));
    fila("Archivo", n.archivo ? `<span class="mono">${esc(n.archivo)}</span>` : "");
  } else if (n.tipo === "grupo") {
    const ctl = grafo.vecinos.get(n.id).filter((v) => v.otro.tipo === "control").map((v) => v.otro);
    const cuenta = {};
    ctl.forEach((c) => { cuenta[c.estado] = (cuenta[c.estado] || 0) + 1; });
    fila("Controles", ctl.length);
    fila("Estados", Object.entries(cuenta).map(([e, k]) => `<span class="insignia e-${clase(e)}">${k} ${esc(e)}</span>`).join(" "));
  } else if (n.tipo === "proyecto") {
    texto = n.detalle ? `<p>${esc(n.detalle)}</p>` : "";
    fila("Rol", esc(ROLES[n.rol] || n.rol));
    fila("Cobertura", `${esc(n.cobertura)} %`);
  } else texto = `<p>${esc(n.detalle || "")}</p>`;

  const rels = grafo.vecinos.get(n.id).filter((v) => visibleArista(v.a))
    .sort((x, y) => x.rel.localeCompare(y.rel) || x.otro.etiqueta.localeCompare(y.otro.etiqueta, "es", { numeric: true }));
  const lista = rels.map((v) => `<li><small>${esc(v.rel)}</small> <button data-nodo="${esc(v.otro.id)}">${esc(v.otro.etiqueta)}</button>` +
    `${v.otro.titulo ? ` <small>${esc(v.otro.titulo)}</small>` : ""}${v.a.similitud ? ` <small>(coseno ${v.a.similitud})</small>` : ""}</li>`).join("");
  $("#grafo-detalle").innerHTML = `
    <small>${esc(TIPO_NODO[n.tipo] || n.tipo)}</small>
    <h3>${titulo}</h3>${texto}
    ${filas.length ? `<dl>${filas.join("")}</dl>` : ""}
    ${acciones.length ? `<div class="acciones">${acciones.join("")}</div>` : ""}
    ${rels.length ? `<h3 style="margin-top:12px">Relaciones (${rels.length})</h3><ul class="relaciones">${lista}</ul>` : ""}`;
}

function pintarResumenGrafo() {
  const r = grafo.datos.resumen;
  const cifra = (v, t) => `<div><b>${esc(v)}</b><small>${t}</small></div>`;
  $("#grafo-resumen").innerHTML = `
    <h3>Lo que sabe el agente ahora</h3>
    <p class="nota" style="margin:4px 0 8px">Conocimiento común (norma y skill) más el expediente de <strong>${esc(estado.proyecto.nombre)}</strong>.</p>
    <div class="grafo-cifras">
      ${cifra(r.fragmentos_conocimiento, "fragmentos de conocimiento")}${cifra(r.fragmentos_norma, "de ellos, de ISO 27701")}
      ${cifra(r.controles, "controles del catálogo")}${cifra(r.evidencias, "evidencias del proyecto")}
      ${cifra(r.semejanzas, "relaciones semánticas")}${cifra(r.remisiones, "remisiones de la norma")}
    </div>
    ${r.indexado ? "" : `<p class="aviso-panel" style="margin-top:8px">El índice FAISS aún no está construido (¿Ollama apagado?): faltan las relaciones semánticas.</p>`}`;
  const cuenta = {};
  grafo.nodos.filter((n) => n.tipo === "control").forEach((n) => { cuenta[n.estado] = (cuenta[n.estado] || 0) + 1; });
  $("#grafo-estados").innerHTML = Object.entries(cuenta)
    .map(([e, k]) => `<span class="insignia e-${clase(e)}">${k} ${esc(e)}</span>`).join("");
}

/* Nodos que el asistente recuperó (RAG) para su última respuesta. */
function marcarUsados() {
  const usados = new Set(grafo.usados);
  grafo.nodos.forEach((n) => n.el.classList.toggle("usado", usados.has(n.id)));
  const caja = $("#grafo-usados");
  const nodos = grafo.usados.map((id) => grafo.porId.get(id)).filter(Boolean);
  caja.classList.toggle("oculto", !nodos.length);
  if (!nodos.length) return;
  caja.innerHTML = `<strong>Última respuesta del asistente</strong><br><small>«${esc(grafo.pregunta)}» se respondió con:</small>
    <div class="chips">${nodos.map((n) => `<button class="chip-nodo" data-nodo="${esc(n.id)}">${esc(n.etiqueta)}</button>`).join("")}</div>
    <button class="boton mini fantasma" data-quitar-usados="1">Quitar resaltado</button>`;
}

function errorGrafo(err) {
  $("#grafo-vacio").textContent = err.message;
  $("#grafo-vacio").classList.remove("oculto");
}

(function eventosGrafo() {
  const svg = $("#grafo-svg");
  const aGrafo = (e) => {
    const r = svg.getBoundingClientRect(), v = grafo.vista;
    return { x: (e.clientX - r.left - svg.clientWidth / 2 - v.x) / v.k, y: (e.clientY - r.top - svg.clientHeight / 2 - v.y) / v.k };
  };
  let arrastre = null;
  svg.addEventListener("pointerdown", (e) => {
    const g = e.target.closest(".nodo");
    const n = g && grafo.porId.get(g.dataset.id);
    arrastre = { n, x0: e.clientX, y0: e.clientY, vx: grafo.vista.x, vy: grafo.vista.y, movido: false };
    if (n) n.fijo = true;
    svg.setPointerCapture(e.pointerId);
    svg.classList.add("moviendo");
  });
  svg.addEventListener("pointermove", (e) => {
    if (!arrastre) return;
    if (Math.abs(e.clientX - arrastre.x0) + Math.abs(e.clientY - arrastre.y0) > 4) arrastre.movido = true;
    if (!arrastre.movido) return;
    if (arrastre.n) {
      Object.assign(arrastre.n, aGrafo(e), { vx: 0, vy: 0 });
      actualizarPosiciones();
      calentar(0.25);
    } else {
      grafo.vista.x = arrastre.vx + e.clientX - arrastre.x0;
      grafo.vista.y = arrastre.vy + e.clientY - arrastre.y0;
      aplicarVista();
    }
  });
  const soltar = () => {
    if (!arrastre) return;
    const { n, movido } = arrastre;
    if (n && n.tipo !== "agente") n.fijo = false;
    if (!movido) seleccionar(n ? n.id : null, false);
    arrastre = null;
    svg.classList.remove("moviendo");
  };
  svg.addEventListener("pointerup", soltar);
  svg.addEventListener("pointercancel", soltar);
  svg.addEventListener("wheel", (e) => {
    e.preventDefault();
    const v = grafo.vista, p = aGrafo(e);
    const k = Math.min(4, Math.max(0.2, v.k * Math.exp(-e.deltaY * 0.0015)));
    v.x += p.x * (v.k - k); v.y += p.y * (v.k - k); v.k = k;
    aplicarVista();
  }, { passive: false });
  svg.addEventListener("pointerover", (e) => {
    const g = e.target.closest(".nodo");
    if (g && !arrastre) enfocar(g.dataset.id);
  });
  svg.addEventListener("pointerout", (e) => {
    const g = e.target.closest(".nodo");
    if (g && !arrastre && !g.contains(e.relatedTarget)) enfocar(grafo.seleccion);
  });

  $("#grafo-filtros").addEventListener("change", (e) => {
    const f = e.target.dataset.filtro;
    if (!f) return;
    grafo.filtros[f] = e.target.checked;
    if (!grafo.datos) return;
    aplicarFiltros();
    enfocar(grafo.seleccion);
    if (grafo.seleccion) pintarDetalleNodo(grafo.porId.get(grafo.seleccion));
  });
  $("#grafo-buscar").addEventListener("input", (e) => {
    const q = e.target.value.trim().toLowerCase();
    grafo.nodos.forEach((n) => n.el.classList.toggle("coincide",
      !!q && `${n.etiqueta} ${n.titulo || ""}`.toLowerCase().includes(q)));
  });
  $("#grafo-buscar").addEventListener("keydown", (e) => {
    if (e.key !== "Enter") return;
    const n = grafo.nodos.find((x) => x.el.classList.contains("coincide"));
    if (n) seleccionar(n.id);
  });
  $("#btn-grafo-encuadrar").addEventListener("click", encuadrar);
  $("#btn-grafo-recargar").addEventListener("click", () => cargarGrafo().catch(errorGrafo));
  const acciones = (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    if (b.dataset.nodo) seleccionar(b.dataset.nodo);
    else if (b.dataset.norma) mostrarNorma(b.dataset.norma);
    else if (b.dataset.evidencia) mostrarEvidencia(b.dataset.evidencia);
    else if (b.dataset.preguntar) { irA("asistente"); preguntar(b.dataset.preguntar); }
    else if (b.dataset.quitarUsados) { grafo.usados = []; marcarUsados(); }
  };
  $("#grafo-detalle").addEventListener("click", acciones);
  $("#grafo-usados").addEventListener("click", acciones);
  window.addEventListener("resize", aplicarVista);
})();

/* --------------------------------------------------------------- proyectos */
/* Cada organización auditada es un proyecto con su propio expediente, cobertura,
   revisiones y chat. Al cambiar de proyecto se vacía todo lo del anterior. */
const CLAVE_PROYECTO = "audita-pims.proyecto";
const ROLES = { responsable: "Responsable del tratamiento", encargado: "Encargado del tratamiento", ambos: "Responsable y encargado" };
function recordarProyecto(id) { try { localStorage.setItem(CLAVE_PROYECTO, id); } catch (e) { /* sin almacenamiento */ } }
function proyectoRecordado() { try { return localStorage.getItem(CLAVE_PROYECTO); } catch (e) { return null; } }

function pintarSelectorProyectos() {
  const sel = $("#proyecto");
  sel.innerHTML = estado.proyectos.length
    ? estado.proyectos.map((p) => `<option value="${esc(p.id)}">${esc(p.nombre)}</option>`).join("")
    : `<option value="">— sin proyectos —</option>`;
  if (estado.proyecto) sel.value = estado.proyecto.id;
}

function bienvenidaChat(p) {
  return `<div class="mensaje asistente"><div class="burbuja">Soy <strong>AUDITA-PIMS</strong>. Estoy trabajando con el expediente de
    <strong>${esc(p.nombre)}</strong>${p.descripcion ? ` (${esc(p.descripcion)})` : ""}: solo veo sus evidencias y su cobertura,
    más la norma ISO/IEC 27701:2025 y la base de conocimiento. Para otra organización, cámbiala arriba.</div></div>`;
}

async function cambiarProyecto(id) {
  const p = estado.proyectos.find((x) => x.id === id);
  if (!p || estado.evaluando) { pintarSelectorProyectos(); return; }
  estado.proyecto = { ...p };
  recordarProyecto(id);
  // Nada del proyecto anterior debe quedar a la vista.
  estado.cobertura = null;
  estado.historial = [];
  Object.assign(grafo, { datos: null, seleccion: null, usados: [], pregunta: "" });
  grafo.pos.clear();
  $("#grafo-svg").innerHTML = "";
  ["#grafo-resumen", "#grafo-detalle", "#grafo-estados"].forEach((s) => { $(s).innerHTML = ""; });
  $("#grafo-usados").classList.add("oculto");
  reiniciarRegistro();
  $("#panel-hallazgo").classList.add("oculto");
  $("#mensajes").innerHTML = bienvenidaChat(p);
  $("#tabla-cobertura tbody").innerHTML = "";
  $("#kpis").innerHTML = "";
  $("#resumen-revision").classList.add("oculto");
  $("#filtro-estado").value = "";
  avisoEvaluacion("");
  ["#nota-verificacion", "#nota-registro"].forEach((s) => { $(s).textContent = ""; });
  $("#rol").value = p.rol;
  document.title = `${p.nombre} · AUDITA-PIMS`;
  pintarSelectorProyectos();
  await cargarEstado();
  if ($("#vista-cobertura").classList.contains("activa")) await cargarCobertura();
  if ($("#vista-grafo").classList.contains("activa")) await cargarGrafo().catch(errorGrafo);
}
$("#proyecto").addEventListener("change", (e) => cambiarProyecto(e.target.value).catch(alertaSuave));

async function cargarProyectos() {
  estado.proyectos = await api("/api/proyectos");
  pintarSelectorProyectos();
}

/* Formulario «Nuevo proyecto» en el panel lateral. */
function mostrarNuevoProyecto() {
  $("#panel-cuerpo").dataset.ref = "";
  $("#panel-titulo").textContent = "Nuevo proyecto de auditoría";
  const filas = estado.catalogo.map((c) => `
    <li><label class="excluir"><input type="checkbox" data-excluir="${esc(c.ref)}">
      <span class="ref">${esc(c.ref)}</span> ${esc(c.titulo)}</label>
      <input type="text" class="justificacion oculto" data-justificacion="${esc(c.ref)}" placeholder="Por qué no aplica (obligatorio)"></li>`).join("");
  $("#panel-cuerpo").innerHTML = `
    <form id="form-proyecto" class="form-proyecto">
      <p class="ayuda">Cada proyecto tiene su propio expediente, cadena de custodia, cobertura, revisiones IA y chat.
        Las evidencias de un proyecto nunca se mezclan con las de otro.</p>
      <label>Nombre de la organización<input type="text" id="np-nombre" required placeholder="p. ej. Farmacias Andinas S.A."></label>
      <label>Descripción <small>(sector, alcance; el asistente la usa como contexto)</small>
        <input type="text" id="np-descripcion" placeholder="p. ej. Cadena de farmacias con venta online"></label>
      <label>Rol en el tratamiento de datos personales
        <select id="np-rol">${Object.entries(ROLES).map(([v, t]) => `<option value="${v}">${t}</option>`).join("")}</select></label>
      <details>
        <summary>Controles que no aplican (Declaración de Aplicabilidad) — opcional</summary>
        <p class="ayuda">Marca solo los que la organización excluye con justificación; el resto se audita.</p>
        <ul class="lista-excluir">${filas}</ul>
      </details>
      <p class="aviso-panel oculto" id="np-error"></p>
      <div class="acciones">
        <button class="boton" type="submit">Crear proyecto</button>
        <button class="boton fantasma" type="button" id="np-cancelar">Cancelar</button>
      </div>
    </form>`;
  $("#panel-hallazgo").classList.remove("oculto");
  $("#np-nombre").focus();
}
$("#btn-nuevo-proyecto").addEventListener("click", mostrarNuevoProyecto);
$("#panel-cuerpo").addEventListener("change", (e) => {
  const ref = e.target.dataset.excluir;
  if (ref) $(`[data-justificacion="${CSS.escape(ref)}"]`).classList.toggle("oculto", !e.target.checked);
});
$("#panel-cuerpo").addEventListener("click", (e) => {
  if (e.target.id === "np-cancelar") $("#panel-hallazgo").classList.add("oculto");
});
$("#panel-cuerpo").addEventListener("submit", async (e) => {
  if (e.target.id !== "form-proyecto") return;
  e.preventDefault();
  const excluidos = [...document.querySelectorAll("[data-excluir]:checked")].map((c) => ({
    ref: c.dataset.excluir,
    justificacion: $(`[data-justificacion="${CSS.escape(c.dataset.excluir)}"]`).value.trim(),
  }));
  const boton = e.target.querySelector("button[type=submit]");
  boton.disabled = true;
  try {
    const p = await api("/api/proyectos", json({
      nombre: $("#np-nombre").value, descripcion: $("#np-descripcion").value, rol: $("#np-rol").value, excluidos,
    }));
    await cargarProyectos();
    await cambiarProyecto(p.id);
    irA("expediente");
    $("#nota-registro").textContent = `Proyecto «${p.nombre}» creado. Registra aquí su primera evidencia.`;
  } catch (err) {
    $("#np-error").textContent = err.message;
    $("#np-error").classList.remove("oculto");
    boton.disabled = false;
  }
});

/* ----------------------------------------------------------------- inicio */
(async function iniciar() {
  $("#fecha-corte").value = hoy();
  try {
    estado.catalogo = await api("/api/catalogo");
    const sel = $("#agregar-control");
    estado.catalogo.forEach((c) => sel.add(new Option(`${c.ref} — ${c.titulo}`, c.ref)));
    await cargarProyectos();
    if (!estado.proyectos.length) { mostrarNuevoProyecto(); return; }
    const recordado = proyectoRecordado();
    await cambiarProyecto(estado.proyectos.some((p) => p.id === recordado) ? recordado : estado.proyectos[0].id);
  } catch (err) { $("#p-modelo").textContent = err.message; }
})();
