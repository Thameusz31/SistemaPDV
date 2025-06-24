import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from database import DATABASE_NAME
from datetime import datetime, date # Importe date também

class CaixaGUI(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding="15")
        self.master = master
        self.conn = self.get_db_connection()

        # Variáveis de controle para Abertura/Fechamento e Movimentações
        self.abertura_caixa_data_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.saldo_inicial_var = tk.StringVar(value="0.00")
        self.selected_responsavel_var = tk.StringVar(value="-- Selecione o Vendedor --")
        
        self.mov_tipo_var = tk.StringVar(value="Entrada")
        self.mov_valor_var = tk.StringVar(value="0.00")
        self.mov_forma_pgto_var = tk.StringVar(value="Dinheiro")
        self.mov_descricao_var = tk.StringVar(value="")

        self.formas_pagamento_caixa_options = ["Dinheiro", "Cartao", "Pix", "Recebimento Parcela", "Outros"] # Formas para entradas/saídas avulsas
        self.tipos_movimentacao_options = ["Entrada", "Saida"]
        
        self.vendedores_dict = {} # Preenchido em _load_vendedores_for_dropdown

        self.create_widgets()
        self._load_vendedores_for_dropdown() # Carrega vendedores para o dropdown
        self.load_movimentacoes_caixa() # Carrega as movimentações iniciais

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

        vendedor_nomes = ["-- Selecione o Vendedor --"]
        for v in vendedores_db:
            self.vendedores_dict[v['nome']] = v['id']
            vendedor_nomes.append(v['nome'])
        
        # Atualiza o OptionMenu de seleção de responsável
        if hasattr(self, 'responsavel_menu') and self.responsavel_menu is not None:
            menu = self.responsavel_menu["menu"]
            menu.delete(0, "end")
            for nome in vendedor_nomes:
                menu.add_command(label=nome, command=tk._setit(self.selected_responsavel_var, nome))
            self.selected_responsavel_var.set(vendedor_nomes[0])
        else: # Se o menu ainda não foi criado (primeira execução)
            pass # Será criado em create_widgets


    def create_widgets(self):
        # Notebook (abas) para Abertura/Fechamento e Movimentações/Histórico
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)

        self.tab_abertura_fechamento = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_abertura_fechamento, text="Abertura/Fechamento de Caixa")
        self.create_abertura_fechamento_widgets(self.tab_abertura_fechamento)

        self.tab_movimentacoes = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_movimentacoes, text="Movimentações do Dia")
        self.create_movimentacoes_widgets(self.tab_movimentacoes)


    def create_abertura_fechamento_widgets(self, parent_frame):
        # Frame de Abertura de Caixa
        abertura_frame = ttk.LabelFrame(parent_frame, text="Abertura de Caixa", padding="10")
        abertura_frame.pack(pady=10, padx=10, fill="x")

        ttk.Label(abertura_frame, text="Data do Caixa:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(abertura_frame, textvariable=self.abertura_caixa_data_var, width=15, state='readonly').grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(abertura_frame, text="Saldo Inicial:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(abertura_frame, textvariable=self.saldo_inicial_var, width=15).grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.saldo_inicial_var.trace_add("write", lambda n, i, m: self.saldo_inicial_var.set(self.format_currency_input(self.saldo_inicial_var.get())))
        
        ttk.Label(abertura_frame, text="Responsável:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.responsavel_menu = ttk.OptionMenu(abertura_frame, self.selected_responsavel_var, self.selected_responsavel_var.get(), *self.vendedores_dict.keys())
        self.responsavel_menu.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Button(abertura_frame, text="Registrar Abertura", command=self.registrar_abertura_caixa, style='Accent.TButton').grid(row=3, column=0, columnspan=2, pady=10)

        # Frame de Fechamento de Caixa
        fechamento_frame = ttk.LabelFrame(parent_frame, text="Fechamento de Caixa", padding="10")
        fechamento_frame.pack(pady=10, padx=10, fill="x")

        self.saldo_final_calculado_label = ttk.Label(fechamento_frame, text="Saldo Final Calculado: R$ 0.00", font=("Arial", 12, "bold"))
        self.saldo_final_calculado_label.pack(pady=5, anchor="w")
        
        ttk.Button(fechamento_frame, text="Calcular Saldo Final", command=self.calcular_saldo_final).pack(pady=5)
        ttk.Button(fechamento_frame, text="Registrar Fechamento", command=self.registrar_fechamento_caixa, style='Danger.TButton').pack(pady=10)


    def create_movimentacoes_widgets(self, parent_frame):
        # Frame para registrar novas movimentações (Entrada/Saída Avulsa)
        mov_registro_frame = ttk.LabelFrame(parent_frame, text="Registrar Movimentação", padding="10")
        mov_registro_frame.pack(pady=5, padx=5, fill="x")
        mov_registro_frame.columnconfigure(1, weight=1)

        ttk.Label(mov_registro_frame, text="Tipo:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Radiobutton(mov_registro_frame, text="Entrada", value="Entrada", variable=self.mov_tipo_var).grid(row=0, column=1, sticky="w", padx=5)
        ttk.Radiobutton(mov_registro_frame, text="Saída", value="Saida", variable=self.mov_tipo_var).grid(row=0, column=2, sticky="w", padx=5)

        ttk.Label(mov_registro_frame, text="Valor:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(mov_registro_frame, textvariable=self.mov_valor_var, width=15).grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        self.mov_valor_var.trace_add("write", lambda n, i, m: self.mov_valor_var.set(self.format_currency_input(self.mov_valor_var.get())))

        ttk.Label(mov_registro_frame, text="Forma Pgto:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        ttk.OptionMenu(mov_registro_frame, self.mov_forma_pgto_var, self.formas_pagamento_caixa_options[0], *self.formas_pagamento_caixa_options).grid(row=2, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(mov_registro_frame, text="Descrição:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(mov_registro_frame, textvariable=self.mov_descricao_var, width=50).grid(row=3, column=1, columnspan=2, sticky="ew", padx=5, pady=2)

        ttk.Button(mov_registro_frame, text="Registrar Movimentação", command=self.registrar_movimentacao_avulsa, style='Accent.TButton').grid(row=4, column=0, columnspan=3, pady=10)

        # Frame para histórico de movimentações do dia
        historico_mov_frame = ttk.LabelFrame(parent_frame, text="Histórico do Dia", padding="10")
        historico_mov_frame.pack(pady=5, padx=5, fill="both", expand=True)

        columns = ("ID", "Data/Hora", "Tipo", "Valor", "Forma Pgto", "Descrição", "Responsável")
        self.mov_caixa_tree = ttk.Treeview(historico_mov_frame, columns=columns, show="headings", selectmode="browse")

        for col in columns:
            self.mov_caixa_tree.heading(col, text=col)
            if col == "ID": self.mov_caixa_tree.column(col, width=50, anchor="center")
            elif col == "Data/Hora": self.mov_caixa_tree.column(col, width=120, anchor="center")
            elif col == "Tipo": self.mov_caixa_tree.column(col, width=70, anchor="center")
            elif col == "Valor": self.mov_caixa_tree.column(col, width=90, anchor="e")
            elif col == "Forma Pgto": self.mov_caixa_tree.column(col, width=90, anchor="center")
            elif col == "Descrição": self.mov_caixa_tree.column(col, width=200, anchor="w")
            elif col == "Responsável": self.mov_caixa_tree.column(col, width=100, anchor="w")

        self.mov_caixa_tree.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(historico_mov_frame, orient="vertical", command=self.mov_caixa_tree.yview)
        self.mov_caixa_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    def registrar_abertura_caixa(self):
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

        responsavel_id = self.vendedores_dict[responsavel_nome]
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se já existe uma abertura para o dia
        cursor.execute("SELECT COUNT(*) FROM movimentacoes_caixa WHERE tipo = 'Abertura' AND DATE(data_hora) = DATE(?)", (data_caixa,))
        if cursor.fetchone()[0] > 0:
            messagebox.showwarning("Aviso", f"Já existe uma abertura de caixa registrada para o dia {data_caixa}.")
            conn.close()
            return

        try:
            cursor.execute("INSERT INTO movimentacoes_caixa (data_hora, tipo, valor, descricao, responsavel_id) VALUES (?, ?, ?, ?, ?)",
                           (f"{data_caixa} {datetime.now().strftime('%H:%M:%S')}", "Abertura", saldo_inicial, "Abertura de Caixa", responsavel_id))
            conn.commit()
            messagebox.showinfo("Sucesso", f"Caixa aberto para {data_caixa} com saldo inicial de R$ {saldo_inicial:.2f}!")
            self.load_movimentacoes_caixa()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Erro", f"Erro ao registrar abertura de caixa: {e}")
        finally:
            conn.close()

    def calcular_saldo_final(self):
        data_hoje = datetime.now().strftime("%Y-%m-%d")
        conn = self.get_db_connection()
        cursor = conn.cursor()

        # Saldo inicial
        cursor.execute("SELECT valor FROM movimentacoes_caixa WHERE tipo = 'Abertura' AND DATE(data_hora) = DATE(?)", (data_hoje,))
        saldo_inicial_row = cursor.fetchone()
        saldo_inicial = saldo_inicial_row['valor'] if saldo_inicial_row else 0.0

        # Total de entradas (exceto abertura)
        cursor.execute("SELECT SUM(valor) FROM movimentacoes_caixa WHERE tipo = 'Entrada' AND DATE(data_hora) = DATE(?)", (data_hoje,))
        total_entradas_row = cursor.fetchone()
        total_entradas = total_entradas_row[0] if total_entradas_row and total_entradas_row[0] is not None else 0.0

        # Total de saídas
        cursor.execute("SELECT SUM(valor) FROM movimentacoes_caixa WHERE tipo = 'Saida' AND DATE(data_hora) = DATE(?)", (data_hoje,))
        total_saidas_row = cursor.fetchone()
        total_saidas = total_saidas_row[0] if total_saidas_row and total_saidas_row[0] is not None else 0.0
        conn.close()

        saldo_final_calculado = saldo_inicial + total_entradas - total_saidas
        self.saldo_final_calculado_label.config(text=f"Saldo Final Calculado: R$ {saldo_final_calculado:.2f}")
        return saldo_final_calculado

    def registrar_fechamento_caixa(self):
        data_hoje = datetime.now().strftime("%Y-%m-%d")
        conn = self.get_db_connection()
        cursor = conn.cursor()

        # Verificar se já existe um fechamento para o dia
        cursor.execute("SELECT COUNT(*) FROM movimentacoes_caixa WHERE tipo = 'Fechamento' AND DATE(data_hora) = DATE(?)", (data_hoje,))
        if cursor.fetchone()[0] > 0:
            messagebox.showwarning("Aviso", f"Já existe um fechamento de caixa registrado para o dia {data_hoje}.")
            conn.close()
            return
        
        # Verificar se há uma abertura de caixa para o dia
        cursor.execute("SELECT COUNT(*) FROM movimentacoes_caixa WHERE tipo = 'Abertura' AND DATE(data_hora) = DATE(?)", (data_hoje,))
        if cursor.fetchone()[0] == 0:
            messagebox.showwarning("Aviso", f"Não há abertura de caixa registrada para o dia {data_hoje}. Por favor, registre a abertura antes de fechar.")
            conn.close()
            return

        saldo_final = self.calcular_saldo_final()
        responsavel_nome = self.selected_responsavel_var.get()
        responsavel_id = self.vendedores_dict.get(responsavel_nome)

        if messagebox.askyesno("Confirmar Fechamento", f"Confirmar fechamento de caixa para R$ {saldo_final:.2f} do dia {data_hoje}?"):
            try:
                cursor.execute("INSERT INTO movimentacoes_caixa (data_hora, tipo, valor, descricao, responsavel_id) VALUES (?, ?, ?, ?, ?)",
                               (f"{data_hoje} {datetime.now().strftime('%H:%M:%S')}", "Fechamento", saldo_final, "Fechamento de Caixa", responsavel_id))
                conn.commit()
                messagebox.showinfo("Sucesso", f"Caixa fechado para {data_hoje} com saldo final de R$ {saldo_final:.2f}!")
                self.load_movimentacoes_caixa()
            except Exception as e:
                conn.rollback()
                messagebox.showerror("Erro", f"Erro ao registrar fechamento de caixa: {e}")
            finally:
                conn.close()

    def registrar_movimentacao_avulsa(self):
        tipo = self.mov_tipo_var.get()
        valor_str = self.mov_valor_var.get().replace(',', '.')
        forma_pgto = self.mov_forma_pgto_var.get()
        descricao = self.mov_descricao_var.get().strip()
        data_hora_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        responsavel_nome = self.selected_responsavel_var.get()
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
            cursor.execute("INSERT INTO movimentacoes_caixa (data_hora, tipo, valor, forma_pagamento, descricao, responsavel_id) VALUES (?, ?, ?, ?, ?, ?)",
                           (data_hora_atual, tipo, valor, forma_pgto, descricao, responsavel_id))
            conn.commit()
            messagebox.showinfo("Sucesso", f"Movimentação de {tipo} de R$ {valor:.2f} registrada com sucesso!")
            self.clear_movimentacao_avulsa_form()
            self.load_movimentacoes_caixa() # Atualiza histórico
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Erro", f"Erro ao registrar movimentação avulsa: {e}")
        finally:
            conn.close()

    def clear_movimentacao_avulsa_form(self):
        self.mov_tipo_var.set("Entrada")
        self.mov_valor_var.set("0.00")
        self.mov_forma_pgto_var.set("Dinheiro")
        self.mov_descricao_var.set("")
        # Não reseta o vendedor pois ele pode ser o mesmo para várias operações.

    def load_movimentacoes_caixa(self):
        for item in self.mov_caixa_tree.get_children():
            self.mov_caixa_tree.delete(item)
        
        data_hoje = datetime.now().strftime("%Y-%m-%d")
        conn = self.get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT mc.id, mc.data_hora, mc.tipo, mc.valor, mc.forma_pagamento, mc.descricao, v.nome as responsavel_nome
            FROM movimentacoes_caixa mc
            LEFT JOIN vendedores v ON mc.responsavel_id = v.id
            WHERE DATE(mc.data_hora) = DATE(?)
            ORDER BY mc.data_hora ASC
        """
        cursor.execute(query, (data_hoje,))
        movimentacoes = cursor.fetchall()
        conn.close()

        for mov in movimentacoes:
            responsavel_nome_exibicao = mov['responsavel_nome'] if mov['responsavel_nome'] else "N/A"
            forma_pgto_exibicao = mov['forma_pagamento'] if mov['forma_pagamento'] else "N/A"
            self.mov_caixa_tree.insert("", "end", values=(
                mov['id'],
                mov['data_hora'],
                mov['tipo'],
                f"R$ {mov['valor']:.2f}",
                forma_pgto_exibicao,
                mov['descricao'],
                responsavel_nome_exibicao
            ))
        
        self.calcular_saldo_final() # Recalcula o saldo final ao carregar as movimentações

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