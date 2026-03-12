from fastapi import FastAPI, Request, Response, HTTPException, Cookie, Depends, status
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Annotated

import time
import logging

app = FastAPI()
templates = Jinja2Templates(directory="../templates")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API")

class Usuario(BaseModel):
    nome: str
    bio: str
    senha: str

class LoginData(BaseModel):
    nome: str
    senha:str

usuarios_db = []


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    # 1. Código executado ANTES da rota
    start_time = time.perf_counter()
    
    # 2. A requisição viaja até a rota e volta como resposta
    response = await call_next(request)
    
    # 3. Código executado DEPOIS da rota
    process_time = time.perf_counter() - start_time
    
    # Adicionamos um header customizado na resposta para o cliente ver
    response.headers["X-Process-Time"] = str(process_time)
    
    logger.info(f"Rota: {request.url.path} | Tempo: {process_time:.4f}s")
    
    return response

@app.post("/usuario")
def createUsuario(u: Usuario, response: Response):
    usuarios_db.append(u)

    return {"message": "Criado com sucesso"}

@app.post("/login")
def login(data: LoginData, response: Response):
    usuario_encontrado = None
    for u in usuarios_db:
        if u.nome == data.nome:
            usuario_encontrado = u
            break
    
    if not usuario_encontrado:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    if usuario_encontrado.senha == data.senha:
        response.set_cookie(key="session_user", value=data.nome)
        return {"message": "Logado com sucesso"}
    
    return HTTPException(status_code=401, detail="Senha incorreta")

def get_active_user(session_user: Annotated[str | None, Cookie()] = None):
    if not session_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acesso negado: você não está logado"
        )
    
    user = next((u for u in usuarios_db if u.nome == session_user), None)
    if not user:
        raise HTTPException(status_code=401, detail="Sessão Inválida")
    
    return user

@app.get("/profile")
def show_profile(request: Request, user: dict = Depends(get_active_user)):
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={"username": user.nome, "bio": user.bio}
    )

@app.get("/")
def root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

@app.get("/login")
def loginPage(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )