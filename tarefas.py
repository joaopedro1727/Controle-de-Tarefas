import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
from datetime import date, datetime
import json

# ==============================
# PALETA DE CORES — DEEP OCEAN PROFESSIONAL
# ==============================
C = {
    # Fundos
    "bg_main":      "#0D1117",   # Preto azulado profundo
    "bg_sidebar":   "#161B22",   # Painel lateral
    "bg_card":      "#1C2333",   # Cards/entradas
    "bg_card2":     "#21262D",   # Cards alternativos
    "bg_hover":     "#30363D",   # Hover

    # Texto
    "txt_primary":  "#E6EDF3",   # Branco suave principal
    "txt_secondary":"#8B949E",   # Cinza médio
    "txt_muted":    "#484F58",   # Cinza escuro

    # Acentos
    "accent":       "#58A6FF",   # Azul elétrico (destaque principal)
    "accent2":      "#3FB950",   # Verde (concluído/sucesso)
    "accent3":      "#D29922",   # Âmbar (alerta)
    "accent4":      "#F85149",   # Vermelho (urgente/vencido)
    "accent5":      "#BC8CFF",   # Roxo (prioridade alta)

    # Bordas
    "border":       "#30363D",
    "border_focus": "#58A6FF",

    # Botões
    "btn_primary":  "#238636",
    "btn_primary_h":"#2EA043",
    "btn_danger":   "#DA3633",
    "btn_blue":     "#1F6FEB",
}

FONT_TITLE  = ("Segoe UI", 13, "bold")
FONT_LABEL  = ("Segoe UI", 9)
FONT_BODY   = ("Segoe UI", 10)
FONT_MONO   = ("Consolas", 9)
FONT_HEADER = ("Segoe UI", 11, "bold")

# ==============================
# BANCO DE DADOS
# ==============================
conexao = sqlite3.connect("tarefas.db")
cursor = conexao.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tarefas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_tarefa     TEXT NOT NULL,
    descricao       TEXT,
    status          TEXT DEFAULT 'Pendente',
    prioridade      TEXT DEFAULT 'Média',
    categoria       TEXT DEFAULT 'Pessoal',
    data_entrega    TEXT,
    data_criacao    TEXT,
    tags            TEXT,
    progresso       INTEGER DEFAULT 0
)
""")
conexao.commit()

# Migrações seguras
colunas_existentes = [row[1] for row in cursor.execute("PRAGMA table_info(tarefas)")]
for coluna, tipo in [
    ("descricao",    "TEXT"),
    ("prioridade",   "TEXT"),
    ("categoria",    "TEXT"),
    ("data_entrega", "TEXT"),
    ("data_criacao", "TEXT"),
    ("tags",         "TEXT"),
    ("progresso",    "INTEGER DEFAULT 0"),
]:
    if coluna not in colunas_existentes:
        cursor.execute(f"ALTER TABLE tarefas ADD COLUMN {coluna} {tipo}")
conexao.commit()

# ==============================
# ESTADO GLOBAL
# ==============================
tarefa_selecionada_id = None
# StringVars são criadas após tk.Tk() — veja abaixo

# ==============================
# HELPERS DE WIDGET
# ==============================
def criar_entry(parent, width=32, **kw):
    e = tk.Entry(parent, width=width,
                 bg=C["bg_card"], fg=C["txt_primary"],
                 insertbackground=C["accent"],
                 borderwidth=0, highlightthickness=1,
                 highlightbackground=C["border"],
                 highlightcolor=C["border_focus"],
                 font=FONT_BODY, **kw)
    return e

def criar_label(parent, txt, bold=False, color=None):
    f = (FONT_HEADER if bold else FONT_LABEL)
    return tk.Label(parent, text=txt, bg=C["bg_sidebar"],
                    fg=color or C["txt_secondary"], font=f)

def criar_btn(parent, txt, cmd, cor=None, fg="white", pad=(12,6)):
    cor = cor or C["btn_blue"]
    b = tk.Button(parent, text=txt, command=cmd,
                  bg=cor, fg=fg,
                  font=("Segoe UI", 9, "bold"),
                  relief="flat", cursor="hand2",
                  padx=pad[0], pady=pad[1],
                  activebackground=C["bg_hover"],
                  activeforeground="white",
                  borderwidth=0)
    b.bind("<Enter>", lambda e: b.config(bg=C["bg_hover"]))
    b.bind("<Leave>", lambda e: b.config(bg=cor))
    return b

def separador(parent, horizontal=True):
    orient = "horizontal" if horizontal else "vertical"
    sep = tk.Frame(parent, bg=C["border"],
                   height=1 if horizontal else 0,
                   width=0 if horizontal else 1)
    return sep

# ==============================
# FUNÇÕES DE BANCO
# ==============================
def cadastrar_tarefa():
    nome      = entry_nome.get().strip()
    descricao = text_descricao.get("1.0", tk.END).strip()
    status    = var_status.get()
    prioridade= var_prioridade.get()
    categoria = var_categoria.get()
    data_str  = entry_data.get().strip()
    tags      = entry_tags.get().strip()
    progresso = int(scale_progresso.get())

    if not nome:
        messagebox.showerror("Campo obrigatório", "Informe o nome da tarefa.")
        return

    if data_str:
        try:
            datetime.strptime(data_str, "%d/%m/%Y")
        except ValueError:
            messagebox.showerror("Data inválida", "Use o formato DD/MM/AAAA.")
            return

    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    cursor.execute(
        """INSERT INTO tarefas
           (nome_tarefa,descricao,status,prioridade,categoria,data_entrega,data_criacao,tags,progresso)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (nome, descricao, status, prioridade, categoria, data_str, agora, tags, progresso)
    )
    conexao.commit()
    limpar_form()
    messagebox.showinfo("✔ Sucesso", f"Tarefa «{nome}» cadastrada!")
    listar_tarefas()
    atualizar_dashboard()


def editar_tarefa():
    global tarefa_selecionada_id
    if not tarefa_selecionada_id:
        messagebox.showwarning("Atenção", "Selecione uma tarefa para editar.")
        return

    nome      = entry_nome.get().strip()
    descricao = text_descricao.get("1.0", tk.END).strip()
    status    = var_status.get()
    prioridade= var_prioridade.get()
    categoria = var_categoria.get()
    data_str  = entry_data.get().strip()
    tags      = entry_tags.get().strip()
    progresso = int(scale_progresso.get())

    if not nome:
        messagebox.showerror("Campo obrigatório", "Informe o nome da tarefa.")
        return

    if data_str:
        try:
            datetime.strptime(data_str, "%d/%m/%Y")
        except ValueError:
            messagebox.showerror("Data inválida", "Use o formato DD/MM/AAAA.")
            return

    cursor.execute(
        """UPDATE tarefas SET
           nome_tarefa=?, descricao=?, status=?, prioridade=?,
           categoria=?, data_entrega=?, tags=?, progresso=?
           WHERE id=?""",
        (nome, descricao, status, prioridade, categoria, data_str, tags, progresso,
         tarefa_selecionada_id)
    )
    conexao.commit()
    limpar_form()
    messagebox.showinfo("✔ Atualizado", "Tarefa atualizada com sucesso!")
    listar_tarefas()
    atualizar_dashboard()


def excluir_tarefa():
    global tarefa_selecionada_id
    if not tarefa_selecionada_id:
        messagebox.showwarning("Atenção", "Selecione uma tarefa para excluir.")
        return
    if messagebox.askyesno("Confirmar", "Deseja excluir esta tarefa permanentemente?"):
        cursor.execute("DELETE FROM tarefas WHERE id=?", (tarefa_selecionada_id,))
        conexao.commit()
        limpar_form()
        listar_tarefas()
        atualizar_dashboard()


def marcar_concluida():
    global tarefa_selecionada_id
    if not tarefa_selecionada_id:
        messagebox.showwarning("Atenção", "Selecione uma tarefa.")
        return
    cursor.execute("UPDATE tarefas SET status='Concluído', progresso=100 WHERE id=?",
                   (tarefa_selecionada_id,))
    conexao.commit()
    limpar_form()
    listar_tarefas()
    atualizar_dashboard()


def limpar_form():
    global tarefa_selecionada_id
    tarefa_selecionada_id = None
    entry_nome.delete(0, tk.END)
    text_descricao.delete("1.0", tk.END)
    entry_data.delete(0, tk.END)
    entry_tags.delete(0, tk.END)
    var_status.set("Pendente")
    var_prioridade.set("Média")
    var_categoria.set("Pessoal")
    scale_progresso.set(0)
    lbl_progresso_val.config(text="0%")
    btn_cadastrar.config(text="＋  CADASTRAR", bg=C["btn_primary"])
    btn_cadastrar.bind("<Leave>", lambda e: btn_cadastrar.config(bg=C["btn_primary"]))
    btn_editar.config(state="disabled")
    btn_excluir.config(state="disabled")
    btn_concluir.config(state="disabled")
    lbl_modo.config(text="Novo registro", fg=C["txt_muted"])


def carregar_para_edicao(tid):
    global tarefa_selecionada_id
    cursor.execute("SELECT * FROM tarefas WHERE id=?", (tid,))
    row = cursor.fetchone()
    if not row:
        return
    _, nome, desc, status, prio, cat, data_e, data_c, tags, prog = row

    tarefa_selecionada_id = tid
    entry_nome.delete(0, tk.END);        entry_nome.insert(0, nome or "")
    text_descricao.delete("1.0", tk.END); text_descricao.insert("1.0", desc or "")
    entry_data.delete(0, tk.END);        entry_data.insert(0, data_e or "")
    entry_tags.delete(0, tk.END);        entry_tags.insert(0, tags or "")
    var_status.set(status or "Pendente")
    var_prioridade.set(prio or "Média")
    var_categoria.set(cat or "Pessoal")
    scale_progresso.set(prog or 0)
    lbl_progresso_val.config(text=f"{prog or 0}%")

    btn_cadastrar.config(text="💾  SALVAR NOVO", bg=C["btn_blue"])
    btn_cadastrar.bind("<Leave>", lambda e: btn_cadastrar.config(bg=C["btn_blue"]))
    btn_editar.config(state="normal")
    btn_excluir.config(state="normal")
    btn_concluir.config(state="normal")
    lbl_modo.config(text=f"Editando tarefa #{tid}", fg=C["accent"])


def listar_tarefas():
    busca    = busca_var.get().strip().lower()
    f_status = filtro_status.get()
    f_cat    = filtro_categoria.get()
    f_prio   = filtro_prioridade.get()

    query  = "SELECT * FROM tarefas WHERE 1=1"
    params = []
    if f_status  and f_status  != "Todos": query += " AND status=?";    params.append(f_status)
    if f_cat     and f_cat     != "Todas": query += " AND categoria=?"; params.append(f_cat)
    if f_prio    and f_prio    != "Todas": query += " AND prioridade=?";params.append(f_prio)
    query += " ORDER BY id DESC"

    cursor.execute(query, params)
    dados = cursor.fetchall()

    if busca:
        dados = [d for d in dados if busca in (d[1] or "").lower()
                                  or busca in (d[2] or "").lower()
                                  or busca in (d[8] or "").lower()]

    # Limpar treeview
    for item in tree.get_children():
        tree.delete(item)

    hoje = date.today()
    total = len(dados)
    lbl_total.config(text=f"{total} tarefa{'s' if total!=1 else ''} encontrada{'s' if total!=1 else ''}")

    for d in dados:
        tid, nome, desc, status, prio, cat, data_e, data_c, tags, prog = d

        alerta = ""
        tag_row = ""
        if data_e:
            try:
                dt = datetime.strptime(data_e, "%d/%m/%Y").date()
                dias = (dt - hoje).days
                if dias < 0:
                    alerta = " ⚠ VENCIDA"
                    tag_row = "vencida"
                elif dias == 0:
                    alerta = " ⚡ HOJE"
                    tag_row = "hoje"
                elif dias == 1:
                    alerta = " ⏰ AMANHÃ"
                    tag_row = "amanha"
            except ValueError:
                pass

        status_icon = {"Pendente": "○", "Em andamento": "◑", "Concluído": "●"}.get(status, "○")
        prio_icon   = {"Alta": "🔴", "Média": "🟡", "Baixa": "🟢"}.get(prio, "●")

        values = (
            f"#{tid}",
            f"{status_icon} {nome}{alerta}",
            f"{prio_icon} {prio}",
            status,
            cat,
            data_e or "—",
            f"{prog or 0}%",
        )
        iid = tree.insert("", "end", values=values, tags=(tag_row,) if tag_row else ())

    tree.tag_configure("vencida", foreground=C["accent4"])
    tree.tag_configure("hoje",    foreground=C["accent5"])
    tree.tag_configure("amanha",  foreground=C["accent3"])


def atualizar_dashboard():
    cursor.execute("SELECT COUNT(*) FROM tarefas")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tarefas WHERE status='Pendente'")
    pendentes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tarefas WHERE status='Em andamento'")
    andamento = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tarefas WHERE status='Concluído'")
    concluidas = cursor.fetchone()[0]

    hoje_str = date.today().strftime("%d/%m/%Y")
    cursor.execute(
        "SELECT COUNT(*) FROM tarefas WHERE data_entrega < ? AND status != 'Concluído'",
        (hoje_str,)
    )
    # Conta vencidas comparando datas corretamente
    cursor.execute("SELECT data_entrega FROM tarefas WHERE data_entrega IS NOT NULL AND status != 'Concluído'")
    rows = cursor.fetchall()
    vencidas = 0
    hoje = date.today()
    for (d,) in rows:
        try:
            if datetime.strptime(d, "%d/%m/%Y").date() < hoje:
                vencidas += 1
        except:
            pass

    lbl_dash_total.config(text=str(total))
    lbl_dash_pend.config(text=str(pendentes))
    lbl_dash_and.config(text=str(andamento))
    lbl_dash_conc.config(text=str(concluidas))
    lbl_dash_venc.config(text=str(vencidas))

    pct = int((concluidas / total * 100) if total > 0 else 0)
    lbl_dash_pct.config(text=f"{pct}% concluído")
    canvas_barra.delete("all")
    canvas_barra.create_rectangle(0, 0, 220, 8, fill=C["bg_hover"], outline="")
    if pct > 0:
        canvas_barra.create_rectangle(0, 0, int(220*pct/100), 8, fill=C["accent2"], outline="")


def exportar_txt():
    cursor.execute("SELECT * FROM tarefas ORDER BY id")
    dados = cursor.fetchall()
    if not dados:
        messagebox.showinfo("Exportar", "Nenhuma tarefa para exportar.")
        return
    linhas = [f"RELATÓRIO DE TAREFAS — {datetime.now().strftime('%d/%m/%Y %H:%M')}\n{'='*60}\n"]
    for d in dados:
        tid, nome, desc, status, prio, cat, data_e, data_c, tags, prog = d
        linhas.append(
            f"#{tid} {nome}\n"
            f"  Status: {status} | Prioridade: {prio} | Categoria: {cat}\n"
            f"  Entrega: {data_e or '—'} | Progresso: {prog or 0}%\n"
            f"  Tags: {tags or '—'}\n"
            f"  Criada em: {data_c or '—'}\n"
            + (f"  Descrição: {desc}\n" if desc else "")
            + "\n"
        )
    with open("relatorio_tarefas.txt", "w", encoding="utf-8") as f:
        f.writelines(linhas)
    messagebox.showinfo("✔ Exportado", "Arquivo 'relatorio_tarefas.txt' gerado com sucesso!")


def on_tree_select(event):
    sel = tree.selection()
    if not sel:
        return
    vals = tree.item(sel[0], "values")
    if vals:
        tid = int(vals[0].replace("#", ""))
        carregar_para_edicao(tid)


def buscar_em_tempo_real(*args):
    listar_tarefas()


# ==============================
# JANELA PRINCIPAL
# ==============================
janela = tk.Tk()
janela.title("TaskFlow — Gerenciador de Tarefas")

# StringVars precisam ser criadas após tk.Tk()
filtro_status     = tk.StringVar()
filtro_categoria  = tk.StringVar()
filtro_prioridade = tk.StringVar()
busca_var         = tk.StringVar()

janela.configure(bg=C["bg_main"])
janela.resizable(True, True)
janela.minsize(1100, 680)

w, h = 1200, 720
sw = janela.winfo_screenwidth()
sh = janela.winfo_screenheight()
janela.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

# ==============================
# LAYOUT PRINCIPAL: SIDEBAR + CONTEÚDO
# ==============================
sidebar = tk.Frame(janela, bg=C["bg_sidebar"], width=320)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

conteudo = tk.Frame(janela, bg=C["bg_main"])
conteudo.pack(side="left", fill="both", expand=True)

# ==============================
# SIDEBAR — LOGO/HEADER
# ==============================
frame_logo = tk.Frame(sidebar, bg=C["bg_sidebar"], pady=20)
frame_logo.pack(fill="x", padx=20)

tk.Label(frame_logo, text="⚡ TaskFlow", font=("Segoe UI", 16, "bold"),
         bg=C["bg_sidebar"], fg=C["accent"]).pack(anchor="w")
tk.Label(frame_logo, text="Gerenciador Profissional", font=FONT_LABEL,
         bg=C["bg_sidebar"], fg=C["txt_muted"]).pack(anchor="w")

separador(sidebar).pack(fill="x", padx=15, pady=4)

# ==============================
# SIDEBAR — DASHBOARD
# ==============================
frame_dash = tk.Frame(sidebar, bg=C["bg_sidebar"], padx=16, pady=10)
frame_dash.pack(fill="x")

tk.Label(frame_dash, text="RESUMO", font=("Segoe UI", 8, "bold"),
         bg=C["bg_sidebar"], fg=C["txt_muted"]).pack(anchor="w", pady=(0,8))

def dash_card(parent, label, color):
    f = tk.Frame(parent, bg=C["bg_card"], padx=12, pady=8)
    f.pack(fill="x", pady=3)
    tk.Label(f, text=label, font=("Segoe UI", 8),
             bg=C["bg_card"], fg=C["txt_secondary"]).pack(anchor="w")
    lbl = tk.Label(f, text="0", font=("Segoe UI", 20, "bold"),
                   bg=C["bg_card"], fg=color)
    lbl.pack(anchor="w")
    return lbl

lbl_dash_total = dash_card(frame_dash, "Total de tarefas", C["txt_primary"])
lbl_dash_pend  = dash_card(frame_dash, "Pendentes",        C["accent3"])
lbl_dash_and   = dash_card(frame_dash, "Em andamento",     C["accent"])
lbl_dash_conc  = dash_card(frame_dash, "Concluídas",       C["accent2"])
lbl_dash_venc  = dash_card(frame_dash, "Vencidas",         C["accent4"])

frame_pct = tk.Frame(frame_dash, bg=C["bg_sidebar"], pady=6)
frame_pct.pack(fill="x")
lbl_dash_pct = tk.Label(frame_pct, text="0% concluído",
                        font=("Segoe UI", 9, "bold"),
                        bg=C["bg_sidebar"], fg=C["accent2"])
lbl_dash_pct.pack(anchor="w")
canvas_barra = tk.Canvas(frame_pct, bg=C["bg_sidebar"], height=8, width=220,
                         borderwidth=0, highlightthickness=0)
canvas_barra.pack(anchor="w", pady=(4,0))

separador(sidebar).pack(fill="x", padx=15, pady=8)

# ==============================
# SIDEBAR — FILTROS
# ==============================
frame_filtros = tk.Frame(sidebar, bg=C["bg_sidebar"], padx=16, pady=6)
frame_filtros.pack(fill="x")

tk.Label(frame_filtros, text="FILTROS", font=("Segoe UI", 8, "bold"),
         bg=C["bg_sidebar"], fg=C["txt_muted"]).grid(row=0, column=0, sticky="w", pady=(0,8))

def filtro_combo(parent, row, label, var, opcoes):
    tk.Label(parent, text=label, font=FONT_LABEL,
             bg=C["bg_sidebar"], fg=C["txt_secondary"]).grid(row=row, column=0, sticky="w", pady=2)
    cb = ttk.Combobox(parent, textvariable=var, values=opcoes,
                      state="readonly", width=26)
    cb.grid(row=row+1, column=0, sticky="ew", pady=(0,6))
    cb.bind("<<ComboboxSelected>>", lambda e: listar_tarefas())
    return cb

filtro_status.set("Todos")
filtro_combo(frame_filtros, 1, "Status", filtro_status,
             ["Todos", "Pendente", "Em andamento", "Concluído"])

filtro_categoria.set("Todas")
filtro_combo(frame_filtros, 3, "Categoria", filtro_categoria,
             ["Todas", "Trabalho", "Pessoal", "Estudo", "Finanças", "Compras", "Saúde"])

filtro_prioridade.set("Todas")
filtro_combo(frame_filtros, 5, "Prioridade", filtro_prioridade,
             ["Todas", "Alta", "Média", "Baixa"])

# Style para comboboxes
style = ttk.Style()
style.theme_use("clam")
style.configure("TCombobox",
                fieldbackground=C["bg_card"],
                background=C["bg_card"],
                foreground=C["txt_primary"],
                selectbackground=C["bg_hover"],
                selectforeground=C["txt_primary"],
                bordercolor=C["border"],
                arrowcolor=C["txt_secondary"])
style.map("TCombobox",
          fieldbackground=[("readonly", C["bg_card"])],
          background=[("readonly", C["bg_card"])],
          foreground=[("readonly", C["txt_primary"])])

separador(sidebar).pack(fill="x", padx=15, pady=8)

# ==============================
# SIDEBAR — AÇÕES RÁPIDAS
# ==============================
frame_acoes = tk.Frame(sidebar, bg=C["bg_sidebar"], padx=16, pady=6)
frame_acoes.pack(fill="x")

tk.Label(frame_acoes, text="AÇÕES", font=("Segoe UI", 8, "bold"),
         bg=C["bg_sidebar"], fg=C["txt_muted"]).pack(anchor="w", pady=(0,8))

criar_btn(frame_acoes, "📤  Exportar Relatório TXT", exportar_txt,
          cor=C["bg_card2"]).pack(fill="x", pady=2)

def resetar_filtros():
    filtro_status.set("Todos")
    filtro_categoria.set("Todas")
    filtro_prioridade.set("Todas")
    busca_var.set("")
    listar_tarefas()

def excluir_selecionada_sidebar():
    """Exclui a tarefa selecionada na treeview (atalho na sidebar)."""
    global tarefa_selecionada_id
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Atenção", "Selecione uma tarefa na lista para excluir.")
        return
    vals = tree.item(sel[0], "values")
    tid = int(vals[0].replace("#", ""))
    nome = vals[1]
    if messagebox.askyesno("Confirmar exclusão",
                           f"Deseja excluir a tarefa:\n\n«{nome}»\n\nEsta ação não pode ser desfeita."):
        cursor.execute("DELETE FROM tarefas WHERE id=?", (tid,))
        conexao.commit()
        limpar_form()
        listar_tarefas()
        atualizar_dashboard()
        messagebox.showinfo("✔ Excluída", "Tarefa excluída com sucesso.")

def limpar_todas_tarefas():
    """Remove todas as tarefas do banco após dupla confirmação."""
    cursor.execute("SELECT COUNT(*) FROM tarefas")
    total = cursor.fetchone()[0]
    if total == 0:
        messagebox.showinfo("Aviso", "Não há tarefas para limpar.")
        return
    if not messagebox.askyesno("⚠ Atenção",
                                f"Isso irá excluir TODAS as {total} tarefa(s) permanentemente.\n\nDeseja continuar?",
                                icon="warning"):
        return
    if not messagebox.askyesno("⚠ Confirmação final",
                                "Tem certeza absoluta? Esta ação NÃO pode ser desfeita.",
                                icon="warning"):
        return
    cursor.execute("DELETE FROM tarefas")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='tarefas'")
    conexao.commit()
    limpar_form()
    listar_tarefas()
    atualizar_dashboard()
    messagebox.showinfo("✔ Concluído", "Todas as tarefas foram removidas.")

criar_btn(frame_acoes, "↺  Limpar Filtros", resetar_filtros,
          cor=C["bg_card2"]).pack(fill="x", pady=2)

separador(frame_acoes).pack(fill="x", pady=8)

tk.Label(frame_acoes, text="PERIGO", font=("Segoe UI", 8, "bold"),
         bg=C["bg_sidebar"], fg=C["txt_muted"]).pack(anchor="w", pady=(0,6))

criar_btn(frame_acoes, "🗑  Excluir Selecionada", excluir_selecionada_sidebar,
          cor=C["btn_danger"]).pack(fill="x", pady=2)

criar_btn(frame_acoes, "⚠  Limpar Todas as Tarefas", limpar_todas_tarefas,
          cor="#7F1D1D").pack(fill="x", pady=2)

# ==============================
# CONTEÚDO — TOPO (BUSCA + TÍTULO)
# ==============================
frame_topo = tk.Frame(conteudo, bg=C["bg_main"], padx=24, pady=16)
frame_topo.pack(fill="x")

tk.Label(frame_topo, text="Suas Tarefas", font=("Segoe UI", 18, "bold"),
         bg=C["bg_main"], fg=C["txt_primary"]).pack(side="left")

frame_busca = tk.Frame(frame_topo, bg=C["bg_card"], padx=8, pady=4)
frame_busca.pack(side="right")
tk.Label(frame_busca, text="🔍", bg=C["bg_card"], fg=C["txt_muted"]).pack(side="left")
entry_busca = tk.Entry(frame_busca, textvariable=busca_var, width=28,
                       bg=C["bg_card"], fg=C["txt_primary"],
                       insertbackground=C["accent"],
                       borderwidth=0, highlightthickness=0,
                       font=FONT_BODY)
entry_busca.pack(side="left", padx=4)
busca_var.trace_add("write", buscar_em_tempo_real)

lbl_total = tk.Label(frame_topo, text="", font=FONT_LABEL,
                     bg=C["bg_main"], fg=C["txt_secondary"])
lbl_total.pack(side="right", padx=16)

separador(conteudo).pack(fill="x", padx=24)

# PanedWindow divide treeview (cima) e formulário (baixo) — ambos ficam visíveis
paned = tk.PanedWindow(conteudo, orient="vertical", bg=C["bg_main"],
                       sashwidth=5, sashrelief="flat", sashpad=2,
                       handlesize=0)
paned.pack(fill="both", expand=True)

# ==============================
# PAINEL SUPERIOR — TREEVIEW
# ==============================
frame_tree = tk.Frame(paned, bg=C["bg_main"], padx=24, pady=8)
paned.add(frame_tree, minsize=160, stretch="always")

style.configure("Custom.Treeview",
                background=C["bg_card"],
                foreground=C["txt_primary"],
                rowheight=32,
                fieldbackground=C["bg_card"],
                borderwidth=0,
                font=FONT_BODY)
style.configure("Custom.Treeview.Heading",
                background=C["bg_card2"],
                foreground=C["txt_secondary"],
                relief="flat",
                font=("Segoe UI", 9, "bold"))
style.map("Custom.Treeview",
          background=[("selected", C["bg_hover"])],
          foreground=[("selected", C["accent"])])

colunas = ("id", "nome", "prioridade", "status", "categoria", "entrega", "progresso")
tree = ttk.Treeview(frame_tree, columns=colunas, show="headings",
                    style="Custom.Treeview", selectmode="browse")

tree.heading("id",         text="#")
tree.heading("nome",       text="Tarefa")
tree.heading("prioridade", text="Prioridade")
tree.heading("status",     text="Status")
tree.heading("categoria",  text="Categoria")
tree.heading("entrega",    text="Entrega")
tree.heading("progresso",  text="Progresso")

tree.column("id",         width=50,  anchor="center", stretch=False)
tree.column("nome",       width=280, anchor="w")
tree.column("prioridade", width=90,  anchor="center")
tree.column("status",     width=110, anchor="center")
tree.column("categoria",  width=100, anchor="center")
tree.column("entrega",    width=100, anchor="center")
tree.column("progresso",  width=80,  anchor="center")

scroll_tree = ttk.Scrollbar(frame_tree, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scroll_tree.set)

tree.pack(side="left", fill="both", expand=True)
scroll_tree.pack(side="right", fill="y")
tree.bind("<<TreeviewSelect>>", on_tree_select)

# ==============================
# PAINEL INFERIOR — FORMULÁRIO (com scroll)
# ==============================
frame_form_container = tk.Frame(paned, bg=C["bg_sidebar"])
paned.add(frame_form_container, minsize=120, stretch="never")

# Canvas + scrollbar para o formulário
form_canvas = tk.Canvas(frame_form_container, bg=C["bg_sidebar"],
                        borderwidth=0, highlightthickness=0)
form_scrollbar = ttk.Scrollbar(frame_form_container, orient="vertical",
                               command=form_canvas.yview)
form_canvas.configure(yscrollcommand=form_scrollbar.set)

form_scrollbar.pack(side="right", fill="y")
form_canvas.pack(side="left", fill="both", expand=True)

frame_form_outer = tk.Frame(form_canvas, bg=C["bg_sidebar"])
form_canvas_window = form_canvas.create_window((0, 0), window=frame_form_outer,
                                               anchor="nw")

def _on_form_configure(event):
    form_canvas.configure(scrollregion=form_canvas.bbox("all"))
    form_canvas.itemconfig(form_canvas_window, width=form_canvas.winfo_width())

frame_form_outer.bind("<Configure>", _on_form_configure)
form_canvas.bind("<Configure>", lambda e: form_canvas.itemconfig(
    form_canvas_window, width=e.width))

def _scroll_form(event):
    form_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
form_canvas.bind_all("<MouseWheel>", _scroll_form)

# Header do form
frame_form_header = tk.Frame(frame_form_outer, bg=C["bg_sidebar"], padx=24, pady=10)
frame_form_header.pack(fill="x")

tk.Label(frame_form_header, text="✏  FORMULÁRIO", font=FONT_HEADER,
         bg=C["bg_sidebar"], fg=C["accent"]).pack(side="left")

lbl_modo = tk.Label(frame_form_header, text="Novo registro", font=FONT_LABEL,
                    bg=C["bg_sidebar"], fg=C["txt_muted"])
lbl_modo.pack(side="left", padx=12)

criar_btn(frame_form_header, "✕ Cancelar", limpar_form,
          cor=C["bg_card2"], pad=(8,4)).pack(side="right")

separador(frame_form_outer).pack(fill="x", padx=0)

frame_form = tk.Frame(frame_form_outer, bg=C["bg_sidebar"], padx=24, pady=14)
frame_form.pack(fill="x")

# Coluna 1
col1 = tk.Frame(frame_form, bg=C["bg_sidebar"])
col1.grid(row=0, column=0, sticky="nw", padx=(0,20))

tk.Label(col1, text="Nome da tarefa *", font=FONT_LABEL,
         bg=C["bg_sidebar"], fg=C["txt_secondary"]).pack(anchor="w")
entry_nome = criar_entry(col1, width=36)
entry_nome.config(highlightbackground=C["border"])
entry_nome.pack(fill="x", ipady=5, pady=(2,8))

tk.Label(col1, text="Descrição", font=FONT_LABEL,
         bg=C["bg_sidebar"], fg=C["txt_secondary"]).pack(anchor="w")
text_descricao = tk.Text(col1, width=36, height=3,
                         bg=C["bg_card"], fg=C["txt_primary"],
                         insertbackground=C["accent"],
                         borderwidth=0, highlightthickness=1,
                         highlightbackground=C["border"],
                         font=FONT_BODY)
text_descricao.pack(fill="x", pady=(2,8))

tk.Label(col1, text="Tags (separadas por vírgula)", font=FONT_LABEL,
         bg=C["bg_sidebar"], fg=C["txt_secondary"]).pack(anchor="w")
entry_tags = criar_entry(col1, width=36)
entry_tags.pack(fill="x", ipady=5, pady=(2,0))

# Coluna 2
col2 = tk.Frame(frame_form, bg=C["bg_sidebar"])
col2.grid(row=0, column=1, sticky="nw", padx=(0,20))

tk.Label(col2, text="Data de entrega (DD/MM/AAAA)", font=FONT_LABEL,
         bg=C["bg_sidebar"], fg=C["txt_secondary"]).pack(anchor="w")
entry_data = criar_entry(col2, width=22)
entry_data.pack(fill="x", ipady=5, pady=(2,8))

tk.Label(col2, text="Status", font=FONT_LABEL,
         bg=C["bg_sidebar"], fg=C["txt_secondary"]).pack(anchor="w")
var_status = tk.StringVar(value="Pendente")
frame_st = tk.Frame(col2, bg=C["bg_sidebar"])
frame_st.pack(anchor="w", pady=(2,8))
for op, cl in [("Pendente", C["txt_primary"]), ("Em andamento", C["accent"]), ("Concluído", C["accent2"])]:
    tk.Radiobutton(frame_st, text=op, variable=var_status, value=op,
                   bg=C["bg_sidebar"], fg=cl,
                   selectcolor=C["bg_card"],
                   activebackground=C["bg_sidebar"],
                   activeforeground="white",
                   font=FONT_LABEL).pack(side="left", padx=(0,8))

tk.Label(col2, text="Prioridade", font=FONT_LABEL,
         bg=C["bg_sidebar"], fg=C["txt_secondary"]).pack(anchor="w")
var_prioridade = tk.StringVar(value="Média")
frame_pr = tk.Frame(col2, bg=C["bg_sidebar"])
frame_pr.pack(anchor="w", pady=(2,8))
for op, cl in [("Alta", C["accent4"]), ("Média", C["accent3"]), ("Baixa", C["accent2"])]:
    tk.Radiobutton(frame_pr, text=op, variable=var_prioridade, value=op,
                   bg=C["bg_sidebar"], fg=cl,
                   selectcolor=C["bg_card"],
                   activebackground=C["bg_sidebar"],
                   activeforeground="white",
                   font=FONT_LABEL).pack(side="left", padx=(0,8))

tk.Label(col2, text="Progresso", font=FONT_LABEL,
         bg=C["bg_sidebar"], fg=C["txt_secondary"]).pack(anchor="w")
frame_prog = tk.Frame(col2, bg=C["bg_sidebar"])
frame_prog.pack(anchor="w", pady=(2,0))
scale_progresso = tk.Scale(frame_prog, from_=0, to=100, orient="horizontal",
                           length=160, bg=C["bg_sidebar"], fg=C["txt_primary"],
                           troughcolor=C["bg_card"], highlightthickness=0,
                           activebackground=C["accent"],
                           command=lambda v: lbl_progresso_val.config(text=f"{int(float(v))}%"))
scale_progresso.pack(side="left")
lbl_progresso_val = tk.Label(frame_prog, text="0%", font=("Segoe UI", 10, "bold"),
                             bg=C["bg_sidebar"], fg=C["accent"], width=4)
lbl_progresso_val.pack(side="left", padx=6)

# Coluna 3
col3 = tk.Frame(frame_form, bg=C["bg_sidebar"])
col3.grid(row=0, column=2, sticky="nw", padx=(0,20))

tk.Label(col3, text="Categoria", font=FONT_LABEL,
         bg=C["bg_sidebar"], fg=C["txt_secondary"]).pack(anchor="w")
var_categoria = tk.StringVar(value="Pessoal")
menu_cat = ttk.Combobox(col3, textvariable=var_categoria, state="readonly", width=20,
                        values=["Trabalho","Pessoal","Estudo","Finanças","Compras","Saúde"])
menu_cat.pack(fill="x", pady=(2,16))

# Botões de ação
btn_cadastrar = tk.Button(col3, text="＋  CADASTRAR", command=cadastrar_tarefa,
                          bg=C["btn_primary"], fg="white",
                          font=("Segoe UI", 10, "bold"),
                          relief="flat", cursor="hand2", padx=14, pady=8,
                          activebackground=C["btn_primary_h"],
                          activeforeground="white")
btn_cadastrar.pack(fill="x", pady=3)

btn_editar = tk.Button(col3, text="✏  ATUALIZAR", command=editar_tarefa,
                       bg=C["btn_blue"], fg="white",
                       font=("Segoe UI", 10, "bold"),
                       relief="flat", cursor="hand2", padx=14, pady=8,
                       state="disabled",
                       activebackground=C["bg_hover"],
                       activeforeground="white")
btn_editar.pack(fill="x", pady=3)

btn_concluir = tk.Button(col3, text="✔  MARCAR CONCLUÍDA", command=marcar_concluida,
                         bg=C["bg_card2"], fg=C["accent2"],
                         font=("Segoe UI", 10, "bold"),
                         relief="flat", cursor="hand2", padx=14, pady=8,
                         state="disabled",
                         activebackground=C["bg_hover"],
                         activeforeground=C["accent2"])
btn_concluir.pack(fill="x", pady=3)

btn_excluir = tk.Button(col3, text="🗑  EXCLUIR", command=excluir_tarefa,
                        bg=C["bg_card2"], fg=C["accent4"],
                        font=("Segoe UI", 10, "bold"),
                        relief="flat", cursor="hand2", padx=14, pady=8,
                        state="disabled",
                        activebackground=C["bg_hover"],
                        activeforeground=C["accent4"])
btn_excluir.pack(fill="x", pady=3)

# ==============================
# INICIALIZAR
# ==============================
listar_tarefas()
atualizar_dashboard()

janela.mainloop()
conexao.close()