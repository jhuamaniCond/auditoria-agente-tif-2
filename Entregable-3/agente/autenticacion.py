# -*- coding: utf-8 -*-
"""
Login del panel del agente (Entregable 2).

Protege TODAS las rutas de la app (panel /agente, su API /api/... y la app del
Entregable 1) con usuario y contrasena. Las credenciales no estan en el codigo:

    AGENTE_USUARIO      usuario (por defecto: admin)
    AGENTE_CLAVE_HASH   hash de la contrasena (werkzeug.security.generate_password_hash)
    AGENTE_CLAVE        alternativa en texto plano (solo para pruebas locales)
    AGENTE_SECRETO      clave para firmar la cookie de sesion (si falta, se genera
                        una al arrancar y las sesiones se pierden al reiniciar)
    AGENTE_LOGIN=0      desactiva el login (solo uso local en 127.0.0.1)
    AGENTE_COOKIE_SEGURA=1  la cookie solo viaja por HTTPS (detras de Caddy)

Generar el hash:
    python -c "from werkzeug.security import generate_password_hash as g; print(g('LA_CLAVE'))"
"""

import hmac
import os
import secrets
import threading
import time
from datetime import timedelta
from urllib.parse import urlparse

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash

AQUI = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(AQUI, "web")

USUARIO = os.environ.get("AGENTE_USUARIO", "admin").strip() or "admin"
CLAVE_HASH = os.environ.get("AGENTE_CLAVE_HASH", "").strip()
CLAVE_PLANA = os.environ.get("AGENTE_CLAVE", "")
ACTIVO = os.environ.get("AGENTE_LOGIN", "1").strip() != "0"

# Rutas que se pueden pedir sin sesion
LIBRES = {"/login", "/logout"}
PREFIJOS_LIBRES = ("/agente/static/login",)

# Freno a la fuerza bruta: 5 fallos por IP -> espera de 5 minutos
MAX_FALLOS = 5
BLOQUEO_S = 300
_fallos = {}
_candado = threading.Lock()

bp = Blueprint("autenticacion", __name__, template_folder=WEB)


def _clave_valida(clave):
    if CLAVE_HASH:
        return check_password_hash(CLAVE_HASH, clave)
    if CLAVE_PLANA:
        return hmac.compare_digest(CLAVE_PLANA.encode(), clave.encode())
    return False


def _bloqueada(ip):
    with _candado:
        n, desde = _fallos.get(ip, (0, 0.0))
        if n >= MAX_FALLOS and time.time() - desde < BLOQUEO_S:
            return int(BLOQUEO_S - (time.time() - desde))
        if n >= MAX_FALLOS:
            _fallos.pop(ip, None)
    return 0


def _anotar_fallo(ip):
    with _candado:
        n, desde = _fallos.get(ip, (0, time.time()))
        _fallos[ip] = (n + 1, time.time() if n + 1 >= MAX_FALLOS else desde)


def _destino_seguro(destino):
    """Solo redirige a rutas internas (evita redirecciones abiertas)."""
    if not destino:
        return "/agente"
    p = urlparse(destino)
    if p.scheme or p.netloc or not destino.startswith("/") or destino.startswith("//"):
        return "/agente"
    return destino


@bp.route("/login", methods=["GET", "POST"])
def login():
    if not ACTIVO:
        return redirect("/agente")
    error = None
    destino = _destino_seguro(request.values.get("siguiente"))
    if request.method == "POST":
        ip = request.remote_addr or "?"
        espera = _bloqueada(ip)
        if espera:
            error = "Demasiados intentos fallidos. Espera %d minuto(s)." % max(1, round(espera / 60))
        else:
            usuario = (request.form.get("usuario") or "").strip()
            clave = request.form.get("clave") or ""
            ok_usuario = hmac.compare_digest(usuario.encode(), USUARIO.encode())
            if ok_usuario and _clave_valida(clave):
                with _candado:
                    _fallos.pop(ip, None)
                session.clear()
                session.permanent = True
                session["usuario"] = USUARIO
                return redirect(destino)
            _anotar_fallo(ip)
            error = "Usuario o contraseña incorrectos."
    elif session.get("usuario"):
        return redirect(destino)
    return render_template("login.html", error=error, siguiente=destino), (401 if error else 200)


@bp.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect("/login")


@bp.route("/api/sesion")
def api_sesion():
    return jsonify({"login": ACTIVO, "usuario": session.get("usuario")})


@bp.before_app_request
def _exigir_sesion():
    if not ACTIVO or session.get("usuario"):
        return None
    ruta = request.path
    if ruta in LIBRES or ruta.startswith(PREFIJOS_LIBRES) or ruta == "/agente/static/agente.css":
        return None
    if ruta.startswith("/api/"):
        return jsonify({"error": "Sesion expirada: vuelve a iniciar sesion", "login": True}), 401
    siguiente = request.full_path.rstrip("?") if request.query_string else ruta
    return redirect(url_for("autenticacion.login", siguiente=siguiente))


def instalar(app):
    """Registra el login sobre la app Flask. Debe llamarse antes que los demas blueprints."""
    if ACTIVO and not (CLAVE_HASH or CLAVE_PLANA):
        raise SystemExit("Login activo pero sin contrasena: define AGENTE_CLAVE_HASH "
                         "(o AGENTE_LOGIN=0 para uso local sin login).")
    app.secret_key = os.environ.get("AGENTE_SECRETO") or secrets.token_hex(32)
    app.config.update(
        SESSION_COOKIE_NAME="agente_sesion",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("AGENTE_COOKIE_SEGURA", "0") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
    )
    if os.environ.get("AGENTE_DETRAS_DE_PROXY", "0") == "1":
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    app.register_blueprint(bp)
    if not ACTIVO:
        print("AVISO: login desactivado (AGENTE_LOGIN=0). Usar solo en 127.0.0.1.")
