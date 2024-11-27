import os

app_path = os.path.join(os.path.dirname(__file__), "1-interface\\interface.py")
comando = (f'python -m streamlit run "{app_path}" --theme.base "dark" '
           f'--theme.primaryColor "#e694ff"')
os.system(comando)
