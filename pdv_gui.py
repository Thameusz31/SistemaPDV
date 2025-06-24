import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from database import DATABASE_NAME
from datetime import datetime, timedelta

class PDVGUI(ttk.Frame):
    PONTOS_POR_REAL = 1 / 10
    VALOR_POR_PONTO = 5 / 100

    def __init__(self, master):
        super().__init__(master, padding="10")
        self.master = master

        self.conn = self.get_db_connection()
        self.carrinho = []
        self.total_venda = 0.0
        self.desconto_aplicado = 0.0
        self.juros_aplicados = 0.0
        self.total_final_com_desconto = 0.0
        self.pontos_utilizados = 0

        # --- Inicialização de TODAS AS StringVar E LISTAS DE OPÇÕES AQUI ---
        self.selected_vendedor_var = tk.StringVar(value="-- Selecione --")
        self.selected_cliente_var = tk.StringVar(value="-- Selecione --")
        self.filter_vendedor_var = tk.StringVar(value="Todos")
        self.filter_cliente_var = tk.StringVar(value="Todos")
        self.forma_pagamento_var = tk.StringVar(value="Dinheiro")
        self.tipo_cartao_var = tk.StringVar(value="Crédito")
        self.parcelas_var = tk.StringVar(value="1x")
        self.filter_pagamento_var = tk.StringVar(value="Todos")
        self.filter_tipo_cartao_var = tk.StringVar(value="Todos")
        self.filter_status_parcela_var = tk.StringVar(value="Todos")

        # Variáveis para Desconto e Juros
        self.desconto_entry_var = tk.StringVar(value="0.00")
        self.juros_tipo_var = tk.StringVar(value="Percentual")
        self.juros_entry_var = tk.StringVar(value="0.00")


        # Listas de opções (definidas como atributos da instância)
        self.forma_pagamento_options = ["Dinheiro", "Cartao", "Pix", "A Prazo"]
        self.tipo_cartao_options = ["Crédito", "Débito"]
        self.parcelas_options = ["1x", "2x", "3x"]
        self.filter_pagamento_options = ["Todos", "Dinheiro", "Cartao", "Pix", "A Prazo"]
        self.filter_tipo_cartao_options = ["Todos", "Crédito", "Débito", "N/A"]
        self.filter_status_parcela_options = ["Todos", "Pendente", "Pago", "Atrasado", "N/A"]

        # --- Notebook para separar Venda e Histórico ---
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=5, padx=5, fill="both", expand=True)

        # --- Frame para Nova Venda (Aba 1) ---
        self.frame_nova_venda_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_nova_venda_tab, text="Nova Venda")

        # --- Canvas com Scrollbar para a aba de Nova Venda ---
        self.canvas_venda = tk.Canvas(self.frame_nova_venda_tab)
        self.scrollbar_venda = ttk.Scrollbar(self.frame_nova_venda_tab, orient="vertical", command=self.canvas_venda.yview)
        
        # Frame onde todo o conteúdo rolável será colocado
        self.scrollable_frame_venda = ttk.Frame(self.canvas_venda, padding="5")

        self.scrollable_frame_venda.bind(
            "<Configure>",
            lambda e: self.canvas_venda.configure(
                scrollregion=self.canvas_venda.bbox("all")
            )
        )
        self.canvas_venda.create_window((0, 0), window=self.scrollable_frame_venda, anchor="nw", width=self.canvas_venda.winfo_width())
        self.canvas_venda.bind('<Configure>', lambda e: self.canvas_venda.itemconfig(self.canvas_venda.find_all()[-1], width=e.width))

        self.canvas_venda.configure(yscrollcommand=self.scrollbar_venda.set)

        self.canvas_venda.pack(side="left", fill="both", expand=True)
        self.scrollbar_venda.pack(side="right", fill="y")
        
        # --- NOVO: Ligar evento de roda do mouse para rolagem ---
        self.canvas_venda.bind_all("<MouseWheel>", self._on_mouse_wheel) # Para Windows/Linux
        # Para macOS, você pode precisar de <Button-4> (rolar para cima) e <Button-5> (rolar para baixo)
        # self.canvas_venda.bind_all("<Button-4>", self._on_mouse_wheel)
        # self.canvas_venda.bind_all("<Button-5>", self._on_mouse_wheel)


        # --- Sub-frames da Aba Nova Venda (AGORA DENTRO DE scrollable_frame_venda) ---
        self.frame_vendedor_cliente = ttk.LabelFrame(self.scrollable_frame_venda, text="Vendedor e Cliente", padding="5 10")
        self.frame_vendedor_cliente.pack(pady=5, padx=5, fill="x")
        self.frame_vendedor_cliente.columnconfigure(1, weight=1)

        self.frame_input = ttk.LabelFrame(self.scrollable_frame_venda, text="Adicionar Item", padding="5 10")
        self.frame_input.pack(pady=5, padx=5, fill="x")
        self.frame_input.columnconfigure(1, weight=1)

        self.frame_carrinho = ttk.LabelFrame(self.scrollable_frame_venda, text="Itens do Carrinho", padding="5 10")
        self.frame_carrinho.pack(pady=5, padx=5, fill="both", expand=True)

        self.frame_desconto_juros_pontos = ttk.LabelFrame(self.scrollable_frame_venda, text="Desconto, Juros e Fidelidade", padding="5 10") 
        self.frame_desconto_juros_pontos.pack(pady=5, padx=5, fill="x")
        self.frame_desconto_juros_pontos.columnconfigure(1, weight=1)
        self.frame_desconto_juros_pontos.columnconfigure(3, weight=1)

        self.frame_total_pagamento = ttk.Frame(self.scrollable_frame_venda, padding="5 10")
        self.frame_total_pagamento.pack(pady=5, padx=5, fill="x")
        self.frame_total_pagamento.columnconfigure(0, weight=1)
        self.frame_total_pagamento.columnconfigure(1, weight=1)


        # --- Frame para Histórico de Vendas (Aba 2) ---
        self.frame_historico_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.frame_historico_tab, text="Histórico de Vendas")
        self.frame_historico_tab.columnconfigure(0, weight=1)

        # --- Criação dos widgets que dependem das variáveis StringVar ---
        self.vendedor_dropdown = ttk.OptionMenu(self.frame_vendedor_cliente, self.selected_vendedor_var, "")
        self.cliente_dropdown = ttk.OptionMenu(self.frame_vendedor_cliente, self.selected_cliente_var, "")
        
        # Widgets de pagamento: Criados aqui, mas não empacotados/grid.
        self.tipo_cartao_label = ttk.Label(self.frame_total_pagamento, text="Tipo Cartão:")
        self.tipo_cartao_menu = ttk.OptionMenu(self.frame_total_pagamento, self.tipo_cartao_var, self.tipo_cartao_options[0], *self.tipo_cartao_options)

        self.parcelas_label = ttk.Label(self.frame_total_pagamento, text="Parcelas:")
        self.parcelas_menu = ttk.OptionMenu(self.frame_total_pagamento, self.parcelas_var, self.parcelas_options[0], *self.parcelas_options)
        
        # Widgets de filtro do histórico: Criados aqui, MAS SERÃO GRID-ED DENTRO DE `filter_controls_frame`
        self.filter_vendedor_menu = ttk.OptionMenu(self.frame_historico_tab, self.filter_vendedor_var, "Todos")
        self.filter_cliente_menu = ttk.OptionMenu(self.frame_historico_tab, self.filter_cliente_var, "Todos")
        self.filter_tipo_cartao_menu = ttk.OptionMenu(self.frame_historico_tab, self.filter_tipo_cartao_var, self.filter_tipo_cartao_options[0], *self.filter_tipo_cartao_options)
        self.filter_status_parcela_menu = ttk.OptionMenu(self.frame_historico_tab, self.filter_status_parcela_var, self.filter_status_parcela_options[0], *self.filter_status_parcela_options)
        self.filter_pagamento_menu = ttk.OptionMenu(self.frame_historico_tab, self.filter_pagamento_var, self.filter_pagamento_options[0], *self.filter_pagamento_options)


        # Chamadas para criar e configurar os widgets (passando os frames corretos como pais)
        self.create_vendedor_cliente_selection(self.frame_vendedor_cliente)
        self.create_input_widgets(self.frame_input)
        self.create_carrinho_widgets(self.frame_carrinho)
        self.create_desconto_juros_pontos_widgets(self.frame_desconto_juros_pontos) 
        self.create_total_pagamento_widgets(self.frame_total_pagamento)
        self.create_historico_widgets(self.frame_historico_tab)
        
        # Recarregar dados após a criação de todos os widgets
        self._load_vendedores_clientes_for_dropdowns() 
        self.load_vendas_historico()

    def _on_mouse_wheel(self, event): # NOVO MÉTODO
        # Role a tela com base na direção da roda do mouse
        self.canvas_venda.yview_scroll(int(-1*(event.delta/120)), "units")

    def get_db_connection(self):
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _load_vendedores_clientes_for_dropdowns(self):
        # Carrega Vendedores
        self.vendedores_dict = {}
        vendedor_nomes_for_sale = ["-- Selecione --"]
        vendedor_nomes_for_filter = ["Todos"]
        
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM vendedores ORDER BY nome")
        vendedores_db = cursor.fetchall()
        for v in vendedores_db:
            self.vendedores_dict[v['nome']] = v['id']
            vendedor_nomes_for_sale.append(v['nome'])
            vendedor_nomes_for_filter.append(v['nome'])

        menu_venda = self.vendedor_dropdown["menu"]
        menu_venda.delete(0, "end")
        for nome in vendedor_nomes_for_sale:
            menu_venda.add_command(label=nome, command=tk._setit(self.selected_vendedor_var, nome))
        self.selected_vendedor_var.set(vendedor_nomes_for_sale[0])

        # Recarrega as opções do menu de filtro do vendedor
        if hasattr(self, 'filter_vendedor_menu') and self.filter_vendedor_menu is not None:
            menu_filter_vendedor = self.filter_vendedor_menu["menu"]
            menu_filter_vendedor.delete(0, "end")
            for nome in vendedor_nomes_for_filter:
                menu_filter_vendedor.add_command(label=nome, command=tk._setit(self.filter_vendedor_var, nome))
            self.filter_vendedor_var.set(vendedor_nomes_for_filter[0])


        # Carrega Clientes (com pontos)
        self.clientes_dict = {}
        self.clientes_pontos_dict = {}
        cliente_nomes_for_sale = ["-- Selecione --"]
        cliente_nomes_for_filter = ["Todos"]

        cursor.execute("SELECT id, nome, pontos FROM clientes ORDER BY nome")
        clientes_db = cursor.fetchall()
        conn.close()

        for c in clientes_db:
            display_name = f"{c['nome']} (Pontos: {c['pontos']})"
            self.clientes_dict[display_name] = c['id']
            self.clientes_pontos_dict[c['id']] = c['pontos']
            cliente_nomes_for_sale.append(display_name)
            cliente_nomes_for_filter.append(c['nome'])

        menu_cliente = self.cliente_dropdown["menu"]
        menu_cliente.delete(0, "end")
        for nome in cliente_nomes_for_sale:
            menu_cliente.add_command(label=nome, command=tk._setit(self.selected_cliente_var, nome, self.update_pontos_display))
        self.selected_cliente_var.set(cliente_nomes_for_sale[0])

        # Recarrega as opções do menu de filtro do cliente
        if hasattr(self, 'filter_cliente_menu') and self.filter_cliente_menu is not None:
            menu_filter_cliente = self.filter_cliente_menu["menu"]
            menu_filter_cliente.delete(0, "end")
            for nome in cliente_nomes_for_filter:
                menu_filter_cliente.add_command(label=nome, command=tk._setit(self.filter_cliente_var, nome))
            self.filter_cliente_var.set(cliente_nomes_for_filter[0])

        self.update_pontos_display()

    def update_pontos_display(self, *args):
        selected_client_display = self.selected_cliente_var.get()
        if selected_client_display == "-- Selecione --":
            self.pontos_disponiveis_label.config(text="Pontos do Cliente: N/A")
            self.pontos_utilizar_entry.delete(0, tk.END)
            self.pontos_utilizar_entry.insert(0, "0")
            self.utilizar_valor_label.config(text="Valor Utilizado: R$ 0.00")
            self.apply_points_discount_button.config(state=tk.DISABLED)
        else:
            cliente_id = self.clientes_dict[selected_client_display]
            pontos = self.clientes_pontos_dict.get(cliente_id, 0)
            self.pontos_disponiveis_label.config(text=f"Pontos do Cliente: {pontos}")
            self.apply_points_discount_button.config(state=tk.NORMAL)

    def create_vendedor_cliente_selection(self, parent_frame):
        # Seleção de Vendedor
        ttk.Label(parent_frame, text="Vendedor:").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        self.vendedor_dropdown.grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        ttk.Button(parent_frame, text="Novo", command=lambda: messagebox.showinfo("Info", "Crie vendedores na aba de Gerenciar Vendedores.")).grid(row=0, column=2, padx=5)

        # Seleção de Cliente
        ttk.Label(parent_frame, text="Cliente:").grid(row=1, column=0, sticky="w", pady=5, padx=5)
        self.cliente_dropdown.grid(row=1, column=1, sticky="ew", pady=5, padx=5)
        
        ttk.Button(parent_frame, text="Novo Cliente", command=self.open_add_cliente_popup).grid(row=1, column=2, padx=5)


    def open_add_cliente_popup(self):
        from clientes_gui import ClientesGUI

        popup = tk.Toplevel(self.master)
        popup.title("Cadastrar Novo Cliente")
        popup.geometry("500x300")
        popup.grab_set()

        ttk.Label(popup, text="Nome:").grid(row=0, column=0, padx=5, pady=5)
        name_entry = ttk.Entry(popup, width=40)
        name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(popup, text="Telefone:").grid(row=1, column=0, padx=5, pady=5)
        tel_entry = ttk.Entry(popup, width=40)
        tel_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(popup, text="Email:").grid(row=2, column=0, padx=5, pady=5)
        email_entry = ttk.Entry(popup, width=40)
        email_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(popup, text="Data Nasc. (AAAA-MM-DD):").grid(row=3, column=0, padx=5, pady=5)
        dob_entry = ttk.Entry(popup, width=40)
        dob_entry.grid(row=3, column=1, padx=5, pady=5)

        def save_and_close():
            nome = name_entry.get().strip()
            telefone = tel_entry.get().strip()
            email = email_entry.get().strip()
            data_nascimento = dob_entry.get().strip()

            if not nome:
                messagebox.showerror("Erro", "Nome do cliente é obrigatório.", parent=popup)
                return

            conn_popup = self.get_db_connection()
            cursor_popup = conn_popup.cursor()
            try:
                cursor_popup.execute("INSERT INTO clientes (nome, telefone, email, data_nascimento, pontos) VALUES (?, ?, ?, ?, 0)",
                                   (nome, telefone, email, data_nascimento))
                conn_popup.commit()
                messagebox.showinfo("Sucesso", f"Cliente '{nome}' cadastrado!", parent=popup)
                self._load_vendedores_clientes_for_dropdowns()
                self.selected_cliente_var.set(f"{nome} (Pontos: 0)")
                popup.destroy()
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed: clientes.email" in str(e):
                    messagebox.showerror("Erro", "Erro: Já existe um cliente com este e-mail.", parent=popup)
                else:
                    messagebox.showerror("Erro", f"Erro ao cadastrar cliente: {e}", parent=popup)
            except Exception as e:
                messagebox.showerror("Erro", f"Erro: {e}", parent=popup)
            finally:
                conn_popup.close()

        ttk.Button(popup, text="Cadastrar e Selecionar", command=save_and_close, style='Accent.TButton').grid(row=4, column=0, columnspan=2, pady=10)
        popup.focus_set()


    def create_input_widgets(self, parent_frame):
        ttk.Label(parent_frame, text="SKU do Produto:").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        self.sku_entry = ttk.Entry(parent_frame, width=30)
        self.sku_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        self.sku_entry.bind("<Return>", lambda event=None: self.add_item_to_cart())

        ttk.Label(parent_frame, text="Quantidade:").grid(row=0, column=2, sticky="w", pady=5, padx=5)
        self.quantidade_entry = ttk.Entry(parent_frame, width=10)
        self.quantidade_entry.grid(row=0, column=3, sticky="ew", pady=5, padx=5)
        self.quantidade_entry.insert(0, "1")
        self.quantidade_entry.bind("<Return>", lambda event=None: self.add_item_to_cart())

        ttk.Button(parent_frame, text="Adicionar", command=self.add_item_to_cart, style='Accent.TButton').grid(row=0, column=4, padx=5, sticky="ew")
        ttk.Button(parent_frame, text="Limpar", command=self.clear_cart, style='Danger.TButton').grid(row=0, column=5, padx=5, sticky="ew")


    def create_carrinho_widgets(self, parent_frame):
        columns = ("SKU", "Produto", "Qtd", "Preço Unit.", "Subtotal")
        self.cart_tree = ttk.Treeview(parent_frame, columns=columns, show="headings", selectmode="browse")

        for col in columns:
            self.cart_tree.heading(col, text=col)
            if col == "Qtd":
                self.cart_tree.column(col, width=50, anchor="center")
            elif col == "Preço Unit.":
                self.cart_tree.column(col, width=90, anchor="e")
            elif col == "Subtotal":
                self.cart_tree.column(col, width=90, anchor="e")
            else:
                self.cart_tree.column(col, width=100, anchor="center")
        
        self.cart_tree.column("Produto", width=250, anchor="w")

        self.cart_tree.pack(fill="both", expand=True)

        ttk.Button(parent_frame, text="Remover Item Selecionado", command=self.remove_item_from_cart, style='Danger.TButton').pack(pady=5)

    def create_desconto_juros_pontos_widgets(self, parent_frame):
        parent_frame.columnconfigure(1, weight=1)
        parent_frame.columnconfigure(2, weight=1)
        
        ttk.Label(parent_frame, text="Tipo de Desconto:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.desconto_tipo_var = tk.StringVar(value="Percentual")
        ttk.Radiobutton(parent_frame, text="%", value="Percentual", variable=self.desconto_tipo_var, command=self.update_total_with_discount).grid(row=0, column=1, sticky="w", padx=5, pady=2)
        ttk.Radiobutton(parent_frame, text="R$", value="Bruto", variable=self.desconto_tipo_var, command=self.update_total_with_discount).grid(row=0, column=2, sticky="w", padx=5, pady=2)

        ttk.Label(parent_frame, text="Valor do Desconto:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.desconto_entry = ttk.Entry(parent_frame, textvariable=self.desconto_entry_var, width=15)
        self.desconto_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        self.desconto_entry_var.set("0.00")
        self.desconto_entry.bind("<KeyRelease>", lambda event=None: self.update_total_with_discount())
        self.desconto_entry.bind("<FocusOut>", lambda event=None: self.fill_default_if_empty(self.desconto_entry_var, "0.00")) # NOVO

        self.desconto_aplicado_label = ttk.Label(parent_frame, text="Desconto Aplicado: R$ 0.00", font=("Arial", 10))
        self.desconto_aplicado_label.grid(row=1, column=2, columnspan=2, sticky="w", padx=5, pady=2)

        # Adição dos Widgets de Juros
        ttk.Label(parent_frame, text="Tipo de Juros:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.juros_tipo_var = tk.StringVar(value="Percentual")
        ttk.Radiobutton(parent_frame, text="%", value="Percentual", variable=self.juros_tipo_var, command=self.update_total_with_discount).grid(row=3, column=1, sticky="w", padx=5, pady=2)
        ttk.Radiobutton(parent_frame, text="R$", value="Bruto", variable=self.juros_tipo_var, command=self.update_total_with_discount).grid(row=3, column=2, sticky="w", padx=5, pady=2)

        ttk.Label(parent_frame, text="Valor dos Juros:").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        self.juros_entry = ttk.Entry(parent_frame, textvariable=self.juros_entry_var, width=15)
        self.juros_entry.grid(row=4, column=1, sticky="ew", padx=5, pady=2)
        self.juros_entry_var.set("0.00")
        self.juros_entry.bind("<KeyRelease>", lambda event=None: self.update_total_with_discount())
        self.juros_entry.bind("<FocusOut>", lambda event=None: self.fill_default_if_empty(self.juros_entry_var, "0.00")) # NOVO

        self.juros_aplicados_label = ttk.Label(parent_frame, text="Juros Aplicados: R$ 0.00", font=("Arial", 10))
        self.juros_aplicados_label.grid(row=4, column=2, columnspan=2, sticky="w", padx=5, pady=2)


        ttk.Separator(parent_frame, orient="horizontal").grid(row=5, column=0, columnspan=4, sticky="ew", pady=5)

        ttk.Label(parent_frame, text="Pontos Disponíveis:").grid(row=6, column=0, sticky="w", padx=5, pady=2)
        self.pontos_disponiveis_label = ttk.Label(parent_frame, text="Pontos do Cliente: N/A", font=("Arial", 10, "bold"), foreground="blue")
        self.pontos_disponiveis_label.grid(row=6, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(parent_frame, text="Pontos para Utilizar:").grid(row=7, column=0, sticky="w", padx=5, pady=2)
        self.pontos_utilizar_entry = ttk.Entry(parent_frame, width=15)
        self.pontos_utilizar_entry.grid(row=7, column=1, sticky="ew", padx=5, pady=2)
        self.pontos_utilizar_entry.insert(0, "0")
        self.pontos_utilizar_entry.bind("<KeyRelease>", lambda event=None: self.calculate_points_redeem_value())

        self.utilizar_valor_label = ttk.Label(parent_frame, text="Valor Utilizado: R$ 0.00", font=("Arial", 10))
        self.utilizar_valor_label.grid(row=7, column=2, sticky="w", padx=5, pady=2)

        self.apply_points_discount_button = ttk.Button(parent_frame, text="Aplicar Utilização de Pontos", command=self.apply_points_discount, style='Accent.TButton')
        self.apply_points_discount_button.grid(row=8, column=0, columnspan=4, pady=5)
        self.apply_points_discount_button.config(state=tk.DISABLED)

    def fill_default_if_empty(self, string_var, default_value): # NOVO MÉTODO
        if not string_var.get().strip():
            string_var.set(default_value)
            self.update_total_with_discount()


    def create_total_pagamento_widgets(self, parent_frame):
        # Frame para os Labels de total
        total_labels_frame = ttk.Frame(parent_frame)
        total_labels_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=5, pady=5)
        total_labels_frame.columnconfigure(0, weight=1)

        self.total_bruto_label = ttk.Label(total_labels_frame, text=f"Total Bruto: R$ {self.total_venda:.2f}", font=("Arial", 14, "bold"))
        self.total_bruto_label.pack(anchor="w", pady=2)

        self.total_final_label = ttk.Label(total_labels_frame, text=f"TOTAL A PAGAR: R$ {self.total_final_com_desconto:.2f}", font=("Arial", 20, "bold"), foreground="green")
        self.total_final_label.pack(anchor="w", pady=5)

        # Frame para opções de pagamento
        payment_options_frame = ttk.Frame(parent_frame)
        payment_options_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=5, pady=5)
        payment_options_frame.columnconfigure(0, weight=1)

        # Forma de Pagamento
        ttk.Label(payment_options_frame, text="Forma de Pagamento:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.forma_pagamento_var.trace_add("write", self.toggle_payment_options_visibility)
        # self.forma_pagamento_options já foram definidas no __init__
        self.forma_pagamento_menu = ttk.OptionMenu(payment_options_frame, self.forma_pagamento_var, self.forma_pagamento_options[0], *self.forma_pagamento_options)
        self.forma_pagamento_menu.grid(row=1, column=0, sticky="ew", padx=5, pady=2)

        # Tipo de Cartão (criados aqui e referenciados por self.)
        self.tipo_cartao_label = ttk.Label(payment_options_frame, text="Tipo Cartão:")
        self.tipo_cartao_var = tk.StringVar(value="Crédito")
        # self.tipo_cartao_options já foram definidas no __init__
        self.tipo_cartao_menu = ttk.OptionMenu(payment_options_frame, self.tipo_cartao_var, self.tipo_cartao_options[0], *self.tipo_cartao_options)

        # Parcelamento (criados aqui e referenciados por self.)
        self.parcelas_label = ttk.Label(payment_options_frame, text="Parcelas:")
        self.parcelas_options = ["1x", "2x", "3x"]
        self.parcelas_menu = ttk.OptionMenu(payment_options_frame, self.parcelas_var, self.parcelas_options[0], *self.parcelas_options)

        # Botão Finalizar Venda
        ttk.Button(payment_options_frame, text="Finalizar Venda", command=self.finalize_sale, style='Accent.TButton').grid(row=4, column=0, sticky="ew", padx=5, pady=10)


    def toggle_payment_options_visibility(self, *args):
        # Esconde todos os campos primeiro
        self.tipo_cartao_label.grid_forget()
        self.tipo_cartao_menu.grid_forget()
        self.parcelas_label.grid_forget()
        self.parcelas_menu.grid_forget()
        
        self.parcelas_var.set("1x") # Reseta para 1x por padrão

        forma_pagamento_selecionada = self.forma_pagamento_var.get()
        if forma_pagamento_selecionada == "Cartao":
            self.tipo_cartao_label.grid(row=2, column=0, sticky="w", padx=5, pady=2)
            self.tipo_cartao_menu.grid(row=3, column=0, sticky="ew", padx=5, pady=2)
            self.parcelas_var.set("1x")

        elif forma_pagamento_selecionada == "A Prazo":
            self.parcelas_label.grid(row=2, column=0, sticky="w", padx=5, pady=2)
            self.parcelas_menu.grid(row=3, column=0, sticky="ew", padx=5, pady=2)
            self.tipo_cartao_var.set("Crédito")


    def create_historico_widgets(self, parent_frame):
        # Cria um sub-frame para os controles de filtro que usará GRID
        filter_controls_frame = ttk.Frame(parent_frame, padding="5")
        filter_controls_frame.pack(pady=5, fill="x")

        # Configura as colunas do filter_controls_frame para usar grid
        for i in range(8): # Ajusta para caber mais filtros em largura
            filter_controls_frame.columnconfigure(i, weight=1)
        
        ttk.Label(filter_controls_frame, text="De:").grid(row=0, column=0, sticky="w", padx=2, pady=2)
        self.data_inicio_entry = ttk.Entry(filter_controls_frame, width=12)
        self.data_inicio_entry.grid(row=0, column=1, sticky="ew", padx=2, pady=2)
        self.data_inicio_entry.insert(0, (datetime.now().replace(day=1)).strftime("%Y-%m-%d"))
        
        ttk.Label(filter_controls_frame, text="Até:").grid(row=0, column=2, sticky="w", padx=2, pady=2)
        self.data_fim_entry = ttk.Entry(filter_controls_frame, width=12)
        self.data_fim_entry.grid(row=0, column=3, sticky="ew", padx=2, pady=2)
        self.data_fim_entry.insert(0, (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")) # Termina amanhã para incluir hoje

        ttk.Label(filter_controls_frame, text="Pagamento:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        # self.filter_pagamento_var já inicializado no __init__
        self.filter_pagamento_menu = ttk.OptionMenu(filter_controls_frame, self.filter_pagamento_var, self.filter_pagamento_options[0], *self.filter_pagamento_options)
        self.filter_pagamento_menu.grid(row=1, column=1, sticky="ew", padx=2, pady=2)

        ttk.Label(filter_controls_frame, text="Tipo Cartão:").grid(row=0, column=4, sticky="w", padx=5, pady=5)
        # self.filter_tipo_cartao_var já inicializado no __init__
        self.filter_tipo_cartao_menu = ttk.OptionMenu(filter_controls_frame, self.filter_tipo_cartao_var, self.filter_tipo_cartao_options[0], *self.filter_tipo_cartao_options)
        self.filter_tipo_cartao_menu.grid(row=0, column=5, sticky="ew", padx=5, pady=5)

        ttk.Label(filter_controls_frame, text="Vendedor:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        # self.filter_vendedor_var já inicializado no __init__
        self.filter_vendedor_menu = ttk.OptionMenu(filter_controls_frame, self.filter_vendedor_var, "Todos") # Reatribui aqui para ser filho do filter_controls_frame
        self.filter_vendedor_menu.grid(row=2, column=1, sticky="ew", padx=2, pady=2)

        ttk.Label(filter_controls_frame, text="Cliente:").grid(row=2, column=2, sticky="w", padx=5, pady=2)
        # self.filter_cliente_var já inicializado no __init__
        self.filter_cliente_menu = ttk.OptionMenu(filter_controls_frame, self.filter_cliente_var, "Todos") # Reatribui aqui para ser filho do filter_controls_frame
        self.filter_cliente_menu.grid(row=2, column=3, sticky="ew", padx=2, pady=2)

        ttk.Label(filter_controls_frame, text="Status Parcela:").grid(row=1, column=6, sticky="w", padx=5, pady=2)
        # self.filter_status_parcela_var já inicializado no __init__
        self.filter_status_parcela_menu = ttk.OptionMenu(filter_controls_frame, self.filter_status_parcela_var, self.filter_status_parcela_options[0], *self.filter_status_parcela_options)
        self.filter_status_parcela_menu.grid(row=1, column=7, sticky="ew", padx=2, pady=2)


        ttk.Button(filter_controls_frame, text="Filtrar", command=self.load_vendas_historico).grid(row=2, column=4, columnspan=4, padx=10, sticky="ew")

        # Treeview para o histórico (ainda filho de parent_frame, que é frame_historico_tab)
        columns_hist = ("ID Venda", "Data/Hora", "Total", "Desconto", "Juros", "Pontos Utilizados", "Total Final", "Forma Pgto", "Tipo Cartão", "Parcelas", "Vendedor", "Cliente")
        self.historico_tree = ttk.Treeview(parent_frame, columns=columns_hist, show="headings", selectmode="browse")

        for col in columns_hist:
            self.historico_tree.heading(col, text=col)
            if col == "ID Venda":
                self.historico_tree.column(col, width=70, anchor="center")
            elif col == "Data/Hora":
                self.historico_tree.column(col, width=150, anchor="center")
            elif col in ["Total", "Desconto", "Juros", "Total Final"]:
                self.historico_tree.column(col, width=90, anchor="e")
            elif col == "Pontos Utilizados":
                self.historico_tree.column(col, width=90, anchor="center")
            elif col == "Forma Pgto":
                self.historico_tree.column(col, width=90, anchor="center")
            elif col == "Tipo Cartão":
                self.historico_tree.column(col, width=90, anchor="center")
            elif col == "Parcelas":
                self.historico_tree.column(col, width=70, anchor="center")
            elif col in ["Vendedor", "Cliente"]:
                self.historico_tree.column(col, width=100, anchor="w")

        self.historico_tree.pack(fill="both", expand=True)

        ttk.Button(parent_frame, text="Ver Detalhes da Venda", command=self.show_venda_details).pack(pady=5)


    def add_item_to_cart(self):
        sku = self.sku_entry.get().strip().upper()
        quantidade_str = self.quantidade_entry.get().strip()

        if not sku:
            messagebox.showwarning("Aviso", "Por favor, digite o SKU do produto.")
            return
        if not quantidade_str:
            messagebox.showwarning("Aviso", "Por favor, digite a quantidade.")
            return

        try:
            quantidade = int(quantidade_str)
            if quantidade <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Quantidade inválida. Digite um número inteiro positivo.")
            return

        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, preco_venda, quantidade FROM produtos WHERE sku = ?", (sku,))
        produto = cursor.fetchone()
        conn.close()

        if not produto:
            messagebox.showerror("Erro", "Produto não encontrado com este SKU.")
            return

        if quantidade > produto['quantidade']:
            messagebox.showwarning("Estoque Insuficiente", f"Estoque insuficiente para '{produto['nome']}'. Disponível: {produto['quantidade']}")
            return

        found_in_cart = False
        for item in self.carrinho:
            if item['sku'] == sku:
                item['quantidade'] += quantidade
                found_in_cart = True
                break
        
        if not found_in_cart:
            self.carrinho.append({
                'product_id': produto['id'],
                'sku': sku,
                'nome': produto['nome'],
                'quantidade': quantidade,
                'preco_unitario': produto['preco_venda']
            })
        
        self.update_cart_display()
        self.sku_entry.delete(0, tk.END)
        self.quantidade_entry.delete(0, tk.END)
        self.quantidade_entry.insert(0, "1")
        self.sku_entry.focus_set()

    def update_cart_display(self):
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        
        self.total_venda = 0.0
        for item in self.carrinho:
            subtotal = item['quantidade'] * item['preco_unitario']
            self.cart_tree.insert("", "end", values=(item['sku'], item['nome'], item['quantidade'], f"{item['preco_unitario']:.2f}", f"{subtotal:.2f}"))
            self.total_venda += subtotal
        
        self.total_bruto_label.config(text=f"Total Bruto: R$ {self.total_venda:.2f}")
        # Zera os campos de desconto, juros e pontos ao atualizar carrinho
        self.desconto_entry_var.set("0.00") # Usa o StringVar para setar o valor
        self.juros_entry_var.set("0.00") # Usa o StringVar para setar o valor
        self.pontos_utilizar_entry.delete(0, tk.END)
        self.pontos_utilizar_entry.insert(0, "0")
        self.desconto_aplicado = 0.0
        self.juros_aplicados = 0.0
        self.pontos_utilizados = 0
        self.utilizar_valor_label.config(text="Valor Utilizado: R$ 0.00")
        self.juros_aplicados_label.config(text="Juros Aplicados: R$ 0.00")
        self.juros_tipo_var.set("Percentual")

        self.update_total_with_discount()

    def update_total_with_discount(self):
        # Desconto manual
        try:
            desconto_manual_valor = float(self.desconto_entry_var.get().replace(',', '.')) # Pega do StringVar
        except ValueError:
            desconto_manual_valor = 0.0

        self.desconto_aplicado = 0.0
        if self.desconto_tipo_var.get() == "Percentual":
            if 0 <= desconto_manual_valor <= 100:
                self.desconto_aplicado = self.total_venda * (desconto_manual_valor / 100)
            else:
                self.desconto_aplicado = 0.0
        elif self.desconto_tipo_var.get() == "Bruto":
            if 0 <= desconto_manual_valor <= self.total_venda:
                self.desconto_aplicado = desconto_manual_valor
            else:
                self.desconto_aplicado = 0.0

        # Juros
        try:
            juros_valor_input = float(self.juros_entry_var.get().replace(',', '.')) # Pega do StringVar
        except ValueError:
            juros_valor_input = 0.0

        self.juros_aplicados = 0.0
        subtotal_pos_desconto_e_pontos = self.total_venda - self.desconto_aplicado - (self.pontos_utilizados * self.VALOR_POR_PONTO)

        if self.juros_tipo_var.get() == "Percentual":
            if juros_valor_input >= 0:
                self.juros_aplicados = subtotal_pos_desconto_e_pontos * (juros_valor_input / 100)
            else:
                self.juros_aplicados = 0.0
        elif self.juros_tipo_var.get() == "Bruto":
            if juros_valor_input >= 0:
                self.juros_aplicados = juros_valor_input
            else:
                self.juros_aplicados = 0.0


        # Cálculo do total final
        self.total_final_com_desconto = subtotal_pos_desconto_e_pontos + self.juros_aplicados
        
        # Garante que o total final não seja negativo
        if self.total_final_com_desconto < 0:
            self.total_final_com_desconto = 0.0


        self.desconto_aplicado = round(self.desconto_aplicado, 2)
        self.juros_aplicados = round(self.juros_aplicados, 2)
        self.total_final_com_desconto = round(self.total_final_com_desconto, 2)

        self.desconto_aplicado_label.config(text=f"Desconto Aplicado: R$ {self.desconto_aplicado:.2f}")
        self.juros_aplicados_label.config(text=f"Juros Aplicados: R$ {self.juros_aplicados:.2f}")
        self.total_final_label.config(text=f"TOTAL A PAGAR: R$ {self.total_final_com_desconto:.2f}")

    def calculate_points_redeem_value(self):
        selected_client_display = self.selected_cliente_var.get()
        if selected_client_display == "-- Selecione --":
            messagebox.showwarning("Aviso", "Selecione um cliente para utilizar pontos.")
            self.pontos_utilizar_entry.delete(0, tk.END)
            self.pontos_utilizar_entry.insert(0, "0")
            self.utilizar_valor_label.config(text="Valor Utilizado: R$ 0.00")
            return

        try:
            pontos_a_utilizar_input = int(self.pontos_utilizar_entry.get())
            if pontos_a_utilizar_input < 0:
                raise ValueError
        except ValueError:
            self.utilizar_valor_label.config(text="Valor Utilizado: R$ 0.00")
            self.pontos_utilizar_entry.delete(0, tk.END)
            self.pontos_utilizar_entry.insert(0, "0")
            return

        cliente_id = self.clientes_dict[selected_client_display]
        pontos_disponiveis = self.clientes_pontos_dict.get(cliente_id, 0)

        if pontos_a_utilizar_input > pontos_disponiveis:
            messagebox.showwarning("Aviso", f"Pontos insuficientes. Cliente tem {pontos_disponiveis} pontos.", parent=self.master)
            self.pontos_utilizar_entry.delete(0, tk.END)
            self.pontos_utilizar_entry.insert(0, str(pontos_disponiveis))
            pontos_a_utilizar = pontos_disponiveis
        else:
            pontos_a_utilizar = pontos_a_utilizar_input

        valor_utilizado = pontos_a_utilizar * self.VALOR_POR_PONTO
        self.utilizar_valor_label.config(text=f"Valor Utilizado: R$ {valor_utilizado:.2f}")

    def apply_points_discount(self):
        selected_client_display = self.selected_cliente_var.get()
        if selected_client_display == "-- Selecione --":
            messagebox.showwarning("Aviso", "Selecione um cliente para aplicar a utilização de pontos.")
            return

        try:
            pontos_input = int(self.pontos_utilizar_entry.get())
            if pontos_input < 0: raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Número de pontos inválido.")
            return

        cliente_id = self.clientes_dict[selected_client_display]
        pontos_disponiveis = self.clientes_pontos_dict.get(cliente_id, 0)

        if pontos_input > pontos_disponiveis:
            messagebox.showwarning("Aviso", "O valor de utilização de pontos excede os pontos disponíveis. Aplicando o máximo possível.", parent=self.master)
            self.pontos_utilizar_entry.delete(0, tk.END)
            self.pontos_utilizar_entry.insert(0, str(pontos_disponiveis))
            pontos_a_utilizar = pontos_disponiveis
        else:
            pontos_a_utilizar = pontos_input

        valor_desconto_pontos = pontos_a_utilizar * self.VALOR_POR_PONTO

        # Calcula o subtotal para ver o máximo de desconto de pontos aplicável
        current_desconto_manual_valor = 0.0
        try:
            desconto_manual_str = self.desconto_entry_var.get().replace(',', '.')
            if self.desconto_tipo_var.get() == "Percentual":
                desconto_percent = float(desconto_manual_str)
                current_desconto_manual_valor = self.total_venda * (desconto_percent / 100)
            elif self.desconto_tipo_var.get() == "Bruto":
                current_desconto_manual_valor = float(desconto_manual_str)
        except ValueError:
            current_desconto_manual_valor = 0.0
        
        # Considera juros já calculados no remaining_total
        # Ajustei o cálculo aqui para usar o total_venda menos o desconto manual (e antes dos juros)
        # para a validação do valor máximo de pontos.
        total_para_validar_pontos = self.total_venda - current_desconto_manual_valor 

        if valor_desconto_pontos > total_para_validar_pontos:
            messagebox.showwarning("Aviso", "O valor de utilização de pontos excede o total restante da venda. Aplicando o máximo possível.", parent=self.master)
            valor_desconto_pontos = total_para_validar_pontos
            pontos_a_utilizar = int(valor_desconto_pontos / self.VALOR_POR_PONTO)

        self.pontos_utilizados = pontos_a_utilizar
        self.utilizar_valor_label.config(text=f"Valor Utilizado: R$ {valor_desconto_pontos:.2f}")
        self.pontos_utilizar_entry.delete(0, tk.END)
        self.pontos_utilizar_entry.insert(0, str(self.pontos_utilizados))
        self.update_total_with_discount()


    def remove_item_from_cart(self):
        selected_item = self.cart_tree.focus()
        if not selected_item:
            messagebox.showwarning("Aviso", "Nenhum item selecionado no carrinho para remover.")
            return
        
        item_sku = self.cart_tree.item(selected_item, 'values')[0]
        
        self.carrinho = [item for item in self.carrinho if item['sku'] != item_sku]
        self.update_cart_display()

    def clear_cart(self):
        if messagebox.askyesno("Limpar Carrinho", "Tem certeza que deseja limpar todo o carrinho?"):
            self.carrinho = []
            self.total_venda = 0.0
            self.desconto_aplicado = 0.0
            self.juros_aplicados = 0.0
            self.total_final_com_desconto = 0.0
            self.pontos_utilizados = 0
            self.desconto_entry_var.set("0.00")
            self.juros_entry_var.set("0.00")
            self.pontos_utilizar_entry.delete(0, tk.END)
            self.pontos_utilizar_entry.insert(0, "0")
            self.utilizar_valor_label.config(text="Valor Utilizado: R$ 0.00")
            self.juros_aplicados_label.config(text="Juros Aplicados: R$ 0.00")
            self.juros_tipo_var.set("Percentual")

            self.update_cart_display()
            messagebox.showinfo("Carrinho Limpo", "O carrinho foi esvaziado.")
            self.sku_entry.focus_set()

    def finalize_sale(self):
        if not self.carrinho:
            messagebox.showwarning("Aviso", "O carrinho está vazio. Adicione itens para finalizar a venda.")
            return
        
        # Validação do desconto
        try:
            desconto_valor_input = float(self.desconto_entry_var.get().replace(',', '.'))
        except ValueError:
            messagebox.showerror("Erro de Validação", "Valor do desconto inválido. Use um número.", parent=self.master)
            return

        if self.desconto_tipo_var.get() == "Percentual" and not (0 <= desconto_valor_input <= 100):
            messagebox.showerror("Erro de Validação", "Porcentagem de desconto deve ser entre 0 e 100.", parent=self.master)
            return
        if self.desconto_tipo_var.get() == "Bruto" and not (0 <= desconto_valor_input <= self.total_venda):
            messagebox.showerror("Erro de Validação", "Valor do desconto bruto não pode ser negativo ou maior que o total da venda.", parent=self.master)
            return
        
        # Validação dos Juros
        try:
            juros_valor_input = float(self.juros_entry_var.get().replace(',', '.'))
        except ValueError:
            messagebox.showerror("Erro de Validação", "Valor dos juros inválido. Use um número.", parent=self.master)
            return
        if self.juros_tipo_var.get() == "Percentual" and juros_valor_input < 0:
            messagebox.showerror("Erro de Validação", "Porcentagem de juros não pode ser negativa.", parent=self.master)
            return
        if self.juros_tipo_var.get() == "Bruto" and juros_valor_input < 0:
            messagebox.showerror("Erro de Validação", "Valor dos juros bruto não pode ser negativo.", parent=self.master)
            return


        self.update_total_with_discount() # Garante que todos os totais estejam atualizados

        selected_vendedor_name = self.selected_vendedor_var.get()
        vendedor_id = None
        if selected_vendedor_name == "-- Selecione --":
            if not messagebox.askyesno("Confirmar Venda", "Nenhum vendedor selecionado. Deseja continuar a venda assim?"):
                return
        else:
            vendedor_id = self.vendedores_dict[selected_vendedor_name]

        selected_cliente_display = self.selected_cliente_var.get()
        cliente_id = None
        if selected_cliente_display == "-- Selecione --":
            if self.pontos_utilizados > 0:
                messagebox.showerror("Erro", "Não é possível utilizar pontos sem selecionar um cliente.")
                return
            if not messagebox.askyesno("Confirmar Venda", "Nenhum cliente selecionado. Deseja continuar a venda assim?"):
                return
        else:
            cliente_id = self.clientes_dict[selected_cliente_display]

        # Coleta informações de pagamento e parcelamento
        forma_pagamento = self.forma_pagamento_var.get()
        tipo_cartao = None
        parcelas_total = 1
        parcelas_pagas = 0

        if forma_pagamento == "Cartao":
            tipo_cartao = self.tipo_cartao_var.get()
        elif forma_pagamento == "A Prazo":
            if cliente_id is None:
                messagebox.showerror("Erro", "Vendas 'A Prazo' exigem a seleção de um cliente.")
                return
            parcelas_total = int(self.parcelas_var.get().replace('x', ''))
            parcelas_pagas = 0

        if not messagebox.askyesno("Confirmar Venda", f"Confirmar venda no total de R$ {self.total_final_com_desconto:.2f}?"):
            return

        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            # 1. Registrar a Venda
            data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute("INSERT INTO vendas (data_hora, total_venda, desconto_aplicado, juros_aplicados, total_final, forma_pagamento, tipo_cartao, parcelas_total, parcelas_pagas, vendedor_id, cliente_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           (data_hora, self.total_venda, self.desconto_aplicado, self.juros_aplicados, self.total_final_com_desconto, forma_pagamento, tipo_cartao, parcelas_total, parcelas_pagas, vendedor_id, cliente_id))
            venda_id = cursor.lastrowid

            # 2. Registrar Itens da Venda e Atualizar Estoque
            for item in self.carrinho:
                cursor.execute("INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                               (venda_id, item['product_id'], item['quantidade'], item['preco_unitario']))
                
                # CORREÇÃO: Usar 'quantidade' ao invés de 'quantity' para atualizar o estoque
                cursor.execute("UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?", 
                               (item['quantidade'], item['product_id']))
            
            # 3. Gerar Parcelas se for 'A Prazo'
            if forma_pagamento == "A Prazo":
                # O valor da parcela já deve incluir os juros, pois ele se baseia no total_final_com_desconto
                valor_parcela_unit = round(self.total_final_com_desconto / parcelas_total, 2)
                
                for i in range(1, parcelas_total + 1):
                    valor = valor_parcela_unit
                    if i == parcelas_total:
                        soma_parcelas_anteriores = valor_parcela_unit * (parcelas_total - 1)
                        valor = round(self.total_final_com_desconto - soma_parcelas_anteriores, 2)

                    data_vencimento = (datetime.now() + timedelta(days=30 * i)).strftime("%Y-%m-%d")
                    cursor.execute("INSERT INTO parcelas (venda_id, numero_parcela, valor_parcela, data_vencimento, status) VALUES (?, ?, ?, ?, ?)",
                                   (venda_id, i, valor, data_vencimento, 'Pendente'))
            
            # 4. Gerenciar Pontos do Cliente
            if cliente_id:
                pontos_ganhos = int(self.total_final_com_desconto * self.PONTOS_POR_REAL)
                
                cursor.execute("UPDATE clientes SET pontos = pontos + ? - ? WHERE id = ?",
                               (pontos_ganhos, self.pontos_utilizados, cliente_id))
                
                if pontos_ganhos > 0:
                    cursor.execute("INSERT INTO movimentacoes_pontos (cliente_id, data_hora, tipo_movimentacao, pontos, referencia_id, motivo) VALUES (?, ?, ?, ?, ?, ?)",
                                   (cliente_id, data_hora, "Ganho", pontos_ganhos, venda_id, "Compra"))
                
                if self.pontos_utilizados > 0:
                    cursor.execute("INSERT INTO movimentacoes_pontos (cliente_id, data_hora, tipo_movimentacao, pontos, referencia_id, motivo) VALUES (?, ?, ?, ?, ?, ?)",
                                   (cliente_id, data_hora, "Utilizacao", self.pontos_utilizados, venda_id, "Desconto na Compra"))
            
            # 5. Registrar Movimentação no Caixa
            responsavel_id = vendedor_id
            forma_pag = forma_pagamento
            descricao_mov = f"Venda ID {venda_id}"
            
            if forma_pagamento != "A Prazo": # Entradas de vendas à vista
                cursor.execute("INSERT INTO movimentacoes_caixa (data_hora, tipo, valor, forma_pagamento, descricao, referencia_id, tabela_referencia, responsavel_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                               (data_hora, "Entrada", self.total_final_com_desconto, forma_pag, descricao_mov, venda_id, "vendas", responsavel_id))


            conn.commit()
            messagebox.showinfo("Sucesso", f"Venda ID {venda_id} finalizada com sucesso!\n"
                                f"Pontos Ganhos: {pontos_ganhos if cliente_id else 0}\n"
                                f"Pontos Utilizados: {self.pontos_utilizados}")
            
            self.clear_cart()
            self._load_vendedores_clientes_for_dropdowns()
            self.load_vendas_historico()
            self.selected_vendedor_var.set("-- Selecione --")
            self.selected_cliente_var.set("-- Selecione --")
            self.sku_entry.focus_set()
            self.forma_pagamento_var.set("Dinheiro")
            self.toggle_payment_options_visibility()


        except Exception as e:
            conn.rollback()
            messagebox.showerror("Erro", f"Erro ao finalizar venda: {e}")
        finally:
            conn.close()

    def load_vendas_historico(self):
        for item in self.historico_tree.get_children():
            self.historico_tree.delete(item)
        
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

        data_inicio = self.data_inicio_entry.get()
        data_fim = self.data_fim_entry.get()
        forma_pagamento_filtro = self.filter_pagamento_var.get()
        tipo_cartao_filtro = self.filter_tipo_cartao_var.get()
        vendedor_filtro_nome = self.filter_vendedor_var.get()
        cliente_filtro_nome = self.filter_cliente_var.get()
        status_parcela_filtro = self.filter_status_parcela_var.get()

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
            cursor_filter = conn.cursor()
            cursor_filter.execute("SELECT id FROM clientes WHERE nome = ?", (cliente_filtro_nome,))
            cliente_id_filtro_row = cursor_filter.fetchone()
            if cliente_id_filtro_row:
                cliente_id_filtro = cliente_id_filtro_row['id']
                query += " AND v.cliente_id = ?"
                params.append(cliente_id_filtro)
            else:
                pass
        
        if status_parcela_filtro != "Todos" and status_parcela_filtro != "N/A":
            query += " AND v.forma_pagamento = 'A Prazo'"
            if status_parcela_filtro == "Atrasado":
                query += f" AND v.id IN (SELECT DISTINCT venda_id FROM parcelas WHERE status = 'Pendente' AND data_vencimento < DATE('{datetime.now().strftime('%Y-%m-%d')}'))"
            else:
                query += f" AND v.id IN (SELECT DISTINCT venda_id FROM parcelas WHERE status = ?)"
                params.append(status_parcela_filtro)
        elif status_parcela_filtro == "N/A":
            query += " AND v.forma_pagamento != 'A Prazo'"


        query += " ORDER BY v.data_hora DESC"
        
        cursor.execute(query, tuple(params))
        vendas = cursor.fetchall()
        conn.close()

        for venda in vendas:
            vendedor_nome_exibicao = venda['vendedor_nome'] if venda['vendedor_nome'] else "Não Informado"
            cliente_nome_exibicao = venda['cliente_nome'] if venda['cliente_nome'] else "Não Informado"
            pontos_utilizados_exibicao = venda['pontos_utilizados_venda'] if venda['pontos_utilizados_venda'] is not None else 0
            tipo_cartao_exibicao = venda['tipo_cartao'] if venda['tipo_cartao'] else "N/A"
            
            parcelas_info = "N/A"
            if venda['forma_pagamento'] == "A Prazo":
                parcelas_info = f"{venda['parcelas_pagas']} de {venda['parcelas_total']}x"

            self.historico_tree.insert("", "end", values=(
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

    def show_venda_details(self):
        selected_item = self.historico_tree.focus()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione uma venda no histórico para ver os detalhes.")
            return
        
        venda_id = self.historico_tree.item(selected_item, 'values')[0]

        conn = self.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT v.data_hora, v.total_venda, v.desconto_aplicado, v.juros_aplicados, v.total_final, v.forma_pagamento, v.tipo_cartao, v.parcelas_total, v.parcelas_pagas,
                   vend.nome as vendedor_nome, cli.nome as cliente_nome,
                   (SELECT ABS(SUM(mp.pontos)) FROM movimentacoes_pontos mp WHERE mp.referencia_id = v.id AND mp.tipo_movimentacao = 'Utilizacao') AS pontos_utilizados_venda
            FROM vendas v
            LEFT JOIN vendedores vend ON v.vendedor_id = vend.id
            LEFT JOIN clientes cli ON v.cliente_id = cli.id
            WHERE v.id = ?
        """, (venda_id,))
        venda_info = cursor.fetchone()

        cursor.execute("""
            SELECT p.nome, iv.quantidade, iv.preco_unitario
            FROM itens_venda iv
            JOIN produtos p ON iv.produto_id = p.id
            WHERE iv.venda_id = ?
        """, (venda_id,))
        itens_venda = cursor.fetchall()

        parcelas_venda = []
        if venda_info['forma_pagamento'] == 'A Prazo':
            cursor.execute("SELECT numero_parcela, valor_parcela, data_vencimento, data_pagamento, status FROM parcelas WHERE venda_id = ? ORDER BY numero_parcela", (venda_id,))
            parcelas_venda = cursor.fetchall()

        conn.close()

        if not venda_info:
            messagebox.showerror("Erro", "Detalhes da venda não encontrados.")
            return

        details_str = f"Detalhes da Venda ID: {venda_id}\n\n"
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

        messagebox.showinfo("Detalhes da Venda", details_str)