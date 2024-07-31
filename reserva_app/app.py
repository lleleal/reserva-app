from flask import Flask, redirect, render_template, request, url_for
import uuid, base64, hashlib, datetime

app = Flask(__name__)

# Cadastrar e validar usuario
def cadastrar_usuario(u):
    password = u['password'].encode('utf-8')
    salt = uuid.uuid4().hex.encode('utf-8')
    hashed_password = hashlib.sha512(password + salt).hexdigest()

    linha = f"\n{u['nome']},{u['email']},{hashed_password},{salt.decode('utf-8')}"
    with open("usuarios.csv", "a") as file:
        file.write(linha)

def validar_usuario(email, password):
    password = password.encode('utf-8')
    with open("usuarios.csv", "r") as file:
        linhas = file.readlines()
        for linha in linhas:
            nome, user_email, user_password, salt = linha.strip().split(",")
            salt = salt.encode('utf-8')
            hashed_password = hashlib.sha512(password + salt).hexdigest()
            if email == user_email and hashed_password == user_password:
                return True
    return False

@app.route("/", methods=["GET", "POST"])
def mensagem_erro():
    error_message = None
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if validar_usuario(email, password):
            return redirect(url_for("reservas"))
        else:
            error_message = "E-mail ou senha incorretos. Tente novamente."
    return render_template("login.html", error_message=error_message)

# Cadastrar e carregar salas
def cadastrar_sala(s):
    sala_id = str(uuid.uuid4())
    linha = f"\n{sala_id},{s['tipo']},{s['capacidade']},{s['descricao']},Sim"
    with open("salas.csv", "a") as file:
        file.write(linha)

def carregar_salas():
    salas = []
    with open("salas.csv", "r") as file:
        for linha in file:
            sala_id, tipo, capacidade, descricao, ativa = linha.strip().split(",")
            sala = {
                "id": sala_id,
                "tipo": tipo,
                "capacidade": capacidade,
                "descricao": descricao,
                "ativa": ativa
            }
            salas.append(sala)
    return salas

# Rotas
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if validar_usuario(email, password):
            return redirect(url_for("reservas"))
        else:
            return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/cadastro", methods=["GET", "POST"])
def cadastrar():
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        password = request.form.get("password")
        cadastrar_usuario({"nome": nome, "email": email, "password": password})
        return redirect(url_for("index"))
    return render_template("cadastro.html")

@app.route("/gerenciar/lista-salas")
def lista_salas():
    salas = carregar_salas()
    return render_template("listar-salas.html", salas=salas)

# Cadastrar salas
@app.route("/gerenciar/cadastrar-salas", methods=["GET", "POST"])
def cadastrar_salas():
    if request.method == "POST":
        tipo = request.form.get("tipo")
        capacidade = request.form.get("capacidade")
        descricao = request.form.get("descricao")
        sala_id = request.form.get("sala_id")
        
        if sala_id:
            salas = carregar_salas()
            for sala in salas:
                if sala["id"] == sala_id:
                    sala["tipo"] = tipo
                    sala["capacidade"] = capacidade
                    sala["descricao"] = descricao
            
            with open("salas.csv", "w") as file:
                for sala in salas:
                    linha = f"{sala['id']},{sala['tipo']},{sala['capacidade']},{sala['descricao']},{sala['ativa']}\n"
                    file.write(linha)
        else:
            cadastrar_sala({"tipo": tipo, "capacidade": capacidade, "descricao": descricao})
        
        return redirect(url_for("lista_salas"))
    
    return render_template("cadastrar-sala.html")


# Excluir salas
@app.route("/gerenciar/excluir-sala/<sala_id>", methods=["POST"])
def excluir_sala(sala_id):
    salas = carregar_salas()
    salas = [sala for sala in salas if sala["id"] != sala_id]
    
    with open("salas.csv", "w") as file:
        for sala in salas:
            linha = f"{sala['id']},{sala['tipo']},{sala['capacidade']},{sala['descricao']}\n"
            file.write(linha)
    
    return redirect(url_for("lista_salas"))

# Desativar salas
@app.route("/gerenciar/desativar-sala/<sala_id>", methods=["POST"])
def desativar_sala(sala_id):
    salas = carregar_salas()
    for sala in salas:
        if sala["id"] == sala_id:
            sala["ativa"] = "Não" if sala["ativa"] == "Sim" else "Sim"
    
    with open("salas.csv", "w") as file:
        for sala in salas:
            linha = f"{sala['id']},{sala['tipo']},{sala['capacidade']},{sala['descricao']},{sala['ativa']}\n"
            file.write(linha)
    
    return redirect(url_for("lista_salas"))

# Editar Sala
@app.route("/gerencia/editar-sala/<sala_id>", methods=["GET", "POST"])
def editar_sala(sala_id):
    if request.method == "POST":
        tipo = request.form.get("tipo")
        capacidade = request.form.get("capacidade")
        descricao = request.form.get("descricao")
        
        salas = carregar_salas()
        for sala in salas:
            if sala["id"] == sala_id:
                sala["tipo"] = tipo
                sala["capacidade"] = capacidade
                sala["descricao"] = descricao
        
        with open("salas.csv", "w") as file:
            for sala in salas:
                linha = f"{sala['id']},{sala['tipo']},{sala['capacidade']},{sala['descricao']},{sala['ativa']}\n"
                file.write(linha)
        
        return redirect(url_for("lista_salas"))
    
    salas = carregar_salas()
    sala = next((s for s in salas if s["id"] == sala_id), None)
    
    return render_template("cadastrar-sala.html", sala=sala, editar=True)

# Reservas
@app.route("/reservas")
def reservas():
    return render_template("reservas.html")

def carregar_reservas():
    reservas = []
    with open("reservas.csv", "r") as file:
        for linha in file:
            sala_id, inicio, fim = linha.strip().split(",")
            reservas.append({
                "sala_id": sala_id,
                "inicio": datetime.datetime.fromisoformat(inicio),
                "fim": datetime.datetime.fromisoformat(fim)
            })
    return reservas

def salvar_reserva(sala_id, inicio, fim):
    linha = f"{sala_id},{inicio},{fim}\n"
    with open("reservas.csv", "a") as file:
        file.write(linha)

def verificar_conflito(sala_id, inicio, fim):
    reservas = carregar_reservas()
    for reserva in reservas:
        if reserva["sala_id"] == sala_id:
            if not (fim <= reserva["inicio"] or inicio >= reserva["fim"]):
                return True
    return False

@app.route("/detalhe-reserva")
def detalhe_reserva():
    sala_id = request.args.get("sala_id")
    inicio = request.args.get("inicio")
    fim = request.args.get("fim")

    salas = carregar_salas()
    sala = next((s for s in salas if s["id"] == sala_id), None)

    return render_template("reserva/detalhe-reserva.html", sala=sala, inicio=inicio, fim=fim)


@app.route("/reservar", methods=["GET", "POST"])
def reservar_sala():
    salas = carregar_salas()
    if request.method == "POST":
        sala_id = request.form.get("sala")
        inicio = request.form.get("inicio")
        fim = request.form.get("fim")
        inicio_dt = datetime.datetime.fromisoformat(inicio)
        fim_dt = datetime.datetime.fromisoformat(fim)

        if verificar_conflito(sala_id, inicio_dt, fim_dt):
            return render_template("reservar-sala.html", salas=salas, error="Conflito de horário! Escolha outro horário.")

        salvar_reserva(sala_id, inicio, fim)
        return redirect(url_for("detalhe_reserva", sala_id=sala_id, inicio=inicio, fim=fim))

    return render_template("reservar-sala.html", salas=salas)

def salvar_reserva(sala_id, inicio, fim):
    linha = f"{sala_id},{inicio},{fim}\n"
    with open("reservas.csv", "a") as file:
        file.write(linha)

# TODO: detalhe-reserva --> nome de usuario, gerar comprovante pdf, cancelar reserva