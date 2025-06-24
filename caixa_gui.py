import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from database import DATABASE_NAME
from datetime import datetime, date

class CaixaGUI(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding="15")
        self.master = master
        self.conn = self.get_db_connection()

        # Variáveis de controle para Abertura/Fechamento e Movimentações
        self.abertura_caixa_data_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.saldo_inicial_var = tk.StringVar(value="0.00")
        self.selected_responsavel_var = tk.StringVar(value="-- Selecione o Vendedor --")
        
        # Variáveis de Movimentação de Caixa
        self.mov_tipo_var = tk.StringVar(value="Entrada")
        self.mov_valor_var = tk.StringVar(value="0.00")
        self.mov_forma_pgto_var = tk.StringVar(value="Dinheiro")
        self.mov_descricao_var = tk.StringVar(value="")
        self.selected_vendedor_caixa_var = tk.StringVar(value="-- Selecione o Vendedor --")


        # Variáveis de Filtro do Histórico de Caixa
        self.filter_data_inicio_caixa_var = tk.StringVar(value=(datetime.now().replace(day=1)).strftime("%Y-%m-%d"))
        self.filter_data_fim_caixa_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.filter_tipo_mov_caixa_var = tk.StringVar(value="Todos")
        self.filter_forma_pgto_caixa_var = tk.StringVar(value="Todas")


        # Listas de Opções
        self.formas_pagamento_caixa_options = ["Dinheiro", "Cartao", "Pix", "Recebimento Parcela", "Outros"]
        self.tipos_movimentacao_caixa_options = ["Entrada", "Saida"]
        self.filter_tipos_mov_caixa_options_dropdown = ["Todos"] + self.tipos_movimentacao_caixa_options
        self.filter_formas_pgto_caixa_options_dropdown = ["Todas"] + self.formas_pagamento_caixa_options


        self.vendedores_dict = {}
        self.vendedor_nomes_for_dropdown = ["-- Selecione o Vendedor --"]

        self.create_widgets()
        self._load_vendedores_for_dropdown()
        self.load_movimentacoes_caixa()

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

        self.vendedores_dict = {"-- Selecione o Vendedor --": None}
        self.vendedor_nomes_for_dropdown = ["-- Selecione o Vendedor --"]
        for v in vendedores_db:
            self.vendedores_dict[v['nome']] = v['id']
            self.vendedor_nomes_for_dropdown.append(v['nome'])
        
        if hasattr(self, 'responsavel_menu') and self.responsavel_menu is not None:
            menu = self.responsavel_menu["menu"]
            menu.delete(0, "end")
            for nome in self.vendedor_nomes_for_dropdown:
                menu.add_command(label=nome, command=tk._setit(self.selected_responsavel_var, nome))
            self.selected_responsavel_var.set(self.vendedor_nomes_for_dropdown[0])
        
        if hasattr(self, 'vendedor_dropdown_caixa') and self.vendedor_dropdown_caixa is not None:
            menu = self.vendedor_dropdown_caixa["menu"]
            menu.delete(0, "end")
            for nome in self.vendedor_nomes_for_dropdown:
                menu.add_command(label=nome, command=tk._setit(self.selected_vendedor_caixa_var, nome))
            self.selected_vendedor_caixa_var.set(self.vendedor_nomes_for_dropdown[0])


    def create_widgets(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)

        self.tab_abertura_fechamento = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_abertura_fechamento, text="Abertura/Fechamento de Caixa")
        self.create_abertura_fechamento_widgets(self.tab_abertura_fechamento)

        self.tab_movimentacoes = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_movimentacoes, text="Movimentações do Dia")
        self.create_movimentacoes_widgets(self.tab_movimentacoes)


    def create_abertura_fechamento_widgets(self, parent_frame):
        abertura_frame = ttk.LabelFrame(parent_frame, text="Abertura de Caixa", padding="10")
        abertura_frame.pack(pady=10, padx=10, fill="x")

        ttk.Label(abertura_frame, text="Data do Caixa:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(abertura_frame, textvariable=self.abertura_caixa_data_var, width=15, state='readonly').grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(abertura_frame, text="Saldo Inicial:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(abertura_frame, textvariable=self.saldo_inicial_var, width=15).grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.saldo_inicial_var.trace_add("write", lambda n, i, m: self.saldo_inicial_var.set(self.format_currency_input(self.saldo_inicial_var.get())))
        
        ttk.Label(abertura_frame, text="Responsável:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.responsavel_menu = ttk.OptionMenu(abertura_frame, self.selected_responsavel_var, self.vendedor_nomes_for_dropdown[0], *self.vendedor_nomes_for_dropdown)
        self.responsavel_menu.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Button(abertura_frame, text="Registrar Abertura", command=self._registrar_abertura_caixa_click, style='Accent.TButton').grid(row=3, column=0, columnspan=2, pady=10)

        fechamento_frame = ttk.LabelFrame(parent_frame, text="Fechamento de Caixa", padding="10")
        fechamento_frame.pack(pady=10, padx=10, fill="x")

        self.saldo_final_calculado_label = ttk.Label(fechamento_frame, text="Saldo Final Calculado: R$ 0.00", font=("Arial", 12, "bold")).pack(pady=5, anchor="w")
        
        ttk.Button(fechamento_frame, text="Calcular Saldo Final", command=self.calcular_saldo_final).pack(pady=5)
        ttk.Button(fechamento_frame, text="Registrar Fechamento", command=self._registrar_fechamento_caixa_click, style='Danger.TButton').pack(pady=10)


    def create_movimentacoes_widgets(self, parent_frame):
        mov_registro_frame = ttk.LabelFrame(parent_frame, text="Registrar Movimentação", padding="10")
        mov_registro_frame.pack(pady=5, padx=5, fill="x")
        mov_registro_frame.columnconfigure(1, weight=1)

        ttk.Label(mov_registro_frame, text="Tipo:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Radiobutton(mov_registro_frame, text="Entrada", value="Entrada", variable=self.mov_tipo_var).grid(row=0, column=1, sticky="w", padx=5)
        ttk.Radiobutton(mov_registro_frame, text="Saída", value="Saida", variable=self.mov_tipo_var).grid(row=0, column=2, sticky="w", padx=5)

        ttk.Label(mov_registro_frame, text="Valor:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.valor_mov_caixa_entry = ttk.Entry(mov_registro_frame, textvariable=self.mov_valor_var, width=15)
        self.valor_mov_caixa_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        self.mov_valor_var.trace_add("write", lambda n, i, m: self.mov_valor_var.set(self.format_currency_input(self.mov_valor_var.get())))
        self.valor_mov_caixa_entry.bind("<FocusOut>", lambda event=None: self.fill_default_if_empty(self.mov_valor_var, "0.00"))


        ttk.Label(mov_registro_frame, text="Forma Pgto:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.forma_pgto_caixa_dropdown = ttk.OptionMenu(mov_registro_frame, self.mov_forma_pgto_var, self.formas_pagamento_caixa_options[0], *self.formas_pagamento_caixa_options)
        self.forma_pgto_caixa_dropdown.grid(row=2, column=1, columnspan=2, sticky="ew", padx=5, pady=2)

        ttk.Label(mov_registro_frame, text="Descrição:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.descricao_mov_caixa_entry = ttk.Entry(mov_registro_frame, textvariable=self.mov_descricao_var, width=50)
        self.descricao_mov_caixa_entry.grid(row=3, column=1, columnspan=2, sticky="ew", padx=5, pady=2)

        ttk.Label(mov_registro_frame, text="Vendedor (opc.):").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        self.vendedor_dropdown_caixa = ttk.OptionMenu(mov_registro_frame, self.selected_vendedor_caixa_var, self.vendedor_nomes_for_dropdown[0], *self.vendedor_nomes_for_dropdown)
        self.vendedor_dropdown_caixa.grid(row=4, column=1, columnspan=2, sticky="ew", padx=5, pady=2)

        ttk.Button(mov_registro_frame, text="Registrar Movimentação de Caixa", command=self.registrar_movimentacao_avulsa, style='Accent.TButton').grid(row=5, column=0, columnspan=3, pady=10)
        
        parent_frame.columnconfigure(1, weight=1)

        self.create_historico_caixa_widgets(parent_frame)
        self.load_movimentacoes_caixa()

    def _registrar_abertura_caixa_click(self):
        data_caixa = self.abertura_caixa_data_var.get()
        saldo_inicial_str = self.saldo_inicial_var.get().replace(',', '.')
        responsavel_nome = self.selected_responsavel_var.get()

        if responsavel_nome == "-- Selecione o Vendedor --":
            messagebox.showwarning("Aviso", "Por favor, selecione o vendedor responsável pela abertura.")
            return

        try:
            saldo_inicial = float(saldo_inicial_str)
            if saldo_inicial < 0: raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Saldo inicial inválido. Use um número positivo.")
            return

        responsavel_id = self.vendedores_dict.get(responsavel_nome)
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM movimentacoes_caixa WHERE tipo_movimentacao = 'Abertura' AND DATE(data_hora) = DATE(?)", (data_caixa,))
        if cursor.fetchone()[0] > 0:
            messagebox.showwarning("Aviso", f"Já existe uma abertura de caixa registrada para o dia {data_caixa}.")
            conn.close()
            return

        try:
            cursor.execute("INSERT INTO movimentacoes_caixa (data_hora, tipo_movimentacao, valor, descricao, responsavel_id) VALUES (?, ?, ?, ?, ?)",
                           (f"{data_caixa} {datetime.now().strftime('%H:%M:%S')}", "Abertura", saldo_inicial, "Abertura de Caixa", responsavel_id))
            conn.commit()
            messagebox.showinfo("Sucesso", f"Caixa aberto para {data_caixa} com saldo inicial de R$ {saldo_inicial:.2f}!")
            self.load_movimentacoes_caixa()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Erro", f"Erro ao registrar abertura de caixa: {e}")
        finally:
            conn.close()

    def _registrar_fechamento_caixa_click(self):
        data_hoje = datetime.now().strftime("%Y-%m-%d")
        conn = self.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM movimentacoes_caixa WHERE tipo_movimentacao = 'Fechamento' AND DATE(data_hora) = DATE(?)", (data_hoje,))
        if cursor.fetchone()[0] > 0:
            messagebox.showwarning("Aviso", f"Já existe um fechamento de caixa registrado para o dia {data_hoje}.")
            conn.close()
            return
        
        cursor.execute("SELECT COUNT(*) FROM movimentacoes_caixa WHERE tipo_movimentacao = 'Abertura' AND DATE(data_hora) = DATE(?)", (data_hoje,))
        if cursor.fetchone()[0] == 0:
            messagebox.showwarning("Aviso", f"Não há abertura de caixa registrada para o dia {data_hoje}. Por favor, registre a abertura antes de fechar.")
            conn.close()
            return

        saldo_final = self.calcular_saldo_final()
        responsavel_nome = self.selected_responsavel_var.get()
        responsavel_id = self.vendedores_dict.get(responsavel_nome)

        if messagebox.askyesno("Confirmar Fechamento", f"Confirmar fechamento de caixa para R$ {saldo_final:.2f} do dia {data_hoje}?"):
            try:
                cursor.execute("INSERT INTO movimentacoes_caixa (data_hora, tipo_movimentacao, valor, descricao, responsavel_id) VALUES (?, ?, ?, ?, ?)",
                               (f"{data_hoje} {datetime.now().strftime('%H:%M:%S')}", "Fechamento", saldo_final, "Fechamento de Caixa", responsavel_id))
                conn.commit()
                messagebox.showinfo("Sucesso", f"Caixa fechado para {data_hoje} com saldo final de R$ {saldo_final:.2f}!")
                self.load_movimentacoes_caixa()
            except Exception as e:
                conn.rollback()
                messagebox.showerror("Erro", f"Erro ao registrar fechamento de caixa: {e}")
            finally:
                conn.close()

    def calcular_saldo_final(self):
        data_hoje = datetime.now().strftime("%Y-%m-%d")
        conn = self.get_db_connection()
        cursor = conn.cursor()

        saldo_inicial = 0.0
        saldo_inicial_row = cursor.execute("SELECT valor FROM movimentacoes_caixa WHERE tipo_movimentacao = 'Abertura' AND DATE(data_hora) = DATE(?)", (data_hoje,)).fetchone()
        if saldo_inicial_row:
            saldo_inicial = saldo_inicial_row['valor']
        
        total_entradas = 0.0
        total_entradas_row = cursor.execute("SELECT SUM(valor) FROM movimentacoes_caixa WHERE tipo_movimentacao = 'Entrada' AND DATE(data_hora) = DATE(?)", (data_hoje,)).fetchone()
        if total_entradas_row and total_entradas_row[0] is not None:
            total_entradas = total_entradas_row[0]

        total_saidas = 0.0
        total_saidas_row = cursor.execute("SELECT SUM(valor) FROM movimentacoes_caixa WHERE tipo_movimentacao = 'Saida' AND DATE(data_hora) = DATE(?)", (data_hoje,)).fetchone()
        if total_saidas_row and total_saidas_row[0] is not None:
            total_saidas = total_saidas_row[0]
        
        conn.close()

        saldo_final_calculado = saldo_inicial + total_entradas - total_saidas
        self.saldo_final_calculado_label.config(text=f"Saldo Final Calculado: R$ {saldo_final_calculado:.2f}")
        return saldo_final_calculado

    def registrar_movimentacao_avulsa(self):
        tipo = self.mov_tipo_var.get()
        valor_str = self.mov_valor_var.get().replace(',', '.')
        forma_pgto = self.mov_forma_pgto_var.get()
        descricao = self.mov_descricao_var.get().strip()
        data_hora_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        responsavel_nome = self.selected_vendedor_caixa_var.get()
        responsavel_id = self.vendedores_dict.get(responsavel_nome)

        if responsavel_nome == "-- Selecione o Vendedor --":
             messagebox.showwarning("Aviso", "Por favor, selecione o vendedor responsável pela movimentação.")
             return
        
        if not descricao:
            messagebox.showwarning("Aviso", "Descrição da movimentação é obrigatória.")
            return

        try:
            valor = float(valor_str)
            if valor <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Valor inválido. Use um número positivo.")
            return

        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO movimentacoes_caixa (data_hora, tipo_movimentacao, valor, forma_pagamento, descricao, responsavel_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (data_hora_atual, tipo, valor, forma_pgto, descricao, responsavel_id))
            
            conn.commit()
            messagebox.showinfo("Sucesso", f"Movimentação de {tipo} de R$ {valor:.2f} registrada com sucesso!")
            self.clear_movimentacao_avulsa_form()
            self.load_movimentacoes_caixa()

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Erro", f"Erro ao registrar movimentação avulsa: {e}")
        finally:
            conn.close()

    def clear_movimentacao_avulsa_form(self):
        self.mov_tipo_var.set("Entrada")
        self.mov_valor_var.set("0.00")
        self.mov_forma_pgto_var.set(self.formas_pagamento_caixa_options[0])
        self.mov_descricao_var.set("")
        self.selected_vendedor_caixa_var.set("-- Selecione o Vendedor --")

    def create_historico_caixa_widgets(self, parent_frame):
        filter_frame = ttk.Frame(parent_frame, padding="5")
        filter_frame.pack(pady=5, fill="x")

        ttk.Label(filter_frame, text="De:").grid(row=0, column=0, sticky="w", padx=2, pady=2)
        self.data_inicio_caixa_entry = ttk.Entry(filter_frame, textvariable=self.filter_data_inicio_caixa_var, width=12)
        self.data_inicio_caixa_entry.grid(row=0, column=1, sticky="ew", padx=2, pady=2)
        
        ttk.Label(filter_frame, text="Até:").grid(row=0, column=2, sticky="w", padx=2, pady=2)
        self.data_fim_caixa_entry = ttk.Entry(filter_frame, textvariable=self.filter_data_fim_caixa_var, width=12)
        self.data_fim_caixa_entry.grid(row=0, column=3, sticky="ew", padx=2, pady=2)

        ttk.Label(filter_frame, text="Tipo:").grid(row=1, column=0, sticky="w", padx=2, pady=2)
        self.filter_tipo_mov_caixa_dropdown = ttk.OptionMenu(filter_frame, self.filter_tipo_mov_caixa_var, self.filter_tipos_mov_caixa_options_dropdown[0], *self.filter_tipos_mov_caixa_options_dropdown)
        self.filter_tipo_mov_caixa_dropdown.grid(row=1, column=1, sticky="ew", padx=2, pady=2)

        ttk.Label(filter_frame, text="Forma Pgto:").grid(row=1, column=2, sticky="w", padx=2, pady=2)
        self.filter_forma_pgto_caixa_dropdown = ttk.OptionMenu(filter_frame, self.filter_forma_pgto_caixa_var, self.filter_formas_pgto_caixa_options_dropdown[0], *self.filter_formas_pgto_caixa_options_dropdown)
        self.filter_forma_pgto_caixa_dropdown.grid(row=1, column=3, sticky="ew", padx=2, pady=2)
        
        ttk.Button(filter_frame, text="Filtrar", command=self.load_movimentacoes_caixa).grid(row=0, column=4, rowspan=2, padx=10, sticky="ns")

        columns = ("ID", "Data/Hora", "Tipo", "Valor", "Forma de Pgto", "Descrição", "Vendedor")
        self.caixa_tree = ttk.Treeview(parent_frame, columns=columns, show="headings", selectmode="browse")

        for col in columns:
            self.caixa_tree.heading(col, text=col)
            if col == "ID":
                self.caixa_tree.column(col, width=50, anchor="center")
            elif col == "Data/Hora":
                self.caixa_tree.column(col, width=120, anchor="center")
            elif col == "Tipo":
                self.caixa_tree.column(col, width=70, anchor="center")
            elif col == "Valor":
                self.caixa_tree.column(col, width=90, anchor="e")
            elif col == "Forma de Pgto":
                self.caixa_tree.column(col, width=90, anchor="center")
            elif col == "Descrição":
                self.caixa_tree.column(col, width=200, anchor="w")
            elif col == "Vendedor":
                self.caixa_tree.column(col, width=100, anchor="w")

        self.caixa_tree.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=self.caixa_tree.yview)
        self.caixa_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.resumo_caixa_label = ttk.Label(parent_frame, text="Saldo do Período: R$ 0.00", font=("Arial", 12, "bold"))
        self.resumo_caixa_label.pack(pady=10, fill="x")

    def load_movimentacoes_caixa(self):
        for item in self.caixa_tree.get_children():
            self.caixa_tree.delete(item)
        
        data_inicio_filtro = self.filter_data_inicio_caixa_var.get()
        data_fim_filtro = self.filter_data_fim_caixa_var.get()
        tipo_mov_filtro = self.filter_tipo_mov_caixa_var.get()
        forma_pgto_filtro = self.filter_forma_pgto_caixa_var.get()

        conn = self.get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT mc.id, mc.data_hora, mc.tipo_movimentacao, mc.valor, mc.forma_pagamento, mc.descricao, v.nome AS vendedor_nome
            FROM movimentacoes_caixa mc
            LEFT JOIN vendedores v ON mc.responsavel_id = v.id
            WHERE 1=1
        """
        params = []

        if data_inicio_filtro:
            query += " AND DATE(mc.data_hora) >= DATE(?)"
            params.append(data_inicio_filtro)
        if data_fim_filtro:
            query += " AND DATE(mc.data_hora) <= DATE(?)"
            params.append(data_fim_filtro)
        if tipo_mov_filtro != "Todos":
            query += " AND mc.tipo_movimentacao = ?"
            params.append(tipo_mov_filtro)
        if forma_pgto_filtro != "Todas":
            query += " AND mc.forma_pagamento = ?"
            params.append(forma_pgto_filtro)

        query += " ORDER BY mc.data_hora DESC"
        
        cursor.execute(query, tuple(params))
        movimentacoes = cursor.fetchall()
        conn.close()

        saldo_periodo = 0.0
        for mov in movimentacoes:
            if mov['tipo_movimentacao'] == "Entrada":
                saldo_periodo += mov['valor']
            elif mov['tipo_movimentacao'] == "Saida":
                saldo_periodo -= mov['valor']
            
            self.caixa_tree.insert("", "end", values=(
                mov['id'],
                mov['data_hora'],
                mov['tipo_movimentacao'],
                f"R$ {mov['valor']:.2f}",
                mov['forma_pagamento'],
                mov['descricao'],
                mov['vendedor_nome'] if mov['vendedor_nome'] else "N/A"
            ))
        
        self.resumo_caixa_label.config(text=f"Saldo do Período: R$ {saldo_periodo:.2f}")

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

    def fill_default_if_empty(self, string_var, default_value):
        if not string_var.get().strip():
            string_var.set(default_value)