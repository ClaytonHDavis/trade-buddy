import nbformat as nbf

# Read the Python script
with open('transform_coinbase_candles.py', 'r') as f:
    script = f.read()

# Create a new notebook
nb = nbf.v4.new_notebook()

# Add the script as a code cell
nb.cells.append(nbf.v4.new_code_cell(script))

# Save the notebook
with open('transform_coinbase_candles.ipynb', 'w') as f:
    nbf.write(nb, f)