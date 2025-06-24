import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from database import DATABASE_NAME

# A CLASSE AGORA HERDA DE ttk.Frame
class VendedoresGUI(ttk.Frame):
    def __init__(self, master): # 'master' é o frame pai que vem do MainApp
        # CHAMA O CONSTRUTOR DA CLASSE PAI (ttk.Frame)
        super().__init__(master, padding="15") # <--- ALTERAÇÃO AQUI
        self.master = master # Mantém a referência ao frame pai se precisar

        # REMOVER: master.title(...), master.geometry(...), etc.

        self.conn = self.get_db_connection()

        # Agora, os LabelFrames e outros widgets são pack/grid DIRETAMENTE NESTE self
        self.frame_form = ttk.LabelFrame(self, text="Cadastro/Edição de Vendedor", padding="15")
        self.frame_form.pack(pady=10, padx=10, fill="x")
        self.frame_form.columnconfigure(1, weight=1)

        self.create_form_widgets(self.frame_form)

        self.frame_list = ttk.LabelFrame(self, text="Vendedores Cadastrados", padding="15")
        self.frame_list.pack(pady=10, padx=10, fill="both", expand=True)
        self.create_list_widgets(self.frame_list)
        
        self.load_vendedores()

    def get_db_connection(self):
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row
        return conn

    def create_form_widgets(self, parent_frame):
        labels = ["Nome:", "CPF:", "Telefone:"]
        self.entries = {}
        for i, label_text in enumerate(labels):
            ttk.Label(parent_frame, text=label_text).grid(row=i, column=0, sticky="w", pady=4, padx=5)
            entry = ttk.Entry(parent_frame, width=40)
            entry.grid(row=i, column=1, sticky="ew", pady=4, padx=5)
            self.entries[label_text.replace(":", "").lower()] = entry
        
        # --- Configuração das máscaras ---
        self.entries["cpf"].bind("<KeyRelease>", lambda event: self.format_cpf(self.entries["cpf"]))
        self.entries["telefone"].bind("<KeyRelease>", lambda event: self.format_phone(self.entries["telefone"]))

        button_frame = ttk.Frame(parent_frame)
        button_frame.grid(row=len(labels), column=0, columnspan=2, pady=15)
        
        ttk.Button(button_frame, text="Salvar Vendedor", command=self.add_vendedor, style='Accent.TButton').pack(side="left", padx=10)
        ttk.Button(button_frame, text="Limpar Campos", command=self.clear_form).pack(side="left", padx=10)
        
        self.vendedor_id_to_edit = None

    def create_list_widgets(self, parent_frame):
        columns = ("ID", "Nome", "CPF", "Telefone")
        self.tree = ttk.Treeview(parent_frame, columns=columns, show="headings", selectmode="browse")

        for col in columns:
            self.tree.heading(col, text=col)
            if col == "ID":
                self.tree.column(col, width=50, anchor="center")
            elif col == "Nome":
                self.tree.column(col, width=200, anchor="w")
            else:
                self.tree.column(col, width=150, anchor="center")
        
        self.tree.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        button_frame_list = ttk.Frame(parent_frame)
        button_frame_list.pack(pady=10)
        ttk.Button(button_frame_list, text="Editar Selecionado", command=self.edit_selected_vendedor).pack(side="left", padx=5)
        ttk.Button(button_frame_list, text="Remover Selecionado", command=self.delete_selected_vendedor, style='Danger.TButton').pack(side="left", padx=5)

    def load_vendedores(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, cpf, telefone FROM vendedores")
        vendedores = cursor.fetchall()
        conn.close()

        for v in vendedores:
            self.tree.insert("", "end", values=(v['id'], v['nome'], v['cpf'], v['telefone']))

    def add_vendedor(self):
        nome = self.entries["nome"].get().strip()
        cpf = self.entries["cpf"].get().strip()
        telefone = self.entries["telefone"].get().strip()

        if not nome:
            messagebox.showerror("Erro de Validação", "Nome do vendedor é obrigatório.")
            return
        
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            if self.vendedor_id_to_edit:
                cursor.execute("""
                    UPDATE vendedores SET
                    nome = ?, cpf = ?, telefone = ?
                    WHERE id = ?
                """, (nome, cpf, telefone, self.vendedor_id_to_edit))
                messagebox.showinfo("Sucesso", "Vendedor atualizado com sucesso!")
            else:
                cursor.execute("INSERT INTO vendedores (nome, cpf, telefone) VALUES (?, ?, ?)",
                               (nome, cpf, telefone))
                messagebox.showinfo("Sucesso", f"Vendedor '{nome}' cadastrado com sucesso!")
            
            conn.commit()
            self.load_vendedores()
            self.clear_form()

        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: vendedores.nome" in str(e):
                messagebox.showerror("Erro", f"Erro: Já existe um vendedor com o nome '{nome}'.")
            elif "UNIQUE constraint failed: vendedores.cpf" in str(e):
                messagebox.showerror("Erro", f"Erro: Já existe um vendedor com o CPF '{cpf}'.")
            else:
                messagebox.showerror("Erro", f"Erro ao salvar vendedor: {e}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar vendedor: {e}")
        finally:
            conn.close()

    def clear_form(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.vendedor_id_to_edit = None
        # Mudei de master.title para self.master.master.title pois self é o frame, master é o content_frame e master.master é a janela principal
        self.master.master.title("Gerenciamento de Vendedores - Loja Streetwear")
        self.frame_form.config(text="Cadastro/Edição de Vendedor")
        
    def edit_selected_vendedor(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Aviso", "Nenhum vendedor selecionado para edição.")
            return

        values = self.tree.item(selected_item, 'values')
        vendedor_id = values[0]

        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vendedores WHERE id = ?", (vendedor_id,))
        vendedor_data = cursor.fetchone()
        conn.close()

        if vendedor_data:
            self.clear_form()
            self.entries["nome"].insert(0, vendedor_data['nome'])
            self.entries["cpf"].insert(0, vendedor_data['cpf'] if vendedor_data['cpf'] else "")
            self.entries["telefone"].insert(0, vendedor_data['telefone'] if vendedor_data['telefone'] else "")
            
            self.vendedor_id_to_edit = vendedor_id
            self.master.master.title(f"Editando Vendedor: {vendedor_data['nome']}")
            self.frame_form.config(text=f"Editando Vendedor: {vendedor_data['nome']}")

    def delete_selected_vendedor(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Aviso", "Nenhum vendedor selecionado para remoção.")
            return

        vendedor_id = self.tree.item(selected_item, 'values')[0]
        vendedor_nome = self.tree.item(selected_item, 'values')[1]

        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM vendas WHERE vendedor_id = ?", (vendedor_id,))
        num_vendas = cursor.fetchone()[0]
        conn.close()

        if num_vendas > 0:
            messagebox.showerror("Erro", f"Não é possível remover o vendedor '{vendedor_nome}' pois ele está associado a {num_vendas} venda(s).")
            return

        if messagebox.askyesno("Confirmar Remoção", f"Tem certeza que deseja remover o vendedor '{vendedor_nome}'?"):
            conn = self.get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM vendedores WHERE id = ?", (vendedor_id,))
                conn.commit()
                messagebox.showinfo("Sucesso", "Vendedor removido com sucesso!")
                self.load_vendedores()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao remover vendedor: {e}")
            finally:
                conn.close()

    # --- Funções de formatação ---
    def format_cpf(self, entry_widget):
        text = entry_widget.get().replace('.', '').replace('-', '')
        new_text = ""
        for i, char in enumerate(text):
            if not char.isdigit():
                continue
            if i == 3 or i == 6:
                new_text += "."
            elif i == 9:
                new_text += "-"
            new_text += char
            if len(new_text) >= 14:
                break
        
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, new_text)

    def format_phone(self, entry_widget):
        text = entry_widget.get().replace('(', '').replace(')', '').replace(' ', '').replace('-', '')
        new_text = ""
        if len(text) > 0:
            new_text += "("
            if len(text) > 2:
                new_text += text[0:2] + ") "
                if len(text) > 7:
                    new_text += text[2:7] + "-" + text[7:]
                else:
                    new_text += text[2:]
            else:
                new_text += text
        
        if len(new_text) > 15:
            new_text = new_text[:15]

        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, new_text)