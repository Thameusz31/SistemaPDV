import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from database import DATABASE_NAME
from datetime import datetime, timedelta

class APrazoGUI(ttk.Frame):
    def __init__(self, master):
        # A classe herda de ttk.Frame e 'master' é o frame pai do MainApp
        super().__init__(master, padding="15")
        self.master = master # Referência ao frame pai

        self.conn = self.get_db_connection()

        # --- INICIALIZAÇÃO DE TODAS AS StringVar E LISTAS DE OPÇÕES AQUI ---
        # Garantindo que existam antes de qualquer widget tentar usá-las
        self.filter_cliente_var = tk.StringVar(value="Todos") # CORREÇÃO: Inicialização movida para aqui
        self.filter_status_var = tk.StringVar(value="Pendente") # CORREÇÃO: Inicialização movida para aqui

        # Listas de opções (definidas como atributos da instância)
        self.filter_status_options = ["Todos", "Pendente", "Pago", "Atrasado"]
        
        # Cria os widgets de filtro
        self.create_filter_widgets(self)
        # Cria os widgets da tabela de parcelas
        self.create_parcelas_widgets(self)
        
        # Dicionário para mapear nome do cliente para ID
        self.clientes_dict = {} 
        
        # Carrega os dados necessários para os filtros e a tabela
        self._load_clientes_for_filter() # Carrega clientes para o dropdown de filtro
        self.load_parcelas() # Carrega as parcelas na tabela

    def get_db_connection(self):
        # Retorna uma conexão com o banco de dados com row_factory para acesso por nome
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row
        return conn

    def _load_clientes_for_filter(self):
        # Carrega a lista de clientes para o dropdown de filtro
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM clientes ORDER BY nome")
        clientes_db = cursor.fetchall()
        conn.close()

        cliente_nomes_for_filter = ["Todos"] # Adiciona a opção "Todos"
        for c in clientes_db:
            self.clientes_dict[c['nome']] = c['id'] # Popula o dicionário
            cliente_nomes_for_filter.append(c['nome'])
        
        # Atualiza o OptionMenu de cliente no filtro
        # Garante que o OptionMenu foi criado em create_filter_widgets
        if hasattr(self, 'filter_cliente_menu') and self.filter_cliente_menu is not None:
            menu = self.filter_cliente_menu["menu"]
            menu.delete(0, "end") # Limpa as opções antigas
            for nome in cliente_nomes_for_filter:
                menu.add_command(label=nome, command=tk._setit(self.filter_cliente_var, nome))
            self.filter_cliente_var.set(cliente_nomes_for_filter[0]) # Reseta a seleção
        else: # Este bloco não deve ser acionado se create_filter_widgets for chamado antes de _load_clientes_for_filter
            pass


    def create_filter_widgets(self, parent_frame):
        # Cria o LabelFrame para os filtros
        self.filter_frame = ttk.LabelFrame(parent_frame, text="Filtros de Parcelas", padding="10")
        self.filter_frame.pack(pady=10, padx=10, fill="x")
        
        # Configura as colunas para que os campos de entrada expandam
        self.filter_frame.columnconfigure(1, weight=1)
        self.filter_frame.columnconfigure(3, weight=1)
        self.filter_frame.columnconfigure(5, weight=1) # Coluna para o filtro de status

        # Campo de data de vencimento "De"
        ttk.Label(self.filter_frame, text="Vencimento De:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.data_venc_inicio_entry = ttk.Entry(self.filter_frame, width=15)
        self.data_venc_inicio_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        # self.data_venc_inicio_entry.insert(0, (datetime.now().replace(day=1)).strftime("%Y-%m-%d")) # Exemplo: Início do mês atual

        # Campo de data de vencimento "Até"
        ttk.Label(self.filter_frame, text="Vencimento Até:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.data_venc_fim_entry = ttk.Entry(self.filter_frame, width=15)
        self.data_venc_fim_entry.grid(row=0, column=3, sticky="ew", padx=5, pady=5)
        self.data_venc_fim_entry.insert(0, (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")) # Padrão: Vencimento nos próximos 30 dias

        # Filtro de Status da Parcela
        ttk.Label(self.filter_frame, text="Status:").grid(row=0, column=4, sticky="w", padx=5, pady=5)
        # self.filter_status_var já inicializado no __init__
        self.filter_status_menu = ttk.OptionMenu(self.filter_frame, self.filter_status_var, self.filter_status_options[0], *self.filter_status_options)
        self.filter_status_menu.grid(row=0, column=5, sticky="ew", padx=5, pady=5)

        # Filtro por Cliente
        ttk.Label(self.filter_frame, text="Cliente:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        # self.filter_cliente_var já inicializado no __init__
        self.filter_cliente_menu = ttk.OptionMenu(self.filter_frame, self.filter_cliente_var, "Todos") # Usar "Todos" como placeholder inicial
        self.filter_cliente_menu.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        # Botão para filtrar
        ttk.Button(self.filter_frame, text="Filtrar Parcelas", command=self.load_parcelas, style='Accent.TButton').grid(row=1, column=2, columnspan=4, pady=10)


    def create_parcelas_widgets(self, parent_frame):
        # Cria o LabelFrame para a tabela de parcelas
        parcelas_frame = ttk.LabelFrame(parent_frame, text="Próximas Parcelas e Pagamentos", padding="10")
        parcelas_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Define as colunas da Treeview
        columns = ("ID Parcela", "Venda ID", "Cliente", "Data da Venda", "Parcela", "Valor", "Vencimento", "Data Pgto", "Status")
        self.parcelas_tree = ttk.Treeview(parcelas_frame, columns=columns, show="headings", selectmode="browse")

        # Configura as cabeçalhos e larguras das colunas
        for col in columns:
            self.parcelas_tree.heading(col, text=col)
            if col == "ID Parcela" or col == "Venda ID":
                self.parcelas_tree.column(col, width=70, anchor="center")
            elif col in ["Cliente", "Data da Venda", "Vencimento", "Data Pgto", "Status"]:
                self.parcelas_tree.column(col, width=120, anchor="center")
            elif col == "Parcela":
                self.parcelas_tree.column(col, width=80, anchor="center")
            elif col == "Valor":
                self.parcelas_tree.column(col, width=100, anchor="e") # Alinhado à direita para valores
            else:
                self.parcelas_tree.column(col, width=80, anchor="center")

        self.parcelas_tree.pack(fill="both", expand=True)

        # Adiciona uma barra de rolagem vertical à Treeview
        scrollbar = ttk.Scrollbar(parcelas_frame, orient="vertical", command=self.parcelas_tree.yview)
        self.parcelas_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Frame para os botões de ação
        button_frame = ttk.Frame(parcelas_frame)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Marcar como Paga", command=self.marcar_parcela_paga, style='Accent.TButton').pack(side="left", padx=5)
        ttk.Button(button_frame, text="Ver Detalhes da Venda", command=self.view_venda_details_from_parcela).pack(side="left", padx=5)


    def load_parcelas(self):
        # Limpa os itens existentes na Treeview
        for item in self.parcelas_tree.get_children():
            self.parcelas_tree.delete(item)
        
        conn = self.get_db_connection()
        cursor = conn.cursor()

        # Query SQL para buscar as parcelas com informações da venda e do cliente
        query = """
            SELECT p.id, p.venda_id, p.numero_parcela, p.valor_parcela, p.data_vencimento, p.data_pagamento, p.status,
                   v.data_hora as data_venda, cli.nome as cliente_nome, v.parcelas_total
            FROM parcelas p
            JOIN vendas v ON p.venda_id = v.id
            LEFT JOIN clientes cli ON v.cliente_id = cli.id
            WHERE 1=1
        """
        params = [] # Lista para os parâmetros da query

        # Obtém os valores dos filtros selecionados pelo usuário
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
        
        # Filtro de status "Atrasado" é tratado especificamente na query
        if status_filtro == "Atrasado":
            query += " AND p.status = 'Pendente' AND DATE(p.data_vencimento) < DATE(?)"
            params.append(datetime.now().strftime("%Y-%m-%d"))
        elif status_filtro != "Todos":
            query += " AND p.status = ?"
            params.append(status_filtro)
        
        # Filtro por cliente
        if cliente_filtro_nome != "Todos":
            cliente_id_filtro = self.clientes_dict.get(cliente_filtro_nome)
            if cliente_id_filtro:
                query += " AND v.cliente_id = ?"
                params.append(cliente_id_filtro)
            else:
                pass # Cliente não encontrado, não filtra

        # Ordena os resultados
        query += " ORDER BY p.data_vencimento ASC, p.venda_id ASC, p.numero_parcela ASC"
        
        # Executa a query e busca os resultados
        cursor.execute(query, tuple(params))
        parcelas = cursor.fetchall()
        conn.close()

        # Popula a Treeview com as parcelas
        for parc in parcelas:
            current_status = parc['status']
            tags = () # Tags para aplicar estilos de cor
            
            # Determina o status real (incluindo "Atrasado" para exibição) e aplica a tag
            if current_status == 'Pendente' and parc['data_vencimento'] < datetime.now().strftime("%Y-%m-%d"):
                current_status = 'Atrasado'
                tags = ('overdue',)
            elif current_status == 'Pendente':
                tags = ('pending',)
            elif current_status == 'Pago':
                tags = ('paid',)

            # Formata a data de pagamento para exibição
            data_pag_exibicao = parc['data_pagamento'] if parc['data_pagamento'] else "Pendente"
            # Formata o nome do cliente para exibição
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
        # Obtém a parcela selecionada na Treeview
        selected_item = self.parcelas_tree.focus()
        if not selected_item:
            messagebox.showwarning("Aviso", "Nenhuma parcela selecionada para marcar como paga.")
            return

        # Pega os valores da parcela selecionada
        parcela_id = self.parcelas_tree.item(selected_item, 'values')[0]
        venda_id = self.parcelas_tree.item(selected_item, 'values')[1]
        parcela_status = self.parcelas_tree.item(selected_item, 'values')[8] # Pega o status exibido

        # Verifica se a parcela já está paga
        if parcela_status == 'Pago':
            messagebox.showinfo("Informação", "Esta parcela já está marcada como 'Paga'.")
            return
        
        # Confirma com o usuário antes de marcar como paga
        if messagebox.askyesno("Confirmar Pagamento", f"Confirmar pagamento da parcela ID {parcela_id}?"):
            conn = self.get_db_connection()
            cursor = conn.cursor()
            try:
                # Atualiza o status da parcela no banco de dados para 'Pago' e registra a data
                data_pagamento = datetime.now().strftime("%Y-%m-%d")
                cursor.execute("UPDATE parcelas SET status = 'Pago', data_pagamento = ? WHERE id = ?", (data_pagamento, parcela_id))
                
                # Incrementa o contador de parcelas pagas na tabela 'vendas'
                cursor.execute("UPDATE vendas SET parcelas_pagas = parcelas_pagas + 1 WHERE id = ?", (venda_id,))

                conn.commit() # Confirma as alterações no banco de dados
                messagebox.showinfo("Sucesso", "Parcela marcada como paga com sucesso!")
                self.load_parcelas() # Recarrega a lista de parcelas para atualizar a exibição
            except Exception as e:
                conn.rollback() # Desfaz as operações em caso de erro
                messagebox.showerror("Erro", f"Erro ao marcar parcela como paga: {e}")
            finally:
                conn.close() # Fecha a conexão com o banco de dados

    def view_venda_details_from_parcela(self):
        # Obtém a parcela selecionada
        selected_item = self.parcelas_tree.focus()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione uma parcela para ver os detalhes da venda.")
            return
        
        # Pega o ID da venda associado à parcela
        venda_id = self.parcelas_tree.item(selected_item, 'values')[1]

        conn = self.get_db_connection()
        cursor = conn.cursor()

        # Busca as informações da venda principal
        cursor.execute("""
            SELECT v.data_hora, v.total_venda, v.desconto_aplicado, v.total_final, v.forma_pagamento, v.tipo_cartao, v.parcelas_total, v.parcelas_pagas,
                   vend.nome as vendedor_nome, cli.nome as cliente_nome,
                   (SELECT ABS(SUM(mp.pontos)) FROM movimentacoes_pontos mp WHERE mp.referencia_id = v.id AND mp.tipo_movimentacao = 'Utilizacao') AS pontos_utilizados_venda
            FROM vendas v
            LEFT JOIN vendedores vend ON v.vendedor_id = vend.id
            LEFT JOIN clientes cli ON v.cliente_id = cli.id
            WHERE v.id = ?
        """, (venda_id,))
        venda_info = cursor.fetchone()

        # Busca os itens da venda
        cursor.execute("""
            SELECT p.nome, iv.quantidade, iv.preco_unitario
            FROM itens_venda iv
            JOIN produtos p ON iv.produto_id = p.id
            WHERE iv.venda_id = ?
        """, (venda_id,))
        itens_venda = cursor.fetchall()

        # Busca as parcelas da venda, se for "A Prazo"
        parcelas_venda = []
        if venda_info and venda_info['forma_pagamento'] == 'A Prazo':
            cursor.execute("SELECT numero_parcela, valor_parcela, data_vencimento, data_pagamento, status FROM parcelas WHERE venda_id = ? ORDER BY numero_parcela", (venda_id,))
            parcelas_venda = cursor.fetchall()

        conn.close() # Fecha a conexão

        if not venda_info:
            messagebox.showerror("Erro", "Detalhes da venda não encontrados.")
            return

        # Monta a string com os detalhes da venda
        details_str = f"Detalhes da Venda ID: {venda_id}\n\n"
        details_str += f"Data/Hora: {venda_info['data_hora']}\n"
        details_str += f"Total Bruto: R$ {venda_info['total_venda']:.2f}\n"
        details_str += f"Desconto Aplicado: R$ {venda_info['desconto_aplicado']:.2f}\n"
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

        # Exibe os detalhes em uma messagebox
        messagebox.showinfo("Detalhes da Venda", details_str, parent=self.master)