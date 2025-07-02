# gerar_post.py - Gera um post diário multilíngue com um álbum pop

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

# Chamada à API para gerar conteúdo multilíngue
def gerar_conteudo():
    prompt = (
        "Recomende um álbum pop (brasileiro, latino ou internacional).\n"
        "Comece exatamente com o nome do álbum em negrito, seguido de 'by' e o artista também em negrito, neste formato:\n"
        "**Album Name** by **Artist Name**\n\n"
        "Depois, escreva os seguintes tópicos:\n"
        "- Year\n- Country\n- Genre\n- Main Tracks (5 to 8 songs)\n- One or two curiosities and any other information about this album that you might find useful.\n\n"
        "Agora escreva o mesmo conteúdo em três idiomas:\n"
        "## ENGLISH (first)\n## PORTUGUÊS (Brazilian Portuguese)\n## ESPAÑOL (Latin American Spanish)\n"
        "Mantenha a estrutura idêntica entre as versões."
    )
    resposta = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1500
    )
    return resposta.choices[0].message.content.strip()

# Extrai o título do álbum/artista da versão em inglês
def extrair_album_artista(texto):
    match = re.search(r'^\*\*(.*?)\*\* by \*\*(.*?)\*\*', texto, re.MULTILINE)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    print("⚠️ Formato inesperado do título no conteúdo inglês.")
    return None, None

# Divide o conteúdo por idioma
def separar_por_idioma(conteudo):
    partes = re.split(r'^##\s+', conteudo, flags=re.MULTILINE)
    blocos = {}
    for parte in partes:
        if parte.strip().startswith("ENGLISH"):
            blocos['en'] = parte.partition("\n")[2].strip()
        elif parte.strip().startswith("PORTUGUÊS"):
            blocos['pt'] = parte.partition("\n")[2].strip()
        elif parte.strip().startswith("ESPAÑOL"):
            blocos['es'] = parte.partition("\n")[2].strip()
    return blocos

# Salvar os arquivos index.en.md, index.pt.md, index.es.md
def salvar_multilingue(blocos, album, artista, hoje):
    titulo_base = f"{album} - {artista}"
    slug = gerar_slug(f"{album} {artista}")
    descricao_base = f"Discover the album '{album}' by {artista}, a highlight in pop music."
    keywords_base = f"pop album, {artista}, {album}, music"

    pasta = f"content/posts/{slug}"
    os.makedirs(pasta, exist_ok=True)

    idiomas = {
        'en': {
            'title': titulo_base,
            'description': descricao_base,
            'content': blocos.get('en', '')
        },
        'pt': {
            'title': f"{album} - {artista}",
            'description': f"Descubra o álbum '{album}' de {artista}, um destaque na música pop.",
            'content': blocos.get('pt', '')
        },
        'es': {
            'title': f"{album} - {artista}",
            'description': f"Descubre el álbum '{album}' de {artista}, un destacado de la música pop.",
            'content': blocos.get('es', '')
        },
    }

    for lang, dados in idiomas.items():
        caminho = f"{pasta}/index.{lang}.md"
        with open(caminho, "w", encoding="utf-8") as f:
            f.write("---\n")
            f.write(f'title: "{dados["title"]}"\n')
            f.write(f'date: {hoje.isoformat()}\n')
            f.write(f'slug: "{slug}"\n')
            f.write(f'description: "{dados["description"]}"\n')
            keywords_formatadas = ', '.join([f'"{k.strip()}"' for k in keywords_base.split(',')])
            f.write(f"keywords: [{keywords_formatadas}]\n")
            f.write("---\n\n")
            f.write(dados['content'])

# Execução principal
if __name__ == "__main__":
    hoje = datetime.now()
    print("📁 Diretório atual:", os.getcwd())
    conteudo = gerar_conteudo()
    blocos = separar_por_idioma(conteudo)

    print("🧾 Início do conteúdo em inglês:\n", blocos.get('en', '')[:200], "\n---")

    album, artista = extrair_album_artista(blocos.get('en', ''))
    if not album or not artista:
        print("❌ Não foi possível extrair álbum ou artista. Abortando post.")
    else:
        print(f"✅ Álbum: {album} | Artista: {artista}")
        salvar_multilingue(blocos, album, artista, hoje)
        print("✅ Post multilíngue gerado com sucesso!")
