

import os

for var_env in os.environ:
    print(f"{var_env}: {os.environ.get(var_env)}")
"""
Traceback (most recent call last):
  
  
2024-11-27 23:25:36.807 Uncaught app exception
Traceback (most recent call last):

File "C:\Users\dwanderley\Digicorner\Installation Analysis Subsea - Daniel Wanderley\tcc\venv_tcc\lib\site-packages\streamlit\runtime\scriptrunner\exec_code.py", line 88, in exec_func_with_error_handling
    result = func()

File "C:\Users\dwanderley\Digicorner\Installation Analysis Subsea - Daniel Wanderley\tcc\venv_tcc\lib\site-packages\streamlit\runtime\scriptrunner\script_runner.py", line 579, in code_to_exec
    exec(code, module.__dict__)

File "C:\Users\dwanderley\Digicorner\Installation Analysis Subsea - Daniel Wanderley\tcc\project\1-interface\Interface.py", line 7, in <module>
    from st_aggrid.grid_options_builder import GridOptionsBuilder

File "C:\Users\dwanderley\Digicorner\Installation Analysis Subsea - Daniel Wanderley\tcc\venv_tcc\lib\site-packages\st_aggrid\__init__.py", line 81, in <module>
    _RELEASE = config("AGGRID_RELEASE", default=True, cast=bool)

File "C:\Users\dwanderley\Digicorner\Installation Analysis Subsea - Daniel Wanderley\tcc\venv_tcc\lib\site-packages\decouple.py", line 246, in __call__
    self._load(self.search_path or self._caller_path())

File "C:\Users\dwanderley\Digicorner\Installation Analysis Subsea - Daniel Wanderley\tcc\venv_tcc\lib\site-packages\decouple.py", line 236, in _load
    self.config = Config(Repository(filename, encoding=self.encoding))

File "C:\Users\dwanderley\Digicorner\Installation Analysis Subsea - Daniel Wanderley\tcc\venv_tcc\lib\site-packages\decouple.py", line 130, in __init__
    read_config(self.parser, file_)

File "C:\Users\dwanderley\Digicorner\Installation Analysis Subsea - Daniel Wanderley\tcc\venv_tcc\lib\site-packages\decouple.py", line 21, in <lambda>
    read_config = lambda parser, file: parser.read_file(file)

File "C:\Users\dwanderley\AppData\Local\Programs\Python\Python310\lib\configparser.py", line 720, in read_file
    self._read(f, source)

File "C:\Users\dwanderley\AppData\Local\Programs\Python\Python310\lib\configparser.py", line 1022, in _read
    for lineno, line in enumerate(fp, start=1):
    
File "C:\Users\dwanderley\AppData\Local\Programs\Python\Python310\lib\codecs.py", line 322, in decode
    (result, consumed) = self._buffer_decode(data, self.errors, final)

UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte
"""
