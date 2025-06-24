import tkinter as tk
from tkinter import ttk, messagebox
from database import create_tables

# Importa todas as GUIs. Elas serão instanciadas como Frames
from produtos_gui import ProdutosGUI
from pdv_gui import PDVGUI
from vendedores_gui import VendedoresGUI
from clientes_gui import ClientesGUI
from relatorios_gui import RelatoriosGUI
from estoque_gui import EstoqueGUI
from aprazo_gui import APrazoGUI
from caixa_gui import CaixaGUI # NOVO

class MainApp:
    def __init__(self, master):
        self.master = master
        master.title("Sistema Loja Streetwear - Gestão Integrada")
        master.geometry("1200x800")
        try:
            master.state('zoomed')
        except:
            master.attributes('-fullscreen', True)

        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except tk.TclError:
            print("Tema 'clam' não disponível, usando tema padrão.")

        self.style.configure('TButton', font=('Arial', 10), padding=8)
        self.style.configure('TLabel', font=('Arial', 10))
        self.style.configure('TEntry', padding=5)
        self.style.configure('TLabelframe.Label', font=('Arial', 12, 'bold'))
        self.style.configure('Accent.TButton', background='#4CAF50', foreground='white')
        self.style.map('Accent.TButton',
                       background=[('active', '#66BB6A'), ('!disabled', '#4CAF50')],
                       foreground=[('active', 'white'), ('!disabled', 'white')])
        self.style.configure('Danger.TButton', background='#F44336', foreground='white')
        self.style.map('Danger.TButton',
                       background=[('active', '#E57373'), ('!disabled', '#F44336')],
                       foreground=[('active', 'white'), ('!disabled', 'white')])
        self.style.configure('Overdue.Treeview.Row', background='#FFCDD2', foreground='#D32F2F')
        self.style.configure('Pending.Treeview.Row', background='#FFF9C4', foreground='#F57F17')
        self.style.configure('Paid.Treeview.Row', background='#C8E6C9', foreground='#2E7D32')


        create_tables()

        # --- Layout Principal: Menu Lateral e Área de Conteúdo ---
        self.menu_frame = ttk.Frame(master, width=220, relief="raised", padding="10 0 10 0")
        self.menu_frame.pack(side="left", fill="y")
        self.menu_frame.pack_propagate(False)

        ttk.Label(self.menu_frame, text="MENU", font=("Arial", 18, "bold"), anchor="center").pack(pady=15, fill="x")

        # Itens do Menu (Botões)
        menu_items = [
            {"text": "Gerenciar Produtos", "command": lambda: self.show_frame("produtos")},
            {"text": "Gerenciar Vendedores", "command": lambda: self.show_frame("vendedores")},
            {"text": "Gerenciar Clientes", "command": lambda: self.show_frame("clientes")},
            {"text": "Gestão de Estoque", "command": lambda: self.show_frame("estoque")},
            {"text": "Abrir PDV e Histórico", "command": lambda: self.show_frame("pdv")},
            {"text": "Ver Vendas A Prazo", "command": lambda: self.show_frame("aprazo")},
            {"text": "Controle de Caixa", "command": lambda: self.show_frame("caixa")}, # NOVO BOTÃO
            {"text": "Ver Relatórios", "command": lambda: self.show_frame("relatorios")},
            {"text": "Sair", "command": master.quit}
        ]

        for item in menu_items:
            ttk.Button(self.menu_frame, text=item["text"], command=item["command"], width=25).pack(pady=8, padx=5)

        # --- Frame Principal para Conteúdo (onde as GUIs serão exibidas) ---
        self.content_frame = ttk.Frame(master)
        self.content_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # --- Criação das instâncias de cada GUI como Frames internos ---
        self.frames = {}
        for F in (ProdutosGUI, VendedoresGUI, ClientesGUI, EstoqueGUI, PDVGUI, APrazoGUI, CaixaGUI, RelatoriosGUI): # Adicionado CaixaGUI
            page_name = F.__name__.replace('GUI', '').lower()
            frame = F(self.content_frame)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Configura o grid do content_frame para que o frame ativo ocupe todo o espaço
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # Mostra o frame inicial (PDV geralmente é o mais usado)
        self.show_frame("pdv")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

        # Recarrega dados específicos quando um módulo é ativado
        if page_name == "pdv":
            self.frames["pdv"]._load_vendedores_clientes_for_dropdowns()
            self.frames["pdv"].load_vendas_historico()
            self.frames["pdv"].sku_entry.focus_set()
        elif page_name == "estoque":
            self.frames["estoque"].load_produtos_for_dropdown()
            self.frames["estoque"].load_estoque_atual()
            self.frames["estoque"].load_historico_movimentacoes()
        elif page_name == "aprazo":
            self.frames["aprazo"]._load_clientes_for_filter()
            self.frames["aprazo"].load_parcelas()
        elif page_name == "caixa": # NOVO: Recarrega o caixa
            self.frames["caixa"]._load_vendedores_for_dropdown()
            self.frames["caixa"].load_movimentacoes_caixa()
        elif page_name == "relatorios":
            self.frames["relatorios"]._load_vendedores_clientes_for_filters()
            self.frames["relatorios"].load_relatorio_vendas()
        elif page_name == "clientes":
            self.frames["clientes"].load_clientes()
        elif page_name == "vendedores":
            self.frames["vendedores"].load_vendedores()
        elif page_name == "produtos":
            self.frames["produtos"].load_products()


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()