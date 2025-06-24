import sqlite3

DATABASE_NAME = 'loja_streetwear.db'

def create_tables():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Tabela de Produtos (CORREÇÃO: Garantindo que SKU e estoque_minimo existam)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            marca TEXT,
            tamanho TEXT,
            cor TEXT,
            preco_custo REAL NOT NULL,
            preco_venda REAL NOT NULL,
            quantidade INTEGER NOT NULL,
            sku TEXT UNIQUE, -- COLUNA 'SKU' CORRIGIDA/ADICIONADA
            estoque_minimo INTEGER DEFAULT 0 -- COLUNA 'ESTOQUE_MINIMO' CORRIGIDA/ADICIONADA
        )
    ''')

    # Tabela de Vendedores (SEM ALTERAÇÃO)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            cpf TEXT UNIQUE,
            telefone TEXT
        )
    ''')

    # Tabela de Clientes (CORREÇÃO FINALMENTE VERIFICADA)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE,
            telefone TEXT,
            email TEXT UNIQUE,
            data_nascimento TEXT,
            pontos INTEGER DEFAULT 0,
            endereco TEXT
        )
    ''')

    # Tabela de Vendas (SEM ALTERAÇÃO)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT NOT NULL,
            total_venda REAL NOT NULL, -- Total BRUTO
            desconto_aplicado REAL NOT NULL DEFAULT 0.0,
            juros_aplicados REAL NOT NULL DEFAULT 0.0,
            total_final REAL NOT NULL, -- Total Líquido (com desconto e juros)
            forma_pagamento TEXT NOT NULL,
            tipo_cartao TEXT,
            parcelas_total INTEGER DEFAULT 1,
            parcelas_pagas INTEGER DEFAULT 0,
            vendedor_id INTEGER,
            cliente_id INTEGER,
            FOREIGN KEY (vendedor_id) REFERENCES vendedores(id),
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    ''')

    # Tabela de Itens da Venda (SEM ALTERAÇÃO)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens_venda (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id INTEGER NOT NULL,
            produto_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            FOREIGN KEY (venda_id) REFERENCES vendas(id),
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
    ''')
    
    # Tabela de Movimentações de Estoque (SEM ALTERAÇÃO)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes_estoque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            tipo_movimentacao TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            data_hora TEXT NOT NULL,
            motivo TEXT,
            custo_unitario_movimentacao REAL,
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
    ''')

    # Tabela de Movimentações de Pontos (SEM ALTERAÇÃO)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes_pontos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            data_hora TEXT NOT NULL,
            tipo_movimentacao TEXT NOT NULL,
            pontos INTEGER NOT NULL,
            referencia_id INTEGER,
            motivo TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    ''')

    # Tabela de Parcelas (SEM ALTERAÇÃO)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parcelas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id INTEGER NOT NULL,
            numero_parcela INTEGER NOT NULL,
            valor_parcela REAL NOT NULL,
            data_vencimento TEXT NOT NULL,
            data_pagamento TEXT,
            status TEXT NOT NULL DEFAULT 'Pendente',
            FOREIGN KEY (venda_id) REFERENCES vendas(id),
            UNIQUE (venda_id, numero_parcela)
        )
    ''')

    # Tabela de Movimentações de Caixa (CORREÇÃO FINALMENTE CONFIRMADA)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes_caixa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT NOT NULL,
            tipo_movimentacao TEXT NOT NULL,
            valor REAL NOT NULL,
            forma_pagamento TEXT,
            descricao TEXT,
            referencia_id INTEGER,
            tabela_referencia TEXT,
            responsavel_id INTEGER,
            FOREIGN KEY (responsavel_id) REFERENCES vendedores(id)
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_tables()