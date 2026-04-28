import json
import os

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ... import crud, schemas
from ...database import SessionLocal

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _require_admin(db: Session, x_user_id: int | None):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")
    user = crud.get_usuario(db, usuario_id=x_user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    if user.tipousuario != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    return user


def _to_schema(cfg, is_admin: bool) -> schemas.AppConfig:
    try:
        statuses = json.loads(cfg.trip_edit_blocked_statuses or "[]")
        if not isinstance(statuses, list):
            statuses = []
    except json.JSONDecodeError:
        statuses = []
    try:
        expense_desc = json.loads(getattr(cfg, "expense_description_options", None) or "[]")
        if not isinstance(expense_desc, list):
            expense_desc = []
    except json.JSONDecodeError:
        expense_desc = []
    try:
        act_statuses = json.loads(getattr(cfg, "activity_edit_delete_allowed_statuses", None) or "[]")
        if not isinstance(act_statuses, list):
            act_statuses = []
    except json.JSONDecodeError:
        act_statuses = []
    try:
        mutation_statuses = json.loads(cfg.trip_activity_expense_allowed_statuses or "[]")
        if not isinstance(mutation_statuses, list):
            mutation_statuses = []
    except json.JSONDecodeError:
        mutation_statuses = []
    env_anthropic = os.getenv("ANTHROPIC_API_KEY")
    env_gemini = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    anth_last4 = getattr(cfg, "anthropic_api_key_last4", None) or (str(env_anthropic)[-4:] if env_anthropic else None)
    gem_last4 = getattr(cfg, "gemini_api_key_last4", None) or (str(env_gemini)[-4:] if env_gemini else None)
    anth_configured = bool(getattr(cfg, "anthropic_api_key_enc", None) or env_anthropic)
    gem_configured = bool(getattr(cfg, "gemini_api_key_enc", None) or env_gemini)

    return schemas.AppConfig(
        expense_photo_required=bool(cfg.expense_photo_required),
        report_include_receipts=bool(getattr(cfg, "report_include_receipts", True)),
        expense_description_options=[str(s) for s in expense_desc],
        activity_edit_delete_allowed_statuses=[str(s) for s in act_statuses],
        ia_provider=str(getattr(cfg, "ia_provider", "anthropic") or "anthropic"),
        ia_model_anthropic=str(getattr(cfg, "ia_model_anthropic", None) or (os.getenv("IA_MODELO_VISAO") or "claude-sonnet-4-6")),
        ia_model_gemini=str(getattr(cfg, "ia_model_gemini", None) or (os.getenv("IA_MODELO_VISAO_GEMINI") or "gemini-2.5-flash")),
        anthropic_api_key_configured=anth_configured,
        anthropic_api_key_masked=(f"****{anth_last4}" if is_admin and anth_last4 else None),
        gemini_api_key_configured=gem_configured,
        gemini_api_key_masked=(f"****{gem_last4}" if is_admin and gem_last4 else None),
        trip_edit_blocked_statuses=[str(s) for s in statuses],
        trip_activity_expense_allowed_statuses=[str(s) for s in mutation_statuses],
        trips_show_all_admin=bool(getattr(cfg, "trips_show_all_admin", True)),
        trips_show_all_colaborador=bool(getattr(cfg, "trips_show_all_colaborador", True)),
    )


@router.get("/", response_model=schemas.AppConfig)
def read_config(x_user_id: int | None = Header(default=None), db: Session = Depends(get_db)):
    cfg = crud.get_app_config(db)
    user = crud.get_usuario(db, usuario_id=x_user_id) if x_user_id else None
    is_admin = bool(user and getattr(user, "tipousuario", None) == "admin")
    return _to_schema(cfg, is_admin=is_admin)


@router.put("/", response_model=schemas.AppConfig)
def update_config(
    payload: schemas.AppConfigUpdate,
    x_user_id: int | None = Header(default=None),
    db: Session = Depends(get_db),
):
    _require_admin(db, x_user_id)
    if payload.ia_provider is not None:
        val = str(payload.ia_provider or "").lower().strip()
        if val not in {"anthropic", "gemini"}:
            raise HTTPException(status_code=400, detail="Provedor de IA inválido")
        payload.ia_provider = val
    if payload.ia_model_anthropic is not None:
        payload.ia_model_anthropic = str(payload.ia_model_anthropic or "").strip() or None
    if payload.ia_model_gemini is not None:
        payload.ia_model_gemini = str(payload.ia_model_gemini or "").strip() or None
    if payload.anthropic_api_key is not None:
        payload.anthropic_api_key = str(payload.anthropic_api_key or "").strip()
    if payload.gemini_api_key is not None:
        payload.gemini_api_key = str(payload.gemini_api_key or "").strip()
    try:
        cfg = crud.update_app_config(db, payload)
    except ValueError as err:
        raise HTTPException(status_code=503, detail=str(err))
    return _to_schema(cfg, is_admin=True)


class IATestRequest(BaseModel):
    provider: str | None = None
    api_key: str | None = None
    model: str | None = None


@router.post("/test-ia")
def test_ia(payload: IATestRequest | None = None, x_user_id: int | None = Header(default=None), db: Session = Depends(get_db)):
    _require_admin(db, x_user_id)
    cfg = crud.get_app_config(db)
    try:
        from ...ia.vision import test_conexao_ia
        from ...ia.client import decrypt_secret

        if payload and payload.api_key:
            provider = str(payload.provider or "").lower().strip()
            if provider not in {"anthropic", "gemini"}:
                provider = "gemini"
            model = str(payload.model or "").strip() or None
            api_key = str(payload.api_key or "").strip()
            ok, detail = test_conexao_ia(provider=provider, api_key=api_key, model=model)
            safe_detail = str(detail or "").strip() or ("Conexão OK" if ok else "Falha ao testar conexão")
            return {"ok": ok, "provider": provider, "detail": safe_detail}

        pref = str(getattr(cfg, "ia_provider", "gemini") or "gemini").lower()
        if pref not in {"anthropic", "gemini"}:
            pref = "gemini"

        anth_token = getattr(cfg, "anthropic_api_key_enc", None)
        gem_token = getattr(cfg, "gemini_api_key_enc", None)
        env_anth = os.getenv("ANTHROPIC_API_KEY")
        env_gem = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

        anth_available = bool(anth_token or env_anth)
        gem_available = bool(gem_token or env_gem)

        providers: list[str] = []
        if anth_available and gem_available:
            providers = [pref, "anthropic" if pref == "gemini" else "gemini"]
        elif gem_available:
            providers = ["gemini"]
        elif anth_available:
            providers = ["anthropic"]
        else:
            return {"ok": False, "provider": None, "detail": "Nenhuma chave configurada"}

        last_detail: str | None = None
        for provider in providers:
            model = (
                str(getattr(cfg, "ia_model_gemini", None) or (os.getenv("IA_MODELO_VISAO_GEMINI") or "gemini-2.5-flash"))
                if provider == "gemini"
                else str(getattr(cfg, "ia_model_anthropic", None) or (os.getenv("IA_MODELO_VISAO") or "claude-sonnet-4-6"))
            )
            token = gem_token if provider == "gemini" else anth_token
            api_key = None
            if token:
                api_key = decrypt_secret(token)
            ok, detail = test_conexao_ia(provider=provider, api_key=api_key, model=model)
            if ok:
                return {"ok": True, "provider": provider, "detail": detail}
            last_detail = str(detail or "").strip() or last_detail

        return {
            "ok": False,
            "provider": providers[-1] if providers else None,
            "detail": last_detail or "Falha ao testar conexão",
        }
    except ValueError as err:
        return {"ok": False, "provider": None, "detail": str(err)}
    except Exception as err:
        msg = str(err or "").strip()
        if not msg:
            msg = f"Erro ao testar IA ({type(err).__name__})"
        return {"ok": False, "provider": None, "detail": msg[:400]}
