import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from database import DATABASE_NAME
from datetime import datetime, date

class EstoqueGUI(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding="15")
        self.master = master

        self.conn = self.get_db_connection()

        # Variáveis StringVar que controlarão o texto dos Entry widgets
        self.selected_produto_var = tk.StringVar(value="-- Selecione o Produto --")
        self.tipo_mov_var = tk.StringVar(value="Entrada")
        self.quantidade_mov_var = tk.StringVar(value="")
        self.custo_unitario_mov_var = tk.StringVar(value="0.00")
        self.motivo_mov_var = tk.StringVar(value="")
        self.filter_estoque_status_var = tk.StringVar(value="Todos")
        self.data_inicio_mov_var = tk.StringVar(value=(datetime.now().replace(day=1)).strftime("%Y-%m-%d"))
        self.data_fim_mov_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.filter_tipo_mov_var = tk.StringVar(value="Todos")

        self.formas_pagamento_caixa_options = ["Dinheiro", "Cartao", "Pix", "Recebimento Parcela", "Outros"]
        self.tipos_movimentacao_options = ["Todos", "Entrada", "Saida", "Ajuste"]

        self.produtos_dict = {}
        self.vendedores_dict = {}

        self.create_widgets()
        self._load_vendedores_for_dropdown()
        self.load_produtos_for_dropdown()
        self.load_estoque_atual()
        self.load_historico_movimentacoes()


    def get_db_connection(self):
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row
        return conn

    def _load_vendedores_for_dropdown(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM vendedores ORDER BY nome")
        vendedores_db = cursor.fetchall()
        conn.close()

        self.vendedores_dict = {}
        for v in vendedores_db:
            self.vendedores_dict[v['nome']] = v['id']

    def load_produtos_for_dropdown(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, sku, preco_venda, quantidade FROM produtos")
        produtos_db = cursor.fetchall()
        conn.close()

        self.produtos_dict = {}
        produtos_nomes_sku = ["-- Selecione o Produto --"]
        for p in produtos_db:
            display_name = f"{p['nome']} ({p['sku']})"
            self.produtos_dict[display_name] = p['id']
            produtos_nomes_sku.append(display_name)
        
        menu_prod = self.produto_dropdown["menu"]
        menu_prod.delete(0, "end")
        for nome in produtos_nomes_sku:
            menu_prod.add_command(label=nome, command=tk._setit(self.selected_produto_var, nome))
        self.selected_produto_var.set(produtos_nomes_sku[0])


    def create_widgets(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)

        self.tab_movimentacao = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_movimentacao, text="Movimentação de Estoque")
        self.create_movimentacao_widgets(self.tab_movimentacao)

        self.tab_estoque_atual = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_estoque_atual, text="Estoque Atual e Alertas")
        self.create_estoque_atual_widgets(self.tab_estoque_atual)

        self.tab_historico_mov = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_historico_mov, text="Histórico de Movimentações")
        self.create_historico_mov_widgets(self.tab_historico_mov)


    def create_movimentacao_widgets(self, parent_frame):
        ttk.Label(parent_frame, text="Produto:").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        self.produto_dropdown = ttk.OptionMenu(parent_frame, self.selected_produto_var, "")
        self.produto_dropdown.grid(row=0, column=1, columnspan=2, sticky="ew", pady=5, padx=5)
        self.produto_dropdown.config(width=40)

        ttk.Label(parent_frame, text="Tipo:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Radiobutton(parent_frame, text="Entrada", value="Entrada", variable=self.tipo_mov_var).grid(row=1, column=1, sticky="w", padx=5)
        ttk.Radiobutton(parent_frame, text="Ajuste (+/-)", value="Ajuste", variable=self.tipo_mov_var).grid(row=1, column=2, sticky="w", padx=5)

        ttk.Label(parent_frame, text="Quantidade:").grid(row=2, column=0, sticky="w", pady=5, padx=5)
        self.quantidade_mov_entry_widget = ttk.Entry(parent_frame, textvariable=self.quantidade_mov_var, width=10)
        self.quantidade_mov_entry_widget.grid(row=2, column=1, sticky="w", pady=5, padx=5)
        self.quantidade_mov_entry_widget.bind("<FocusOut>", lambda event=None: self.fill_default_if_empty(self.quantidade_mov_var, "0"))

        ttk.Label(parent_frame, text="Custo Unitário (Entrada):").grid(row=3, column=0, sticky="w", pady=5, padx=5)
        self.custo_unitario_mov_entry_widget = ttk.Entry(parent_frame, textvariable=self.custo_unitario_mov_var, width=10)
        self.custo_unitario_mov_entry_widget.grid(row=3, column=1, sticky="w", pady=5, padx=5)
        self.custo_unitario_mov_var.trace_add("write", lambda n, i, m: self.custo_unitario_mov_var.set(self.format_currency_input(self.custo_unitario_mov_var.get())))
        self.custo_unitario_mov_entry_widget.bind("<FocusOut>", lambda event=None: self.fill_default_if_empty(self.custo_unitario_mov_var, "0.00"))


        ttk.Label(parent_frame, text="Motivo:").grid(row=4, column=0, sticky="w", pady=5, padx=5)
        self.motivo_mov_entry_widget = ttk.Entry(parent_frame, textvariable=self.motivo_mov_var, width=50)
        self.motivo_mov_entry_widget.grid(row=4, column=1, columnspan=2, sticky="ew", pady=5, padx=5)

        ttk.Button(parent_frame, text="Registrar Movimentação", command=self.registrar_movimentacao, style='Accent.TButton').grid(row=5, column=0, columnspan=3, pady=15)
        
        parent_frame.columnconfigure(1, weight=1)

    def registrar_movimentacao(self):
        produto_nome_sku = self.selected_produto_var.get()
        if produto_nome_sku == "-- Selecione o Produto --":
            messagebox.showwarning("Aviso", "Por favor, selecione um produto.")
            return

        produto_id = self.produtos_dict[produto_nome_sku]['id']
        tipo_mov = self.tipo_mov_var.get().strip()
        quantidade_str = self.quantidade_mov_var.get().strip()
        motivo = self.motivo_mov_var.get().strip()
        custo_str = self.custo_unitario_mov_var.get().strip()

        if not quantidade_str:
            messagebox.showwarning("Aviso", "Por favor, digite a quantidade.")
            return
        
        try:
            quantidade = int(quantidade_str)
            if quantidade == 0:
                messagebox.showerror("Erro", "Quantidade não pode ser zero.")
                return
            if tipo_mov == "Entrada" and quantidade < 0:
                messagebox.showerror("Erro", "Para 'Entrada', a quantidade deve ser positiva.")
                return
        except ValueError:
            messagebox.showerror("Erro", "Quantidade inválida. Digite um número inteiro.")
            return

        custo_unitario = 0.0
        if tipo_mov == "Entrada" or tipo_mov == "Ajuste":
            if not custo_str:
                if messagebox.askyesno("Confirmação", "Custo unitário está vazio. Deseja prosseguir com 0.00?", parent=self.master):
                    custo_unitario = 0.0
                else:
                    return
            else:
                try:
                    custo_unitario = float(custo_str.replace(',', '.'))
                except ValueError:
                    messagebox.showerror("Erro", "Custo unitário inválido. Use um número.")
                    return

        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO movimentacoes_estoque (produto_id, tipo_movimentacao, quantidade, data_hora, motivo, custo_unitario_movimentacao) VALUES (?, ?, ?, ?, ?, ?)",
                           (produto_id, tipo_mov, quantidade, data_hora, motivo, custo_unitario))
            
            current_qty_query = cursor.execute("SELECT quantidade FROM produtos WHERE id = ?", (produto_id,)).fetchone()
            current_qty = current_qty_query['quantidade'] if current_qty_query else 0

            new_qty = current_qty
            if tipo_mov == "Entrada":
                new_qty += quantidade
            elif tipo_mov == "Ajuste":
                new_qty += quantidade
            # 'Saída' via PDV já é tratada lá e não vem por aqui.

            if new_qty < 0:
                messagebox.showerror("Erro", "Quantidade resultante não pode ser negativa. Ajuste a quantidade.")
                conn.rollback()
                return

            cursor.execute("UPDATE produtos SET quantidade = ? WHERE id = ?", (new_qty, produto_id))
            
            conn.commit()
            messagebox.showinfo("Sucesso", f"Movimentação de estoque registrada com sucesso para {produto_nome_sku}!")
            self.clear_movimentacao_form()
            self.load_estoque_atual()
            self.load_historico_movimentacoes()

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Erro", f"Erro ao registrar movimentação: {e}")
        finally:
            conn.close()

    def clear_movimentacao_form(self):
        self.selected_produto_var.set("-- Selecione o Produto --")
        self.quantidade_mov_var.set("")
        self.motivo_mov_var.set("")
        self.custo_unitario_mov_var.set("0.00")
        self.tipo_mov_var.set("Entrada")
        
    def create_estoque_atual_widgets(self, parent_frame):
        filter_frame = ttk.Frame(parent_frame, padding="5")
        filter_frame.pack(pady=5, fill="x")

        ttk.Label(filter_frame, text="Status:").pack(side="left", padx=5) # REMOVIDO background='white'
        self.filter_estoque_status_var = tk.StringVar(value="Todos")
        filter_status_options = ["Todos", "Em Estoque", "Abaixo do Mínimo", "Esgotado"]
        self.filter_estoque_status_menu = ttk.OptionMenu(filter_frame, self.filter_estoque_status_var, *filter_status_options)
        self.filter_estoque_status_menu.pack(side="left", padx=2)
        ttk.Button(filter_frame, text="Atualizar", command=self.load_estoque_atual).pack(side="left", padx=10)

        columns = ("ID", "SKU", "Nome", "Marca", "Quantidade", "Estoque Mínimo", "Status")
        self.estoque_tree = ttk.Treeview(parent_frame, columns=columns, show="headings", selectmode="browse")

        for col in columns:
            self.estoque_tree.heading(col, text=col)
            if col == "ID":
                self.estoque_tree.column(col, width=40, anchor="center")
            elif col == "SKU":
                self.estoque_tree.column(col, width=80, anchor="center")
            elif col == "Nome":
                self.estoque_tree.column(col, width=200, anchor="w")
            elif col == "Marca":
                self.estoque_tree.column(col, width=100, anchor="w")
            elif col in ["Quantidade", "Estoque Mínimo"]:
                self.estoque_tree.column(col, width=90, anchor="center")
            elif col == "Status":
                self.estoque_tree.column(col, width=120, anchor="center")
            else:
                self.estoque_tree.column(col, width=80, anchor="center")

        self.estoque_tree.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=self.estoque_tree.yview)
        self.estoque_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    def load_estoque_atual(self, *args):
        for item in self.estoque_tree.get_children():
            self.estoque_tree.delete(item)
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, sku, nome, marca, quantidade, estoque_minimo FROM produtos ORDER BY nome")
        produtos_estoque = cursor.fetchall()
        conn.close()

        filter_status = self.filter_estoque_status_var.get()

        for p in produtos_estoque:
            status = "Em Estoque"
            tags = ()
            if p['quantidade'] <= 0:
                status = "Esgotado"
                tags = ('esgotado',)
            elif p['quantidade'] <= p['estoque_minimo']:
                status = "Abaixo do Mínimo"
                tags = ('baixo',)
            
            if filter_status == "Todos" or status == filter_status:
                self.estoque_tree.insert("", "end", values=(p['id'], p['sku'], p['nome'], p['marca'], p['quantidade'], p['estoque_minimo'], status), tags=tags)

    def create_historico_mov_widgets(self, parent_frame):
        filter_mov_frame = ttk.Frame(parent_frame, padding="5")
        filter_mov_frame.pack(pady=5, fill="x")

        ttk.Label(filter_mov_frame, text="De:").grid(row=0, column=0, sticky="w", padx=2, pady=2) # REMOVIDO background='white'
        self.data_inicio_mov_entry = ttk.Entry(filter_mov_frame, textvariable=self.data_inicio_mov_var, width=12)
        self.data_inicio_mov_entry.grid(row=0, column=1, sticky="ew", padx=2, pady=2)
        
        ttk.Label(filter_mov_frame, text="Até:").grid(row=0, column=2, sticky="w", padx=2, pady=2) # REMOVIDO background='white'
        self.data_fim_mov_entry = ttk.Entry(filter_mov_frame, textvariable=self.data_fim_mov_var, width=12)
        self.data_fim_mov_entry.grid(row=0, column=3, sticky="ew", padx=2, pady=2)
        self.data_fim_mov_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ttk.Label(filter_mov_frame, text="Tipo:").grid(row=1, column=0, sticky="w", padx=5, pady=2) # REMOVIDO background='white'
        self.filter_tipo_mov_menu = ttk.OptionMenu(filter_mov_frame, self.filter_tipo_mov_var, self.tipos_movimentacao_options[0], *self.tipos_movimentacao_options)
        self.filter_tipo_mov_menu.grid(row=1, column=1, sticky="ew", padx=2, pady=2)
        
        ttk.Button(filter_mov_frame, text="Filtrar", command=self.load_historico_movimentacoes).grid(row=1, column=2, columnspan=2, padx=10, sticky="ew")

        columns = ("ID Mov.", "Data/Hora", "Produto", "SKU", "Tipo", "Quantidade", "Custo Unit. Mov.", "Motivo")
        self.historico_mov_tree = ttk.Treeview(parent_frame, columns=columns, show="headings", selectmode="browse")

        for col in columns:
            self.historico_mov_tree.heading(col, text=col)
            if col == "ID Mov.":
                self.historico_mov_tree.column(col, width=60, anchor="center")
            elif col == "Data/Hora":
                self.historico_mov_tree.column(col, width=120, anchor="center")
            elif col == "Produto":
                self.historico_mov_tree.column(col, width=180, anchor="w")
            elif col == "SKU":
                self.historico_mov_tree.column(col, width=80, anchor="center")
            elif col == "Tipo":
                self.historico_mov_tree.column(col, width=70, anchor="center")
            elif col == "Quantidade":
                self.historico_mov_tree.column(col, width=80, anchor="center")
            elif col == "Custo Unit. Mov.":
                self.historico_mov_tree.column(col, width=110, anchor="e")
            elif col == "Motivo":
                self.historico_mov_tree.column(col, width=150, anchor="w")

        self.historico_mov_tree.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=self.historico_mov_tree.yview)
        self.historico_mov_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    def load_historico_movimentacoes(self):
        for item in self.historico_mov_tree.get_children():
            self.historico_mov_tree.delete(item)
        
        conn = self.get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                m.id, m.data_hora, p.nome, p.sku, m.tipo_movimentacao, m.quantidade, m.custo_unitario_movimentacao, m.motivo
            FROM movimentacoes_estoque m
            JOIN produtos p ON m.produto_id = p.id
            WHERE 1=1
        """
        params = []

        data_inicio = self.data_inicio_mov_var.get()
        data_fim = self.data_fim_mov_var.get()
        tipo_mov_filtro = self.filter_tipo_mov_var.get()

        if data_inicio:
            query += " AND DATE(m.data_hora) >= DATE(?)"
            params.append(data_inicio)
        if data_fim:
            query += " AND DATE(m.data_hora) <= DATE(?)"
            params.append(data_fim)
        if tipo_mov_filtro != "Todos":
            query += " AND m.tipo_movimentacao = ?"
            params.append(tipo_mov_filtro)

        query += " ORDER BY m.data_hora DESC"
        
        cursor.execute(query, tuple(params))
        movimentacoes = cursor.fetchall()
        conn.close()

        for mov in movimentacoes:
            self.historico_mov_tree.insert("", "end", values=(
                mov['id'],
                mov['data_hora'],
                mov['tipo_movimentacao'],
                mov['quantidade'],
                f"R$ {mov['custo_unitario_movimentacao']:.2f}" if mov['custo_unitario_movimentacao'] is not None else "N/A",
                mov['motivo']
            ))

    def fill_default_if_empty(self, string_var, default_value):
        if not string_var.get().strip():
            string_var.set(default_value)

    def format_currency_input(self, text_input):
        clean_text = ''.join(filter(lambda x: x.isdigit() or x in ['.', ','], text_input))
        clean_text = clean_text.replace(',', '.')

        if clean_text.count('.') > 1:
            parts = clean_text.split('.')
            clean_text = parts[0] + '.' + ''.join(parts[1:])

        if '.' in clean_text:
            integer_part, decimal_part = clean_text.split('.')
            clean_text = integer_part + '.' + decimal_part[:2]

        if clean_text.startswith('0') and len(clean_text) > 1 and clean_text[1].isdigit():
            if '.' not in clean_text:
                clean_text = clean_text.lstrip('0') or '0'
            elif clean_text.index('.') > 1:
                 clean_text = clean_text.lstrip('0')
                 if clean_text.startswith('.'):
                     clean_text = '0' + clean_text
        if not clean_text:
            return ""
        return clean_text

    def format_integer_input(self, text_input):
        clean_text = ''.join(filter(str.isdigit, text_input))
        if clean_text.startswith('0') and len(clean_text) > 1:
            clean_text = clean_text.lstrip('0') or '0'
        return clean_text