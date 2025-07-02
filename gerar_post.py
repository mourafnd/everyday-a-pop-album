# gerar_post.py - Gera um post diário com um álbum pop

from openai import OpenAI
from datetime import datetime
import os
import re
import unicodedata

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Função para gerar slug a partir de texto
def gerar_slug(texto):
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('utf-8')
    texto = re.sub(r'[^a-zA-Z0-9\s-]', '', texto)
    texto = texto.lower().replace(' ', '-').strip('-')
    return texto

# Chamada à API para gerar conteúdo
def gerar_conteudo():
    prompt = (
        "Sugira um álbum pop (brasileiro, latino ou internacional) para apresentar hoje. "
        "Inclua o nome do álbum, artista, ano, país, estilo musical, principais faixas, curiosidades se houver e qualquer outra informação sobre este album que você ache útil. "
        "Formate com títulos e tópicos. Escreva em inglês."
    )
    resposta = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000
    )
    return resposta.choices[0].message.content.strip()

# Salvar conteúdo como arquivo Markdown
def salvar_post(conteudo, hoje):
    titulo_match = re.search(r'^\*\*(.*?)\*\* by \*\*(.*?)\*\*', conteudo, re.MULTILINE)
    if titulo_match:
        album = titulo_match.group(1).strip()
        artista = titulo_match.group(2).strip()
    else:
        album = "Unknown Album"
        artista = "Unknown Artist"

    titulo = f"{album} - {artista}"
    slug = gerar_slug(f"{album} {artista}")
    descricao = f"Discover the album '{album}' by {artista}, a highlight in pop music."
    keywords = f"pop album, {artista}, {album}, music"

    caminho = f"content/posts/{slug}.md"
    
    keywords_formatadas = [f'"{k.strip()}"' for k in keywords.split(",")]
    
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(f"title: \"{titulo}\"\n")
        f.write(f"date: {hoje.isoformat()}\n")
        f.write(f"slug: \"{slug}\"\n")
        f.write(f"description: \"{descricao}\"\n")
        f.write(f'keywords: [{", ".join(keywords_formatadas)}]\n')
        f.write("---\n\n")
        f.write(conteudo)

# Executar geração
if __name__ == "__main__":
    hoje = datetime.now()
    conteudo = gerar_conteudo()
    salvar_post(conteudo, hoje)
    print("Post gerado com sucesso!")