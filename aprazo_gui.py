import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from database import DATABASE_NAME
from datetime import datetime, timedelta

class APrazoGUI(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding="15")
        self.master = master

        self.conn = self.get_db_connection()

        self.filter_cliente_var = tk.StringVar(value="Todos")
        self.filter_status_var = tk.StringVar(value="Pendente")

        self.filter_status_options = ["Todos", "Pendente", "Pago", "Atrasado"]
        
        self.create_filter_widgets(self)
        self.create_parcelas_widgets(self)
        
        self.clientes_dict = {}
        self._load_clientes_for_filter()
        self.load_parcelas()

    def get_db_connection(self):
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row
        return conn

    def _load_clientes_for_filter(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM clientes ORDER BY nome")
        clientes_db = cursor.fetchall()
        conn.close()

        cliente_nomes_for_filter = ["Todos"]
        for c in clientes_db:
            self.clientes_dict[c['nome']] = c['id']
            cliente_nomes_for_filter.append(c['nome'])
        
        if hasattr(self, 'filter_cliente_menu') and self.filter_cliente_menu is not None:
            menu = self.filter_cliente_menu["menu"]
            menu.delete(0, "end")
            for nome in cliente_nomes_for_filter:
                menu.add_command(label=nome, command=tk._setit(self.filter_cliente_var, nome))
            self.filter_cliente_var.set(cliente_nomes_for_filter[0])
        else:
            pass


    def create_filter_widgets(self, parent_frame):
        self.filter_frame = ttk.LabelFrame(parent_frame, text="Filtros de Parcelas", padding="10")
        self.filter_frame.pack(pady=10, padx=10, fill="x")
        
        self.filter_frame.columnconfigure(1, weight=1)
        self.filter_frame.columnconfigure(3, weight=1)
        self.filter_frame.columnconfigure(5, weight=1)

        ttk.Label(self.filter_frame, text="Vencimento De:").grid(row=0, column=0, sticky="w", padx=5, pady=5) # REMOVIDO background='white'
        self.data_venc_inicio_entry = ttk.Entry(self.filter_frame, width=15)
        self.data_venc_inicio_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Label(self.filter_frame, text="Vencimento Até:").grid(row=0, column=2, sticky="w", padx=5, pady=5) # REMOVIDO background='white'
        self.data_venc_fim_entry = ttk.Entry(self.filter_frame, width=15)
        self.data_venc_fim_entry.grid(row=0, column=3, sticky="ew", padx=5, pady=5)
        self.data_venc_fim_entry.insert(0, (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"))

        ttk.Label(self.filter_frame, text="Status:").grid(row=0, column=4, sticky="w", padx=5, pady=5) # REMOVIDO background='white'
        self.filter_status_menu = ttk.OptionMenu(self.filter_frame, self.filter_status_var, self.filter_status_options[0], *self.filter_status_options)
        self.filter_status_menu.grid(row=0, column=5, sticky="ew", padx=5, pady=5)

        ttk.Label(self.filter_frame, text="Cliente:").grid(row=1, column=0, sticky="w", padx=5, pady=5) # REMOVIDO background='white'
        self.filter_cliente_menu = ttk.OptionMenu(self.filter_frame, self.filter_cliente_var, "Todos")
        self.filter_cliente_menu.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ttk.Button(self.filter_frame, text="Filtrar Parcelas", command=self.load_parcelas, style='Accent.TButton').grid(row=1, column=2, columnspan=4, pady=10)


    def create_parcelas_widgets(self, parent_frame):
        parcelas_frame = ttk.LabelFrame(parent_frame, text="Próximas Parcelas e Pagamentos", padding="10")
        parcelas_frame.pack(pady=10, padx=10, fill="both", expand=True)

        columns = ("ID Parcela", "Venda ID", "Cliente", "Data da Venda", "Parcela", "Valor", "Vencimento", "Data Pgto", "Status")
        self.parcelas_tree = ttk.Treeview(parcelas_frame, columns=columns, show="headings", selectmode="browse")

        for col in columns:
            self.parcelas_tree.heading(col, text=col)
            if col == "ID Parcela" or col == "Venda ID":
                self.parcelas_tree.column(col, width=70, anchor="center")
            elif col in ["Cliente", "Data da Venda", "Vencimento", "Data Pgto", "Status"]:
                self.parcelas_tree.column(col, width=120, anchor="center")
            elif col == "Parcela":
                self.parcelas_tree.column(col, width=80, anchor="center")
            elif col == "Valor":
                self.parcelas_tree.column(col, width=100, anchor="e")
            else:
                self.parcelas_tree.column(col, width=80, anchor="center")

        self.parcelas_tree.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(parcelas_frame, orient="vertical", command=self.parcelas_tree.yview)
        self.parcelas_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        button_frame = ttk.Frame(parcelas_frame)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Marcar como Paga", command=self.marcar_parcela_paga, style='Accent.TButton').pack(side="left", padx=5)
        ttk.Button(button_frame, text="Ver Detalhes da Venda", command=self.view_venda_details_from_parcela).pack(side="left", padx=5)


    def load_parcelas(self):
        for item in self.parcelas_tree.get_children():
            self.parcelas_tree.delete(item)
        
        conn = self.get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT p.id, p.venda_id, p.numero_parcela, p.valor_parcela, p.data_vencimento, p.data_pagamento, p.status,
                   v.data_hora as data_venda, cli.nome as cliente_nome, v.parcelas_total, v.forma_pagamento, v.tipo_cartao, v.desconto_aplicado, v.juros_aplicados, v.total_final
            FROM parcelas p
            JOIN vendas v ON p.venda_id = v.id
            LEFT JOIN clientes cli ON v.cliente_id = cli.id
            WHERE 1=1
        """
        params = []

        data_venc_inicio = self.data_venc_inicio_entry.get()
        data_venc_fim = self.data_venc_fim_entry.get()
        status_filtro = self.filter_status_var.get()
        cliente_filtro_nome = self.filter_cliente_var.get()

        if data_venc_inicio:
            query += " AND DATE(p.data_vencimento) >= DATE(?)"
            params.append(data_venc_inicio)
        if data_venc_fim:
            query += " AND DATE(p.data_vencimento) <= DATE(?)"
            params.append(data_venc_fim)
        
        if status_filtro == "Atrasado":
            query += " AND p.status = 'Pendente' AND DATE(p.data_vencimento) < DATE(?)"
            params.append(datetime.now().strftime("%Y-%m-%d"))
        elif status_filtro != "Todos":
            query += " AND p.status = ?"
            params.append(status_filtro)
        
        if cliente_filtro_nome != "Todos":
            cliente_id_filtro = self.clientes_dict.get(cliente_filtro_nome)
            if cliente_id_filtro:
                query += " AND v.cliente_id = ?"
                params.append(cliente_id_filtro)
            else:
                pass

        query += " ORDER BY p.data_vencimento ASC, p.venda_id ASC, p.numero_parcela ASC"
        
        cursor.execute(query, tuple(params))
        parcelas = cursor.fetchall()
        conn.close()

        for parc in parcelas:
            current_status = parc['status']
            tags = ()
            
            if current_status == 'Pendente' and parc['data_vencimento'] < datetime.now().strftime("%Y-%m-%d"):
                current_status = 'Atrasada' # Corrigido para 'Atrasada' para consistência
                tags = ('overdue',)
            elif current_status == 'Pendente':
                tags = ('pending',)
            elif current_status == 'Pago':
                tags = ('paid',)

            data_pag_exibicao = parc['data_pagamento'] if parc['data_pagamento'] else "Pendente"
            cliente_nome_exibicao = parc['cliente_nome'] if parc['cliente_nome'] else "Não Informado"

            self.parcelas_tree.insert("", "end", values=(
                parc['id'],
                parc['venda_id'],
                cliente_nome_exibicao,
                parc['data_venda'],
                f"{parc['numero_parcela']} de {parc['parcelas_total']}",
                f"R$ {parc['valor_parcela']:.2f}",
                parc['data_vencimento'],
                data_pag_exibicao,
                current_status
            ), tags=tags)


    def marcar_parcela_paga(self):
        selected_item = self.parcelas_tree.focus()
        if not selected_item:
            messagebox.showwarning("Aviso", "Nenhuma parcela selecionada para marcar como paga.")
            return

        parcela_id = self.parcelas_tree.item(selected_item, 'values')[0]
        venda_id = self.parcelas_tree.item(selected_item, 'values')[1]
        parcela_status_exibido = self.parcelas_tree.item(selected_item, 'values')[8]

        if parcela_status_exibido == 'Pago':
            messagebox.showinfo("Informação", "Esta parcela já está marcada como 'Paga'.")
            return
        
        if messagebox.askyesno("Confirmar Pagamento", f"Confirmar pagamento da parcela ID {parcela_id}?"):
            conn = self.get_db_connection()
            cursor = conn.cursor()
            try:
                data_pagamento_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("UPDATE parcelas SET status = 'Pago', data_pagamento = ? WHERE id = ?", (data_pagamento_atual.split(' ')[0], parcela_id))
                
                # Incrementa o contador de parcelas pagas na tabela 'vendas'
                cursor.execute("UPDATE vendas SET parcelas_pagas = parcelas_pagas + 1 WHERE id = ?", (venda_id,))

                # NOVO: Registrar movimentação no Caixa
                cursor.execute("""
                    SELECT p.numero_parcela, p.valor_parcela, v.parcelas_total, v.forma_pagamento, v.tipo_cartao, v.vendedor_id, v.cliente_id
                    FROM parcelas p JOIN vendas v ON p.venda_id = v.id WHERE p.id = ?
                """, (parcela_id,))
                parcela_data = cursor.fetchone()

                if parcela_data:
                    valor_parcela_paga = parcela_data['valor_parcela']
                    forma_pag_venda = parcela_data['forma_pagamento']
                    tipo_cartao_venda = parcela_data['tipo_cartao']
                    responsavel_id = parcela_data['vendedor_id']
                    cliente_id_venda = parcela_data['cliente_id']

                    descricao_mov = f"Pagamento Parcela {parcela_data['numero_parcela']}/{parcela_data['parcelas_total']} - Venda ID {venda_id}"
                    
                    forma_pagamento_para_caixa = "Recebimento Parcela"
                    if forma_pag_venda == "Cartao" and tipo_cartao_venda:
                        forma_pagamento_para_caixa = f"Parcela - {tipo_cartao_venda}"
                    elif forma_pag_venda == "Dinheiro" or forma_pag_venda == "Pix":
                         forma_pagamento_para_caixa = f"Parcela - {forma_pag_venda}"
                    
                    cursor.execute("INSERT INTO movimentacoes_caixa (data_hora, tipo_movimentacao, valor, forma_pagamento, descricao, referencia_id, tabela_referencia, responsavel_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                   (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Entrada", valor_parcela_paga, forma_pagamento_para_caixa,
                                    descricao_mov, parcela_id, "parcelas", responsavel_id))


                conn.commit()
                messagebox.showinfo("Sucesso", "Parcela marcada como paga com sucesso!")
                self.load_parcelas()
            except Exception as e:
                conn.rollback()
                messagebox.showerror("Erro", f"Erro ao marcar parcela como paga: {e}")
            finally:
                conn.close()

    def view_venda_details_from_parcela(self):
        selected_item = self.parcelas_tree.focus()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione uma parcela para ver os detalhes da venda.")
            return
        
        venda_id = self.parcelas_tree.item(selected_item, 'values')[1]

        self._show_sale_details_common(venda_id, self.master)

    def _show_sale_details_common(self, sale_id, parent_window):
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