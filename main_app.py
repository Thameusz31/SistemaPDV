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
from caixa_gui import CaixaGUI

class MainApp:
    def __init__(self, master):
        self.master = master
        master.title("Sistema Loja Streetwear - Gestão Integrada")
        master.geometry("1200x800")
        try:
            master.state('zoomed') # Inicia maximizado em Windows/Linux
        except:
            master.attributes('-fullscreen', True) # Para tela cheia completa no macOS/outros

        # --- Aplica um tema moderno e configura estilos globais ---
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except tk.TclError:
            print("Tema 'clam' não disponível, usando tema padrão.")

        # Configurações de estilo para fontes e paddings
        self.style.configure('TButton', font=('Arial', 10), padding=8)
        self.style.configure('TEntry', padding=5)
        
        # --- CORREÇÃO AQUI: Força o background do TFrame e TLabelframe para branco ---
        self.style.configure('TFrame', background='white') # Define background para todos os ttk.Frame
        
        # Configurações para TLabelframe (incluindo o fundo do label do título)
        self.style.configure('TLabelframe', background='white', borderwidth=2, relief='flat') # Mudado para 'flat' para menos sombra
        self.style.configure('TLabelframe.Label', font=('Arial', 12, 'bold'), foreground='#333333', background='white') # Força background branco para o texto do LabelFrame

        # --- CORREÇÃO AQUI: Configura o background do TLabel e TRadiobutton ---
        # Removido background='white' dos Labels individuais nos GUIs
        self.style.configure('TLabel', font=('Arial', 10), background='white') # Força background branco para todos os ttk.Label
        self.style.configure('TRadiobutton', background='white', foreground='#333333') # Força background branco para Radiobuttons
        self.style.configure('TCheckbutton', background='white', foreground='#333333') # Para caso de Checkbuttons no futuro

        # Estilos para botões de destaque e perigo
        self.style.configure('Accent.TButton', background='#4CAF50', foreground='white')
        self.style.map('Accent.TButton',
                       background=[('active', '#66BB6A'), ('!disabled', '#4CAF50')],
                       foreground=[('active', 'white'), ('!disabled', 'white')])
        self.style.configure('Danger.TButton', background='#F44336', foreground='white')
        self.style.map('Danger.TButton',
                       background=[('active', '#E57370'), ('!disabled', '#F44336')], # Ajuste sutil na cor ativa
                       foreground=[('active', 'white'), ('!disabled', 'white')])
        # Estilos para cores de status em Treeview
        self.style.configure('Overdue.Treeview.Row', background='#FFCDD2', foreground='#D32F2F')
        self.style.configure('Pending.Treeview.Row', background='#FFF9C4', foreground='#F57F17')
        self.style.configure('Paid.Treeview.Row', background='#C8E6C9', foreground='#2E7D32')


        create_tables()

        # --- Layout Principal: Menu Lateral e Área de Conteúdo ---
        self.menu_frame = ttk.Frame(master, width=220, relief="raised", padding="10 0 10 0")
        self.menu_frame.pack(side="left", fill="y")
        self.menu_frame.pack_propagate(False)

        ttk.Label(self.menu_frame, text="MENU", font=("Arial", 18, "bold"), anchor="center", foreground="#333333").pack(pady=15, fill="x")

        # Mapeamento de teclas de função para módulos e seus nomes de frame
        self.module_map = {
            "F1": {"text": "Gerenciar Produtos", "frame_name": "produtos"},
            "F2": {"text": "Gerenciar Vendedores", "frame_name": "vendedores"},
            "F3": {"text": "Gerenciar Clientes", "frame_name": "clientes"},
            "F4": {"text": "Gestão de Estoque", "frame_name": "estoque"},
            "F5": {"text": "Abrir PDV e Histórico", "frame_name": "pdv"},
            "F6": {"text": "Ver Vendas A Prazo", "frame_name": "aprazo"},
            "F7": {"text": "Controle de Caixa", "frame_name": "caixa"},
            "F8": {"text": "Ver Relatórios", "frame_name": "relatorios"}
        }

        for key, item_info in self.module_map.items():
            btn = ttk.Button(self.menu_frame, text=f"{item_info['text']} ({key})", 
                             command=lambda name=item_info['frame_name']: self.show_frame(name), 
                             width=25)
            btn.pack(pady=6, padx=5)
            self.master.bind(f"<{key}>", lambda event, name=item_info['frame_name']: self.show_frame(name))

        ttk.Button(self.menu_frame, text="Sair", command=master.quit, width=25).pack(pady=15, padx=5)

        self.content_frame = ttk.Frame(master)
        self.content_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.frames = {}
        for F in (ProdutosGUI, VendedoresGUI, ClientesGUI, EstoqueGUI, PDVGUI, APrazoGUI, CaixaGUI, RelatoriosGUI):
            page_name = F.__name__.replace('GUI', '').lower()
            frame_instance = F(self.content_frame)
            self.frames[page_name] = frame_instance
            frame_instance.grid(row=0, column=0, sticky="nsew")

        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        self.show_frame("pdv")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        self.master.title(f"Sistema Loja Streetwear - {page_name.capitalize()}")

        try:
            if page_name == "pdv":
                self.frames["pdv"]._load_vendedores_clientes_for_dropdowns()
                self.frames["pdv"].load_vendas_historico()
                self.frames["pdv"].sku_entry.focus_set()
            elif page_name == "estoque":
                self.frames["estoque"]._load_vendedores_for_dropdown()
                self.frames["estoque"].load_produtos_for_dropdown()
                self.frames["estoque"].load_estoque_atual()
                self.frames["estoque"].load_historico_movimentacoes()
            elif page_name == "aprazo":
                self.frames["aprazo"]._load_clientes_for_filter()
                self.frames["aprazo"].load_parcelas()
            elif page_name == "caixa":
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
        except Exception as e:
            print(f"Erro ao recarregar dados para {page_name}: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()