import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from database import DATABASE_NAME
from datetime import datetime, timedelta

class RelatoriosGUI(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding="15")
        self.master = master
        self.conn = self.get_db_connection()

        # Variáveis para filtros
        self.data_inicio_var = tk.StringVar(value=(datetime.now().replace(day=1)).strftime("%Y-%m-%d"))
        self.data_fim_var = tk.StringVar(value=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")) # Termina amanhã para incluir hoje
        self.filter_vendedor_var = tk.StringVar(value="Todos")
        self.filter_cliente_var = tk.StringVar(value="Todos")
        self.filter_pagamento_var = tk.StringVar(value="Todos")
        self.filter_tipo_cartao_var = tk.StringVar(value="Todos")

        # Listas de opções
        self.filter_pagamento_options = ["Todos", "Dinheiro", "Cartao", "Pix", "A Prazo"]
        self.filter_tipo_cartao_options = ["Todos", "Crédito", "Débito", "N/A"]

        self._load_vendedores_clientes_for_filters() # Carrega vendedores e clientes para os dropdowns

        self.create_widgets()
        self.load_relatorio_vendas() # Carrega o relatório inicial

    def get_db_connection(self):
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row
        return conn

    def _load_vendedores_clientes_for_filters(self):
        self.vendedores_dict = {}
        self.clientes_dict = {}

        conn = self.get_db_connection()
        cursor = conn.cursor()

        # Vendedores
        cursor.execute("SELECT id, nome FROM vendedores ORDER BY nome")
        vendedores_db = cursor.fetchall()
        self.vendedor_nomes_for_filter = ["Todos"]
        for v in vendedores_db:
            self.vendedores_dict[v['nome']] = v['id']
            self.vendedor_nomes_for_filter.append(v['nome'])

        # Atualiza o OptionMenu de vendedor no filtro (se já existe)
        if hasattr(self, 'vendedor_menu') and self.vendedor_menu is not None:
            menu_vendedor = self.vendedor_menu["menu"]
            menu_vendedor.delete(0, "end")
            for nome in self.vendedor_nomes_for_filter:
                menu_vendedor.add_command(label=nome, command=tk._setit(self.filter_vendedor_var, nome))
            self.filter_vendedor_var.set(self.vendedor_nomes_for_filter[0])


        # Clientes
        cursor.execute("SELECT id, nome FROM clientes ORDER BY nome")
        clientes_db = cursor.fetchall()
        self.cliente_nomes_for_filter = ["Todos"]
        for c in clientes_db:
            self.clientes_dict[c['nome']] = c['id']
            self.cliente_nomes_for_filter.append(c['nome'])
        
        conn.close()

        # Atualiza o OptionMenu de cliente no filtro (se já existe)
        if hasattr(self, 'cliente_menu') and self.cliente_menu is not None:
            menu_cliente = self.cliente_menu["menu"]
            menu_cliente.delete(0, "end")
            for nome in self.cliente_nomes_for_filter:
                menu_cliente.add_command(label=nome, command=tk._setit(self.filter_cliente_var, nome))
            self.filter_cliente_var.set(self.cliente_nomes_for_filter[0])


    def create_widgets(self):
        # Frame de filtros
        filter_frame = ttk.LabelFrame(self, text="Filtros do Relatório", padding="10")
        filter_frame.pack(pady=10, padx=10, fill="x")
        filter_frame.columnconfigure(1, weight=1)
        filter_frame.columnconfigure(3, weight=1)
        filter_frame.columnconfigure(5, weight=1)
        filter_frame.columnconfigure(7, weight=1) # Coluna extra para Tipo Cartão

        # Data Início
        ttk.Label(filter_frame, text="Data Início:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.data_inicio_entry = ttk.Entry(filter_frame, textvariable=self.data_inicio_var, width=15)
        self.data_inicio_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Data Fim
        ttk.Label(filter_frame, text="Data Fim:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.data_fim_entry = ttk.Entry(filter_frame, textvariable=self.data_fim_var, width=15)
        self.data_fim_entry.grid(row=0, column=3, sticky="ew", padx=5, pady=5)

        # Vendedor
        ttk.Label(filter_frame, text="Vendedor:").grid(row=0, column=4, sticky="w", padx=5, pady=5)
        # self.vendedor_nomes_for_filter já existe do _load_vendedores_clientes_for_filters
        self.vendedor_menu = ttk.OptionMenu(filter_frame, self.filter_vendedor_var, self.vendedor_nomes_for_filter[0], *self.vendedor_nomes_for_filter)
        self.vendedor_menu.grid(row=0, column=5, sticky="ew", padx=5, pady=5)

        # Cliente
        ttk.Label(filter_frame, text="Cliente:").grid(row=0, column=6, sticky="w", padx=5, pady=5)
        # self.cliente_nomes_for_filter já existe do _load_vendedores_clientes_for_filters
        self.cliente_menu = ttk.OptionMenu(filter_frame, self.filter_cliente_var, self.cliente_nomes_for_filter[0], *self.cliente_nomes_for_filter)
        self.cliente_menu.grid(row=0, column=7, sticky="ew", padx=5, pady=5)

        # Forma de Pagamento
        ttk.Label(filter_frame, text="Forma Pgto:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.pagamento_menu = ttk.OptionMenu(filter_frame, self.filter_pagamento_var, self.filter_pagamento_options[0], *self.filter_pagamento_options)
        self.pagamento_menu.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        # Tipo de Cartão
        ttk.Label(filter_frame, text="Tipo Cartão:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.tipo_cartao_menu = ttk.OptionMenu(filter_frame, self.filter_tipo_cartao_var, self.filter_tipo_cartao_options[0], *self.filter_tipo_cartao_options)
        self.tipo_cartao_menu.grid(row=1, column=3, sticky="ew", padx=5, pady=5)

        # Botão Filtrar
        ttk.Button(filter_frame, text="Gerar Relatório", command=self.load_relatorio_vendas, style='Accent.TButton').grid(row=1, column=4, columnspan=4, pady=10)

        # Frame da Treeview (Tabela de Vendas)
        vendas_frame = ttk.LabelFrame(self, text="Vendas Detalhadas", padding="10")
        vendas_frame.pack(pady=10, padx=10, fill="both", expand=True)

        columns = ("ID Venda", "Data/Hora", "Total Bruto", "Desconto", "Juros", "Pontos Utilizados", "Total Final", "Forma Pgto", "Tipo Cartão", "Parcelas", "Vendedor", "Cliente")
        self.vendas_tree = ttk.Treeview(vendas_frame, columns=columns, show="headings", selectmode="browse")

        for col in columns:
            self.vendas_tree.heading(col, text=col)
            if col in ["ID Venda", "Pontos Utilizados", "Parcelas"]:
                self.vendas_tree.column(col, width=70, anchor="center")
            elif col == "Data/Hora":
                self.vendas_tree.column(col, width=130, anchor="center")
            elif col in ["Total Bruto", "Desconto", "Juros", "Total Final"]:
                self.vendas_tree.column(col, width=100, anchor="e")
            elif col in ["Forma Pgto", "Tipo Cartão"]:
                self.vendas_tree.column(col, width=90, anchor="center")
            elif col in ["Vendedor", "Cliente"]:
                self.vendas_tree.column(col, width=120, anchor="w")
            else:
                self.vendas_tree.column(col, width=80, anchor="center")

        self.vendas_tree.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(vendas_frame, orient="vertical", command=self.vendas_tree.yview)
        self.vendas_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # Binding para clique direito para ver detalhes da venda
        self.vendas_tree.bind("<Button-3>", self.on_right_click_tree) # Botão direito

        # Frame de Totais Resumidos
        summary_frame = ttk.LabelFrame(self, text="Totais do Período", padding="10")
        summary_frame.pack(pady=10, padx=10, fill="x")
        summary_frame.columnconfigure(0, weight=1)
        summary_frame.columnconfigure(1, weight=1)
        summary_frame.columnconfigure(2, weight=1)
        summary_frame.columnconfigure(3, weight=1)

        self.total_vendas_label = ttk.Label(summary_frame, text="Total Bruto de Vendas: R$ 0.00", font=("Arial", 11, "bold"))
        self.total_vendas_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)

        self.total_descontos_label = ttk.Label(summary_frame, text="Total de Descontos: R$ 0.00", font=("Arial", 11, "bold"))
        self.total_descontos_label.grid(row=0, column=1, sticky="w", padx=5, pady=2)

        self.total_juros_label = ttk.Label(summary_frame, text="Total de Juros: R$ 0.00", font=("Arial", 11, "bold"))
        self.total_juros_label.grid(row=0, column=2, sticky="w", padx=5, pady=2)

        self.total_pontos_utilizados_label = ttk.Label(summary_frame, text="Total Pontos Utilizados: 0", font=("Arial", 11, "bold"))
        self.total_pontos_utilizados_label.grid(row=0, column=3, sticky="w", padx=5, pady=2)

        self.total_final_label = ttk.Label(summary_frame, text="TOTAL LÍQUIDO ARRECADADO: R$ 0.00", font=("Arial", 14, "bold"), foreground="green")
        self.total_final_label.grid(row=1, column=0, columnspan=4, sticky="w", padx=5, pady=5)


    def load_relatorio_vendas(self):
        for item in self.vendas_tree.get_children():
            self.vendas_tree.delete(item)
        
        conn = self.get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT v.id, v.data_hora, v.total_venda, v.desconto_aplicado, v.juros_aplicados, v.total_final, v.forma_pagamento, v.tipo_cartao, v.parcelas_total, v.parcelas_pagas,
                   vend.nome as vendedor_nome, cli.nome as cliente_nome,
                   (SELECT ABS(SUM(mp.pontos)) FROM movimentacoes_pontos mp WHERE mp.referencia_id = v.id AND mp.tipo_movimentacao = 'Utilizacao') AS pontos_utilizados_venda
            FROM vendas v
            LEFT JOIN vendedores vend ON v.vendedor_id = vend.id
            LEFT JOIN clientes cli ON v.cliente_id = cli.id
            WHERE 1=1
        """
        params = []

        data_inicio = self.data_inicio_var.get()
        data_fim = self.data_fim_var.get()
        forma_pagamento_filtro = self.filter_pagamento_var.get()
        tipo_cartao_filtro = self.filter_tipo_cartao_var.get()
        vendedor_filtro_nome = self.filter_vendedor_var.get()
        cliente_filtro_nome = self.filter_cliente_var.get()

        if data_inicio:
            query += " AND DATE(v.data_hora) >= DATE(?)"
            params.append(data_inicio)
        if data_fim:
            query += " AND DATE(v.data_hora) <= DATE(?)"
            params.append(data_fim)
        if forma_pagamento_filtro != "Todos":
            query += " AND v.forma_pagamento = ?"
            params.append(forma_pagamento_filtro)
        if tipo_cartao_filtro != "Todos":
            if tipo_cartao_filtro == "N/A":
                query += " AND v.tipo_cartao IS NULL"
            else:
                query += " AND v.tipo_cartao = ?"
                params.append(tipo_cartao_filtro)
        if vendedor_filtro_nome != "Todos":
            vendedor_id_filtro = self.vendedores_dict.get(vendedor_filtro_nome)
            if vendedor_id_filtro:
                query += " AND v.vendedor_id = ?"
                params.append(vendedor_id_filtro)
        if cliente_filtro_nome != "Todos":
            # Para filtrar cliente, precisamos buscar o ID do cliente pelo nome
            # Usamos uma nova conexão temporária aqui para evitar problemas de cursor
            temp_conn = self.get_db_connection()
            temp_cursor = temp_conn.cursor()
            temp_cursor.execute("SELECT id FROM clientes WHERE nome = ?", (cliente_filtro_nome,))
            cliente_id_filtro_row = temp_cursor.fetchone()
            temp_conn.close() # Fechar a conexão temporária
            
            if cliente_id_filtro_row:
                cliente_id_filtro = cliente_id_filtro_row['id']
                query += " AND v.cliente_id = ?"
                params.append(cliente_id_filtro)
        
        query += " ORDER BY v.data_hora DESC"
        
        cursor.execute(query, tuple(params))
        vendas = cursor.fetchall()
        conn.close()

        total_bruto_acumulado = 0.0
        total_descontos_acumulado = 0.0
        total_juros_acumulado = 0.0
        total_pontos_utilizados_acumulado = 0
        total_final_acumulado = 0.0

        for venda in vendas:
            vendedor_nome_exibicao = venda['vendedor_nome'] if venda['vendedor_nome'] else "Não Informado"
            cliente_nome_exibicao = venda['cliente_nome'] if venda['cliente_nome'] else "Não Informado"
            pontos_utilizados_exibicao = venda['pontos_utilizados_venda'] if venda['pontos_utilizados_venda'] is not None else 0
            tipo_cartao_exibicao = venda['tipo_cartao'] if venda['tipo_cartao'] else "N/A"
            
            parcelas_info = "N/A"
            if venda['forma_pagamento'] == "A Prazo":
                parcelas_info = f"{venda['parcelas_pagas']} de {venda['parcelas_total']}x"

            self.vendas_tree.insert("", "end", values=(
                venda['id'], 
                venda['data_hora'], 
                f"{venda['total_venda']:.2f}",
                f"{venda['desconto_aplicado']:.2f}",
                f"{venda['juros_aplicados']:.2f}",
                pontos_utilizados_exibicao,
                f"{venda['total_final']:.2f}",
                venda['forma_pagamento'],
                tipo_cartao_exibicao,
                parcelas_info,
                vendedor_nome_exibicao, 
                cliente_nome_exibicao
            ))

            total_bruto_acumulado += venda['total_venda']
            total_descontos_acumulado += venda['desconto_aplicado']
            total_juros_acumulado += venda['juros_aplicados']
            total_pontos_utilizados_acumulado += pontos_utilizados_exibicao
            total_final_acumulado += venda['total_final']

        self.total_vendas_label.config(text=f"Total Bruto de Vendas: R$ {total_bruto_acumulado:.2f}")
        self.total_descontos_label.config(text=f"Total de Descontos: R$ {total_descontos_acumulado:.2f}")
        self.total_juros_label.config(text=f"Total de Juros: R$ {total_juros_acumulado:.2f}")
        self.total_pontos_utilizados_label.config(text=f"Total Pontos Utilizados: {total_pontos_utilizados_acumulado}")
        self.total_final_label.config(text=f"TOTAL LÍQUIDO ARRECADADO: R$ {total_final_acumulado:.2f}")

    def on_right_click_tree(self, event):
        # Seleciona o item clicado com o botão direito
        item_id = self.vendas_tree.identify_row(event.y)
        if not item_id:
            return

        self.vendas_tree.selection_set(item_id) # Seleciona o item para que get_selection() funcione
        
        # Cria o menu de contexto
        menu = tk.Menu(self.master, tearoff=0)
        menu.add_command(label="Ver Detalhes da Venda", command=self.show_venda_details_from_tree)
        menu.tk_popup(event.x_root, event.y_root)

    def show_venda_details_from_tree(self):
        selected_item = self.vendas_tree.focus()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione uma venda para ver os detalhes.")
            return
        
        venda_id = self.vendas_tree.item(selected_item, 'values')[0]

        # Reutiliza a lógica de show_venda_details do PDVGUI
        # Para evitar circular import e manter a consistência, chamaremos a função auxiliar
        self._show_sale_details_common(venda_id, self.master) # Passa o master (o frame atual do RelatóriosGUI) como parent_window para a messagebox

    def _show_sale_details_common(self, sale_id, parent_window):
        # Essa função é uma cópia da lógica de show_venda_details do PDVGUI
        # Para evitar dependência circular e permitir reuso.
        conn = self.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT v.data_hora, v.total_venda, v.desconto_aplicado, v.juros_aplicados, v.total_final, v.forma_pagamento, 
                   vend.nome as vendedor_nome, cli.nome as cliente_nome, v.tipo_cartao, v.parcelas_total, v.parcelas_pagas,
                   (SELECT ABS(SUM(mp.pontos)) FROM movimentacoes_pontos mp WHERE mp.referencia_id = v.id AND mp.tipo_movimentacao = 'Utilizacao') AS pontos_utilizados_venda
            FROM vendas v
            LEFT JOIN vendedores vend ON v.vendedor_id = vend.id
            LEFT JOIN clientes cli ON v.cliente_id = cli.id
            WHERE v.id = ?
        """, (sale_id,))
        venda_info = cursor.fetchone()

        cursor.execute("""
            SELECT p.nome, iv.quantidade, iv.preco_unitario
            FROM itens_venda iv
            JOIN produtos p ON iv.produto_id = p.id
            WHERE iv.venda_id = ?
        """, (sale_id,))
        itens_venda = cursor.fetchall()

        parcelas_venda = []
        if venda_info and venda_info['forma_pagamento'] == 'A Prazo':
            cursor.execute("SELECT numero_parcela, valor_parcela, data_vencimento, data_pagamento, status FROM parcelas WHERE venda_id = ? ORDER BY numero_parcela", (sale_id,))
            parcelas_venda = cursor.fetchall()
            
        conn.close()

        if not venda_info:
            messagebox.showerror("Erro", "Detalhes da venda não encontrados.", parent=parent_window)
            return

        details_str = f"Detalhes da Venda ID: {sale_id}\n\n"
        details_str += f"Data/Hora: {venda_info['data_hora']}\n"
        details_str += f"Total Bruto: R$ {venda_info['total_venda']:.2f}\n"
        details_str += f"Desconto Aplicado: R$ {venda_info['desconto_aplicado']:.2f}\n"
        details_str += f"Juros Aplicados: R$ {venda_info['juros_aplicados']:.2f}\n"
        details_str += f"Pontos Utilizados: {venda_info['pontos_utilizados_venda'] if venda_info['pontos_utilizados_venda'] is not None else 0}\n"
        details_str += f"TOTAL FINAL: R$ {venda_info['total_final']:.2f}\n"
        details_str += f"Pagamento: {venda_info['forma_pagamento']}\n"
        details_str += f"Tipo Cartão: {venda_info['tipo_cartao'] if venda_info['tipo_cartao'] else 'N/A'}\n"
        
        if venda_info['forma_pagamento'] == 'A Prazo':
            details_str += f"Parcelamento: {venda_info['parcelas_pagas']} de {venda_info['parcelas_total']}x\n"
            details_str += "\nDetalhes das Parcelas:\n"
            for parcela in parcelas_venda:
                data_pag = parcela['data_pagamento'] if parcela['data_pagamento'] else "Pendente"
                details_str += f"  - Parcela {parcela['numero_parcela']}/{venda_info['parcelas_total']}: R$ {parcela['valor_parcela']:.2f} (Venc: {parcela['data_vencimento']}, Pgto: {data_pag}, Status: {parcela['status']})\n"
        details_str += "\n"

        details_str += f"Vendedor: {venda_info['vendedor_nome'] if venda_info['vendedor_nome'] else 'Não Informado'}\n"
        details_str += f"Cliente: {venda_info['cliente_nome'] if venda_info['cliente_nome'] else 'Não Informado'}\n\n"
        details_str += "Itens Vendidos:\n"
        
        for item in itens_venda:
            details_str += f"- {item['nome']} (x{item['quantidade']}) @ R$ {item['preco_unitario']:.2f} cada\n"

        messagebox.showinfo("Detalhes da Venda", details_str, parent=parent_window)