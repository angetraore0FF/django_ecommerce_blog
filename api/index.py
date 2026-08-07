from ecommerce.wsgi import application  # pyright: ignore[reportMissingImports]

# Vercel exige que la variable exportée s'appelle 'app'
app = application