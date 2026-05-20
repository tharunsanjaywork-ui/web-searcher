"""
SearchMind — FastAPI Application
Serves frontend, auth routes, and API routes for the agent pipeline.
"""

import os
import uuid
import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Startup Diagnostics ---
print("=================== SEARCHMIND STARTUP DIAGNOSTICS ===================")
secret_key = os.getenv("SECRET_KEY", "")
print(f"SECRET_KEY status: {'CONFIGURED' if secret_key else 'MISSING'}, length: {len(secret_key)}")

firebase_json = os.getenv("FIREBASE_CREDENTIALS_JSON", "")
print(f"FIREBASE_CREDENTIALS_JSON status: {'CONFIGURED' if firebase_json else 'MISSING'}, length: {len(firebase_json)}")

tavily_key = os.getenv("TAVILY_API_KEY", "")
print(f"TAVILY_API_KEY status: {'CONFIGURED' if tavily_key else 'MISSING'}")

nvidia_key = os.getenv("NVIDIA_API_KEY", "")
print(f"NVIDIA_API_KEY status: {'CONFIGURED' if nvidia_key else 'MISSING'}")
print("======================================================================")

try:
    from memory import initialize_firebase
    initialize_firebase()
except Exception as startup_err:
    print("=================== STARTUP CRITICAL ERROR ===================")
    print(f"Firebase initialization failed: {startup_err}")
    import traceback
    traceback.print_exc()
    print("===============================================================")
    raise startup_err

app = FastAPI(title="SearchMind", version="1.0.0")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


app.add_middleware(SecurityHeadersMiddleware)
app.mount("/static", StaticFiles(directory="static"), name="static")


def success_response(data):
    return {"success": True, "data": data}


def error_response(message, status_code=500):
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "error": message}
    )


def _get_user_id(request_obj):
    """Extract user_id from Authorization header JWT token."""
    try:
        from auth import verify_token
        auth_header = request_obj.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None
        token = auth_header[len("Bearer "):]
        payload = verify_token(token)
        if not payload:
            return None
        return payload.get("user_id")
    except Exception:
        return None


# --- Page Routes ---

@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")


# --- Auth Routes ---

@app.post("/api/register")
@limiter.limit("3/minute")
async def register_route(request: Request):
    try:
        body = await request.json()
        email = body.get("email", "").strip()
        password = body.get("password", "")

        if not email or not password:
            return error_response("Email and password required", 400)

        from auth import register
        data, err = register(email, password)
        if err:
            return error_response(err, 400)
        return success_response(data)
    except Exception as e:
        logger.error(f"Register error: {e}")
        return error_response(str(e))


@app.post("/api/login")
@limiter.limit("5/minute")
async def login_route(request: Request):
    try:
        body = await request.json()
        email = body.get("email", "").strip()
        password = body.get("password", "")

        if not email or not password:
            return error_response("Email and password required", 400)

        from auth import login
        data, err = login(email, password)
        if err:
            return error_response(err, 401)
        return success_response(data)
    except Exception as e:
        logger.error(f"Login error: {e}")
        return error_response(str(e))


@app.get("/api/verify")
async def verify_route(request: Request):
    user_id = _get_user_id(request)
    if not user_id:
        return error_response("Invalid or expired token", 401)
    return success_response({"user_id": user_id})


# --- Chat Routes ---

@app.post("/api/chat")
@limiter.limit("20/minute")
async def chat(request: Request):
    try:
        user_id = _get_user_id(request)
        if not user_id:
            return error_response("Authentication required", 401)

        body = await request.json()
        message = body.get("message", "").strip()
        session_id = body.get("session_id", "").strip()

        if not message:
            return error_response("Message is required", 400)
        if len(message) > 2000:
            return error_response("Message too long. Maximum 2000 characters.", 400)
        if not session_id:
            return error_response("session_id is required", 400)

        from agents import run_pipeline
        result = await run_pipeline(message, session_id, user_id)
        return success_response(result)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return error_response(_friendly_error(str(e)), 503)


def _friendly_error(raw_error):
    """Convert raw error strings into user-friendly messages."""
    err = raw_error.lower()

    if "resource_exhausted" in err or "quota" in err or "rate" in err:
        return "⏳ API limit reached. Our servers are experiencing high demand. Please try again in a minute."

    if "unavailable" in err or "503" in err:
        return "🔧 Our servers are temporarily down. Please try again shortly."

    if "invalid_api_key" in err or "401" in err or "permission" in err:
        return "🔑 Service configuration error. Please contact the administrator."

    if "web search" in err:
        return "🌐 Web search is temporarily unavailable. Please try again in a moment."

    if "timeout" in err or "timed out" in err:
        return "⏱️ Request timed out. Please try again with a shorter query."

    return "⚠️ Something went wrong. Please try again later."


@app.get("/api/history")
async def get_history(request: Request):
    try:
        user_id = _get_user_id(request)
        if not user_id:
            return error_response("Authentication required", 401)

        from memory import get_all_sessions
        sessions = get_all_sessions(user_id)
        return success_response(sessions)
    except Exception as e:
        logger.error(f"History error: {e}")
        return error_response(str(e))


@app.get("/api/history/{session_id}")
async def get_session_history_route(session_id: str, request: Request):
    try:
        user_id = _get_user_id(request)
        if not user_id:
            return error_response("Authentication required", 401)

        from memory import get_session_history
        messages = get_session_history(session_id, user_id)
        return success_response(messages)
    except Exception as e:
        logger.error(f"Session history error: {e}")
        return error_response(str(e))


@app.post("/api/new-session")
async def new_session(request: Request):
    try:
        user_id = _get_user_id(request)
        if not user_id:
            return error_response("Authentication required", 401)

        session_id = str(uuid.uuid4())
        return success_response({"session_id": session_id})
    except Exception as e:
        logger.error(f"New session error: {e}")
        return error_response(str(e))
