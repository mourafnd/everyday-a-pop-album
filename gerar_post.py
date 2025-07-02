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
        "Sua tarefa é recomendar um álbum EXCLUSIVAMENTE do gênero POP (pop brasileiro, pop latino ou pop internacional).\n"
        "⚠️ Não inclua álbuns de outros gêneros como rap, rock, metal, samba, funk, jazz, etc.\n"
        "⚠️ Recomende apenas álbuns com sonoridade pop clara, seja mainstream ou alternativo.\n"
        "⚠️ NÃO recomende 'Future Nostalgia' de 'Dua Lipa'.\n\n"
        "Comece exatamente com esta linha (substituindo os colchetes pelo conteúdo real):\n"
        "**[Nome do Álbum]** by **[Nome do Artista]**\n\n"
        "Em seguida, escreva os tópicos abaixo:\n"
        "- Year\n- Country\n- Genre\n- Main Tracks (5 to 8 songs)\n"
        "- Curiosities and any other relevant information about this album\n\n"
        "Depois, traduza esse mesmo conteúdo para os idiomas abaixo, com o mesmo formato e tópicos:\n"
        "## ENGLISH\n## PORTUGUÊS\n## ESPAÑOL\n\n"
        "⚠️ IMPORTANTE: O título com o nome do álbum e artista deve aparecer apenas na versão em inglês, no topo, sempre no formato:\n"
        "**Album Name** by **Artist Name**\n"
        "Mantenha a estrutura exata e não adicione explicações extras. Escolha sempre um álbum real diferente."
    )

    resposta = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
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

    for tentativa in range(3):
        conteudo = gerar_conteudo()
        blocos = separar_por_idioma(conteudo)
        print(f"🔎 Tentativa {tentativa + 1} - Conteúdo inglês:\n{blocos.get('en', '')[:200]}...\n")

        album, artista = extrair_album_artista(blocos.get('en', ''))
        if album and artista:
            salvar_multilingue(blocos, album, artista, hoje)
            print(f"✅ Post multilíngue gerado com sucesso para: {album} by {artista}")
            break
        else:
            print("⚠️ Formato inesperado. Tentando novamente...\n")

    else:
        print("❌ Não foi possível gerar conteúdo válido após 3 tentativas. Abortando.")
