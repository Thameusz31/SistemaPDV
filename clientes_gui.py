import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from database import DATABASE_NAME
from datetime import datetime, timedelta

class ClientesGUI(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding="15")
        self.master = master

        self.conn = self.get_db_connection()

        self.frame_form = ttk.LabelFrame(self, text="Cadastro/Edição de Cliente", padding="15")
        self.frame_form.pack(pady=10, padx=10, fill="x")
        self.frame_form.columnconfigure(1, weight=1)

        self.create_form_widgets(self.frame_form)

        self.frame_list = ttk.LabelFrame(self, text="Clientes Cadastrados", padding="15")
        self.frame_list.pack(pady=10, padx=10, fill="both", expand=True)
        self.create_list_widgets(self.frame_list)
        
        self.load_clientes()

    def get_db_connection(self):
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row
        return conn

    def create_form_widgets(self, parent_frame):
        field_configs = [
            ("Nome:", "nome"),
            ("CPF:", "cpf"),
            ("Telefone:", "telefone"),
            ("Data Nasc. (DD-MM-AAAA):", "data_nascimento"),
            ("Pontos:", "pontos")
        ]
        
        self.entries = {}
        for i, (label_text, key_name) in enumerate(field_configs):
            ttk.Label(parent_frame, text=label_text).grid(row=i, column=0, sticky="w", pady=4, padx=5)
            entry = ttk.Entry(parent_frame, width=40)
            entry.grid(row=i, column=1, sticky="ew", pady=4, padx=5)
            self.entries[key_name] = entry
        
        # --- Configuração do valor padrão para 'Pontos' ---
        self.entries["pontos"].insert(0, "0") # Adicionado para que já venha com '0'

        # --- Configuração das máscaras ---
        if "cpf" in self.entries:
            self.entries["cpf"].bind("<KeyRelease>", lambda event: self.format_cpf(self.entries["cpf"]))
        if "telefone" in self.entries:
            self.entries["telefone"].bind("<KeyRelease>", lambda event: self.format_phone(self.entries["telefone"]))
        if "data_nascimento" in self.entries:
            self.entries["data_nascimento"].bind("<KeyRelease>", lambda event: self.format_date(self.entries["data_nascimento"]))


        button_frame = ttk.Frame(parent_frame)
        button_frame.grid(row=len(field_configs), column=0, columnspan=2, pady=15)
        
        ttk.Button(button_frame, text="Salvar Cliente", command=self.add_cliente, style='Accent.TButton').pack(side="left", padx=10)
        ttk.Button(button_frame, text="Limpar Campos", command=self.clear_form).pack(side="left", padx=10)
        
        self.cliente_id_to_edit = None

    def create_list_widgets(self, parent_frame):
        columns = ("ID", "Nome", "CPF", "Telefone", "Data Nasc.", "Pontos")
        self.tree = ttk.Treeview(parent_frame, columns=columns, show="headings", selectmode="browse")

        for col in columns:
            self.tree.heading(col, text=col)
            if col == "ID":
                self.tree.column(col, width=50, anchor="center")
            elif col == "Nome":
                self.tree.column(col, width=150, anchor="w")
            elif col == "CPF":
                self.tree.column(col, width=120, anchor="center")
            elif col == "Telefone":
                self.tree.column(col, width=120, anchor="center")
            elif col == "Data Nasc.":
                self.tree.column(col, width=100, anchor="center")
            elif col == "Pontos":
                self.tree.column(col, width=70, anchor="center")
        
        self.tree.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        button_frame_list = ttk.Frame(parent_frame)
        button_frame_list.pack(pady=10)
        ttk.Button(button_frame_list, text="Editar Selecionado", command=self.edit_selected_cliente).pack(side="left", padx=5)
        ttk.Button(button_frame_list, text="Remover Selecionado", command=self.delete_selected_cliente, style='Danger.TButton').pack(side="left", padx=5)
        ttk.Button(button_frame_list, text="Ver Histórico de Compras", command=self.show_purchase_history).pack(side="left", padx=5)


    def load_clientes(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, cpf, telefone, data_nascimento, pontos FROM clientes ORDER BY nome")
        clientes = cursor.fetchall()
    
        for c in clientes:
            data_nasc_exibicao = ""
            if c['data_nascimento']:
                try:
                    data_obj = datetime.strptime(c['data_nascimento'], "%Y-%m-%d").date()
                    data_nasc_exibicao = data_obj.strftime("%d-%m-%Y")
                except ValueError:
                    data_nasc_exibicao = c['data_nascimento']

            self.tree.insert("", "end", values=(c['id'], c['nome'], c['cpf'], c['telefone'], data_nasc_exibicao, c['pontos']))
        conn.close() # Fechar a conexão aqui


    def add_cliente(self):
        nome = self.entries["nome"].get().strip()
        cpf = self.entries["cpf"].get().strip()
        telefone = self.entries["telefone"].get().strip()
        data_nascimento_input = self.entries["data_nascimento"].get().strip()
        pontos_str = self.entries["pontos"].get().strip()

        if not nome:
            messagebox.showerror("Erro de Validação", "Nome do cliente é obrigatório.")
            return
        
        try:
            pontos = int(pontos_str)
            if pontos < 0: raise ValueError
        except ValueError:
            messagebox.showerror("Erro de Validação", "Pontos devem ser um número inteiro positivo ou zero.")
            return

        data_nascimento_db = None
        if data_nascimento_input:
            try:
                data_obj = datetime.strptime(data_nascimento_input, "%d-%m-%Y").date()
                data_nascimento_db = data_obj.strftime("%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Erro de Validação", "Formato de Data de Nascimento inválido. Use DD-MM-AAAA.")
                return

        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            if self.cliente_id_to_edit:
                cursor.execute("""
                    UPDATE clientes SET
                    nome = ?, cpf = ?, telefone = ?, data_nascimento = ?, pontos = ?
                    WHERE id = ?
                """, (nome, cpf, telefone, data_nascimento_db, pontos, self.cliente_id_to_edit))
                messagebox.showinfo("Sucesso", "Cliente atualizado com sucesso!")
            else:
                cursor.execute("INSERT INTO clientes (nome, cpf, telefone, data_nascimento, pontos) VALUES (?, ?, ?, ?, ?)",
                               (nome, cpf, telefone, data_nascimento_db, pontos))
                messagebox.showinfo("Sucesso", f"Cliente '{nome}' cadastrado com sucesso!")
            
            conn.commit()
            self.load_clientes()
            self.clear_form()

        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: clientes.cpf" in str(e):
                messagebox.showerror("Erro", f"Erro: Já existe um cliente com o CPF '{cpf}'.")
            else:
                messagebox.showerror("Erro", f"Erro ao salvar cliente: {e}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar cliente: {e}")
        finally:
            conn.close()

    def clear_form(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.entries["pontos"].insert(0, "0") # Garante que o padrão seja 0 ao limpar
        self.cliente_id_to_edit = None
        self.winfo_toplevel().title("Sistema Loja Streetwear - Gestão Integrada")
        self.frame_form.config(text="Cadastro/Edição de Cliente")
        
    def edit_selected_cliente(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Aviso", "Nenhum cliente selecionado para edição.")
            return

        values = self.tree.item(selected_item, 'values')
        cliente_id = values[0]

        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,))
        cliente_data = cursor.fetchone()
        conn.close()

        if cliente_data:
            self.clear_form()
            self.entries["nome"].insert(0, cliente_data['nome'])
            self.entries["cpf"].insert(0, cliente_data['cpf'] if cliente_data['cpf'] else "")
            self.entries["telefone"].insert(0, cliente_data['telefone'] if cliente_data['telefone'] else "")
            
            data_nasc_exibicao = ""
            if cliente_data['data_nascimento']:
                try:
                    data_obj = datetime.strptime(cliente_data['data_nascimento'], "%Y-%m-%d").date()
                    data_nasc_exibicao = data_obj.strftime("%d-%m-%Y")
                except ValueError:
                    data_nasc_exibicao = cliente_data['data_nascimento']
            self.entries["data_nascimento"].insert(0, data_nasc_exibicao)
            
            self.entries["pontos"].insert(0, str(cliente_data['pontos']))
            
            self.cliente_id_to_edit = cliente_id
            self.winfo_toplevel().title(f"Sistema Loja Streetwear - Editando Cliente: {cliente_data['nome']}")
            self.frame_form.config(text=f"Editando Cliente: {cliente_data['nome']}")

    def delete_selected_cliente(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Aviso", "Nenhum cliente selecionado para remoção.")
            return

        cliente_id = self.tree.item(selected_item, 'values')[0]
        cliente_nome = self.tree.item(selected_item, 'values')[1]

        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM vendas WHERE cliente_id = ?", (cliente_id,))
        num_vendas = cursor.fetchone()[0]
        conn.close()

        if num_vendas > 0:
            messagebox.showerror("Erro", f"Não é possível remover o cliente '{cliente_nome}' pois ele está associado a {num_vendas} venda(s).")
            return

        if messagebox.askyesno("Confirmar Remoção", f"Tem certeza que deseja remover o cliente '{cliente_nome}'?"):
            conn = self.get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM movimentacoes_pontos WHERE cliente_id = ?", (cliente_id,))
                cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
                conn.commit()
                messagebox.showinfo("Sucesso", "Cliente removido com sucesso!")
                self.load_clientes()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao remover cliente: {e}")
            finally:
                conn.close()

    def show_purchase_history(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione um cliente para ver o histórico de compras.")
            return
        
        cliente_id = self.tree.item(selected_item, 'values')[0]
        cliente_nome = self.tree.item(selected_item, 'values')[1]

        conn = self.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT v.id, v.data_hora, v.total_venda, v.desconto_aplicado, v.juros_aplicados, v.total_final, v.forma_pagamento, 
                   vend.nome as vendedor_nome, v.tipo_cartao, v.parcelas_total, v.parcelas_pagas,
                   (SELECT ABS(SUM(mp.pontos)) FROM movimentacoes_pontos mp WHERE mp.referencia_id = v.id AND mp.tipo_movimentacao = 'Utilizacao') AS pontos_utilizados_venda
            FROM vendas v
            LEFT JOIN vendedores vend ON v.vendedor_id = vend.id
            WHERE v.cliente_id = ?
            ORDER BY v.data_hora DESC
        """, (cliente_id,))
        vendas = cursor.fetchall()
        conn.close()

        if not vendas:
            messagebox.showinfo("Histórico de Compras", f"O cliente '{cliente_nome}' não possui histórico de compras registrado.", parent=self.winfo_toplevel())
            return

        history_window = tk.Toplevel(self.winfo_toplevel())
        history_window.title(f"Histórico de Compras de {cliente_nome}")
        history_window.geometry("950x550")
        history_window.grab_set()

        ttk.Label(history_window, text=f"Histórico de Compras de: {cliente_nome}", font=("Arial", 14, "bold")).pack(pady=10)

        columns = ("ID Venda", "Data/Hora", "Total Bruto", "Desconto", "Juros", "Pontos Utilizados", "Total Final", "Forma Pgto", "Tipo Cartão", "Parcelas", "Vendedor")
        history_tree = ttk.Treeview(history_window, columns=columns, show="headings", selectmode="browse")

        for col in columns:
            history_tree.heading(col, text=col)
            if col == "ID Venda":
                history_tree.column(col, width=70, anchor="center")
            elif col == "Data/Hora":
                history_tree.column(col, width=130, anchor="center")
            elif col in ["Total Bruto", "Desconto", "Juros", "Total Final"]:
                history_tree.column(col, width=90, anchor="e")
            elif col == "Pontos Utilizados":
                history_tree.column(col, width=90, anchor="center")
            elif col == "Forma Pgto":
                history_tree.column(col, width=90, anchor="center")
            elif col == "Tipo Cartão":
                history_tree.column(col, width=90, anchor="center")
            elif col == "Parcelas":
                history_tree.column(col, width=70, anchor="center")
            elif col == "Vendedor":
                history_tree.column(col, width=100, anchor="w")
            else:
                history_tree.column(col, width=80, anchor="center")

        history_tree.pack(fill="both", expand=True, padx=10, pady=10)

        for venda in vendas:
            vendedor_nome_exibicao = venda['vendedor_nome'] if venda['vendedor_nome'] else "N/A"
            pontos_utilizados_exibicao = venda['pontos_utilizados_venda'] if venda['pontos_utilizados_venda'] is not None else 0
            tipo_cartao_exibicao = venda['tipo_cartao'] if venda['tipo_cartao'] else "N/A"
            parcelas_info = "N/A"
            if venda['forma_pagamento'] == "A Prazo":
                parcelas_info = f"{venda['parcelas_pagas']} de {venda['parcelas_total']}x"

            history_tree.insert("", "end", values=(
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
                vendedor_nome_exibicao
            ))
        
        def view_selected_sale_details():
            selected_sale_item = history_tree.focus()
            if not selected_sale_item:
                messagebox.showwarning("Aviso", "Selecione uma venda para ver os detalhes.", parent=history_window)
                return
            sale_id = history_tree.item(selected_sale_item, 'values')[0]
            
            self._show_sale_details_common(sale_id, history_window)

        ttk.Button(history_window, text="Ver Detalhes da Venda Selecionada", command=view_selected_sale_details).pack(pady=5)

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

    def format_cpf(self, entry_widget):
        text = entry_widget.get().replace(".", "").replace("-", "")
        formatted_text = ""
        for i, char in enumerate(text):
            if not char.isdigit():
                continue
            formatted_text += char
            if i == 2 or i == 5:
                formatted_text += "."
            elif i == 8:
                formatted_text += "-"
        
        if len(formatted_text) > 14:
            formatted_text = formatted_text[:14]

        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, formatted_text)
        entry_widget.icursor(tk.END) # Posiciona o cursor no final do texto

    def format_phone(self, entry_widget):
        text = entry_widget.get().replace("(", "").replace(")", "").replace(" ", "").replace("-", "")
        formatted_text = ""
        
        if len(text) > 11:
            text = text[:11]

        if len(text) > 0:
            formatted_text += "(" + text[0:2] + ")"
            if len(text) > 2:
                if len(text) > 7:
                    formatted_text += " " + text[2:7] + "-" + text[7:]
                else:
                    formatted_text += " " + text[2:6] + "-" + text[6:]
        
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, formatted_text)
        entry_widget.icursor(tk.END) # Posiciona o cursor no final do texto

    def format_date(self, entry_widget):
        text = entry_widget.get().replace("-", "")
        formatted_text = ""
        
        if len(text) > 8:
            text = text[:8]

        for i, char in enumerate(text):
            if not char.isdigit():
                continue
            formatted_text += char
            if i == 1 or i == 3: # DD-MM-AAAA
                formatted_text += "-"
        
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, formatted_text)
        entry_widget.icursor(tk.END) # Posiciona o cursor no final do texto