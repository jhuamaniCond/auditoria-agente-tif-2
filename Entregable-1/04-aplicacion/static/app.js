/* AUDITA-PIMS - interfaz en JavaScript puro (sin frameworks). */
"use strict";

const $ = (sel) => document.querySelector(sel);
const estado = { catalogo: [], cobertura: null, historial: [], subida: null, controles: [] };
const ORDEN = ["Cubierto", "Parcial", "Desactualizada", "Comprometida", "Sin evidencia", "No aplica"];

function clase(texto) {
  return texto.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/\s+/g, "-");
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
document.querySelectorAll(".pestana").forEach((b) => b.addEventListener("click", () => {
  document.querySelectorAll(".pestana").forEach((x) => x.classList.toggle("activa", x === b));
  document.querySelectorAll(".vista").forEach((v) => v.classList.toggle("activa", v.id === "vista-" + b.dataset.vista));
  if (b.dataset.vista === "cobertura" && !estado.cobertura) cargarCobertura();
}));

/* ------------------------------------------------------------------ estado */
async function cargarEstado() {
  const d = await api("/api/estado");
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
      <td class="ref">${esc(ev.id)}</td>
      <td>${esc(ev.titulo)}<br><small>${esc(ev.tipo)} · ${esc(ev.fuente || "sin fuente")}</small></td>
      <td class="mono">${ev.controles.map(esc).join(", ")}</td>
      <td class="mono sin-corte">${esc(ev.fecha_documento)}</td>
      <td class="mono" title="${esc(ev.sha256)}">${esc(ev.sha256.slice(0, 12))}…</td>
      <td><span class="insignia i-${clase(ev.integridad)}">${esc(ev.integridad)}</span></td>
    </tr>`).join("") : `<tr><td colspan="6" class="nota">El expediente está vacío. Registra la primera evidencia.</td></tr>`;
}

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
  const c = await api("/api/cobertura?" + new URLSearchParams(parametros()));
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
  if (filtro.options.length === 1) ORDEN.forEach((e) => filtro.add(new Option(e, e)));
  pintarCobertura();
}
function pintarCobertura() {
  const f = $("#filtro-estado").value;
  const filas = estado.cobertura.controles.filter((x) => !f || x.estado === f);
  $("#tabla-cobertura tbody").innerHTML = filas.map((x) => `
    <tr>
      <td><button class="ref enlace-norma" data-norma="${esc(x.ref)}" title="Ver el texto de ISO/IEC 27701:2025">${esc(x.ref)}</button></td>
      <td>${esc(x.titulo)}</td>
      <td><span class="insignia e-${clase(x.estado)}">${esc(x.estado)}</span></td>
      <td class="mono">${x.evidencias.map(esc).join(", ") || "—"}</td>
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
      <li><span class="ref">${esc(c.evidencia)}</span> «${esc(c.texto)}»
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

$("#btn-evaluar-todos").addEventListener("click", async (e) => {
  if (!estado.cobertura) await cargarCobertura();
  const pendientes = estado.cobertura.controles.filter((x) => evaluable(x) && !(x.revision && x.revision.vigente));
  const nota = $("#nota-evaluacion");
  if (!pendientes.length) { nota.textContent = "Todos los controles con evidencia válida ya tienen revisión IA."; return; }
  e.target.disabled = true;
  let hechos = 0;
  for (const x of pendientes) {
    nota.textContent = `Evaluando ${x.ref} (${hechos + 1} de ${pendientes.length}) con el modelo local…`;
    try { await evaluar(x.ref); hechos++; }
    catch (err) { nota.textContent = `${x.ref}: ${err.message}`; break; }
    await cargarCobertura();
  }
  if (hechos === pendientes.length) nota.textContent = `${hechos} propuestas listas. Ábrelas en la columna «Revisión IA» para aceptarlas o rechazarlas.`;
  e.target.disabled = false;
});

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
  try {
    const r = await api("/api/chat", json({ mensaje: texto, historial: estado.historial, ...parametros() }));
    const fuentes = [...new Set(r.fuentes.map((f) => f.fuente))].map((f) => `<span>${esc(f)}</span>`).join("");
    espera.querySelector(".burbuja").innerHTML = md(r.respuesta) + `<div class="fuentes">Fuentes recuperadas: ${fuentes}</div>`;
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
$("#sugeridas").addEventListener("click", (e) => { if (e.target.tagName === "BUTTON") preguntar(e.target.textContent); });

/* ----------------------------------------------------------------- inicio */
(async function iniciar() {
  $("#fecha-corte").value = hoy();
  try {
    estado.catalogo = await api("/api/catalogo");
    const sel = $("#agregar-control");
    estado.catalogo.forEach((c) => sel.add(new Option(`${c.ref} — ${c.titulo}`, c.ref)));
    await cargarEstado();
  } catch (err) { $("#p-modelo").textContent = err.message; }
})();
