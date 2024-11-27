import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridUpdateMode

# Função para exibir a tabela editável
def show_table(dict_data: pd.DataFrame) -> pd.DataFrame:
    """
    Exibe a tabela com a possibilidade de edição
    :param dict_data: Dados para exibir
    :return: Dados modificados após edição
    """
    # Definindo as configurações diretamente no AgGrid
    grid_response = AgGrid(
        dict_data,
        editable=True,  # Permite edição
        fit_columns_on_grid_load=True,  # Ajusta as colunas ao carregar
        height=250,  # Altura do grid
        width='100%',  # Largura do grid
        update_mode=GridUpdateMode.MODEL_CHANGED,  # Modo de atualização
        enable_enterprise_modules=True,  # Habilita módulos extras se necessário
        theme='streamlit',  # Configura o tema
        allow_unsafe_jscode=True,  # Habilita execução de código JS inseguro (se necessário)
    )
    
    # Retorna os dados modificados pelo usuário
    return grid_response['data']

st.set_page_config(
    page_title="Automatic DVC",
    layout="wide"
)
st.title(
    "Installation Analysis Subsea"
)

# Exemplo de dados
data1 = pd.DataFrame({
    'Curvature [1/m]': [1.2, 2.3, 3.4],
    'Bend Moment [N.m]': [150, 250, 350]
})

# Exibe a tabela interativa
grid_response1 = show_table(data1)

tab0 = st.tabs["teste"]

with tab0:
    # Exibe os dados modificados
    st.write("Dados após a edição:")
    st.write(grid_response1)

    # Exemplo de botão para salvar os dados editados
    if st.button("Save Data"):
        # Aqui você pode salvar os dados em um arquivo ou banco de dados
        # Exemplo: grid_response1.to_csv("dados_editados.csv")
        st.write("Dados salvos com sucesso!")