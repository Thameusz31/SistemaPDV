import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from database import DATABASE_NAME
import uuid # Para gerar SKUs únicos mais facilmente

class ProdutosGUI(ttk.Frame):
    def __init__(self, master): # 'master' é o frame pai que vem do MainApp
        super().__init__(master, padding="15") # Adiciona padding ao frame deste módulo
        self.master = master # Mantém a referência ao frame pai se precisar

        self.conn = self.get_db_connection()

        # Agora, os LabelFrames e outros widgets são pack/grid DIRETAMENTE NESTE self
        self.frame_form = ttk.LabelFrame(self, text="Cadastro/Edição de Produto", padding="15")
        self.frame_form.pack(pady=10, padx=10, fill="x")
        self.frame_form.columnconfigure(1, weight=1)

        self.create_form_widgets(self.frame_form)

        self.frame_list = ttk.LabelFrame(self, text="Produtos Cadastrados", padding="15")
        self.frame_list.pack(pady=10, padx=10, fill="both", expand=True)
        self.create_list_widgets(self.frame_list)
        
        self.load_products()

    def get_db_connection(self):
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row
        return conn

    def create_form_widgets(self, parent_frame):
        field_configs = [
            ("Nome:", "nome"),
            ("Marca:", "marca"),
            ("Tamanho:", "tamanho"),
            ("Cor:", "cor"),
            ("Preço Custo:", "preco_custo"),
            ("Preço Venda:", "preco_venda"),
            ("Quantidade:", "quantidade"),
            ("Estoque Mínimo:", "estoque_minimo"),
            ("SKU:", "sku")
        ]
        
        self.entries = {}
        for i, (label_text, key_name) in enumerate(field_configs):
            ttk.Label(parent_frame, text=label_text).grid(row=i, column=0, sticky="w", pady=4, padx=5)
            entry = ttk.Entry(parent_frame, width=40)
            entry.grid(row=i, column=1, sticky="ew", pady=4, padx=5)
            self.entries[key_name] = entry
        
        button_frame = ttk.Frame(parent_frame)
        button_frame.grid(row=len(field_configs), column=0, columnspan=2, pady=15)
        
        ttk.Button(button_frame, text="Salvar Produto", command=self.add_product, style='Accent.TButton').pack(side="left", padx=10)
        ttk.Button(button_frame, text="Limpar Campos", command=self.clear_form).pack(side="left", padx=10)
        
        self.product_id_to_edit = None

    def create_list_widgets(self, parent_frame):
        columns = ("ID", "SKU", "Nome", "Marca", "Tamanho", "Cor", "Preço Venda", "Quantidade", "Estoque Mínimo")
        self.tree = ttk.Treeview(parent_frame, columns=columns, show="headings", selectmode="browse")

        for col in columns:
            self.tree.heading(col, text=col)
            if col == "ID":
                self.tree.column(col, width=40, anchor="center")
            elif col == "SKU":
                self.tree.column(col, width=80, anchor="center")
            elif col == "Nome":
                self.tree.column(col, width=150, anchor="w")
            elif col == "Marca":
                self.tree.column(col, width=80, anchor="w")
            elif col == "Tamanho":
                self.tree.column(col, width=60, anchor="center")
            elif col == "Cor":
                self.tree.column(col, width=70, anchor="w")
            elif col == "Preço Venda":
                self.tree.column(col, width=90, anchor="e")
            elif col == "Quantidade":
                self.tree.column(col, width=70, anchor="center")
            elif col == "Estoque Mínimo":
                self.tree.column(col, width=90, anchor="center")
            else:
                self.tree.column(col, width=100, anchor="center")

        self.tree.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        button_frame_list = ttk.Frame(parent_frame)
        button_frame_list.pack(pady=10)
        ttk.Button(button_frame_list, text="Editar Selecionado", command=self.edit_selected_product).pack(side="left", padx=5)
        ttk.Button(button_frame_list, text="Remover Selecionado", command=self.delete_selected_product, style='Danger.TButton').pack(side="left", padx=5)
        
    def load_products(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, sku, nome, marca, tamanho, cor, preco_venda, quantidade, estoque_minimo FROM produtos")
        products = cursor.fetchall()
        conn.close()

        for p in products:
            self.tree.insert("", "end", values=(p['id'], p['sku'], p['nome'], p['marca'], p['tamanho'], p['cor'], f"{p['preco_venda']:.2f}", p['quantidade'], p['estoque_minimo']))

    def add_product(self):
        nome = self.entries["nome"].get()
        marca = self.entries["marca"].get()
        tamanho = self.entries["tamanho"].get()
        cor = self.entries["cor"].get()
        preco_custo = self.entries["preco_custo"].get()
        preco_venda = self.entries["preco_venda"].get()
        quantidade = self.entries["quantidade"].get()
        estoque_minimo = self.entries["estoque_minimo"].get()
        sku = self.entries["sku"].get()

        if not nome or not preco_custo or not preco_venda or not quantidade or not estoque_minimo:
            messagebox.showerror("Erro de Validação", "Nome, Preço de Custo, Preço de Venda, Quantidade e Estoque Mínimo são obrigatórios.")
            return

        try:
            preco_custo = float(preco_custo)
            preco_venda = float(preco_venda)
            quantidade = int(quantidade)
            estoque_minimo = int(estoque_minimo)
        except ValueError:
            messagebox.showerror("Erro de Validação", "Preços, Quantidade e Estoque Mínimo devem ser números válidos.")
            return

        if not sku:
            sku = str(uuid.uuid4())[:8].upper()

        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            if self.product_id_to_edit:
                cursor.execute("""
                    UPDATE produtos SET
                    nome = ?, marca = ?, tamanho = ?, cor = ?, preco_custo = ?, preco_venda = ?, quantidade = ?, sku = ?, estoque_minimo = ?
                    WHERE id = ?
                """, (nome, marca, tamanho, cor, preco_custo, preco_venda, quantidade, sku, estoque_minimo, self.product_id_to_edit))
                messagebox.showinfo("Sucesso", "Produto atualizado com sucesso!")
            else:
                cursor.execute("INSERT INTO produtos (nome, marca, tamanho, cor, preco_custo, preco_venda, quantidade, sku, estoque_minimo) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                               (nome, marca, tamanho, cor, preco_custo, preco_venda, quantidade, sku, estoque_minimo))
                messagebox.showinfo("Sucesso", f"Produto '{nome}' cadastrado com sucesso! SKU: {sku}")
            
            conn.commit()
            self.load_products()
            self.clear_form()

        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", f"Erro: O SKU '{sku}' já existe. Por favor, insira um SKU diferente.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar produto: {e}")
        finally:
            conn.close()

    def clear_form(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.entries["estoque_minimo"].insert(0, "0")
        # CORREÇÃO AQUI: Usando winfo_toplevel() para acessar a janela principal
        self.winfo_toplevel().title("Sistema Loja Streetwear - Gestão Integrada") 
        self.frame_form.config(text="Cadastro/Edição de Produto")
        
    def edit_selected_product(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Aviso", "Nenhum produto selecionado para edição.")
            return

        values = self.tree.item(selected_item, 'values')
        product_id = values[0]

        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM produtos WHERE id = ?", (product_id,))
        product_data = cursor.fetchone()
        conn.close()

        if product_data:
            self.clear_form()
            self.entries["nome"].insert(0, product_data['nome'])
            self.entries["marca"].insert(0, product_data['marca'])
            self.entries["tamanho"].insert(0, product_data['tamanho'])
            self.entries["cor"].insert(0, product_data['cor'])
            self.entries["preco_custo"].insert(0, str(product_data['preco_custo']))
            self.entries["preco_venda"].insert(0, str(product_data['preco_venda']))
            self.entries["quantidade"].insert(0, str(product_data['quantidade']))
            self.entries["estoque_minimo"].insert(0, str(product_data['estoque_minimo']))
            self.entries["sku"].insert(0, product_data['sku'])
            
            self.product_id_to_edit = product_id
            # CORREÇÃO AQUI: Usando winfo_toplevel() para acessar a janela principal
            self.winfo_toplevel().title(f"Sistema Loja Streetwear - Editando: {product_data['nome']}") 
            self.frame_form.config(text=f"Editando Produto: {product_data['nome']}")

    def delete_selected_product(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Aviso", "Nenhum produto selecionado para remoção.")
            return

        product_id = self.tree.item(selected_item, 'values')[0]
        product_name = self.tree.item(selected_item, 'values')[2]

        if messagebox.askyesno("Confirmar Remoção", f"Tem certeza que deseja remover o produto '{product_name}'?"):
            conn = self.get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM produtos WHERE id = ?", (product_id,))
                conn.commit()
                messagebox.showinfo("Sucesso", "Produto removido com sucesso!")
                self.load_products()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao remover produto: {e}")
            finally:
                conn.close()