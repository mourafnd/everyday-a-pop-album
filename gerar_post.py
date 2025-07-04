# gerar_post.py - Gera um post diário multilíngue com um álbum pop

from openai import OpenAI
from datetime import datetime
import os
import re
import unicodedata
import requests
from urllib.parse import quote

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Função para gerar slug a partir de texto
def gerar_slug(texto):
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('utf-8')
    texto = re.sub(r'[^a-zA-Z0-9\s-]', '', texto)
    texto = texto.lower().replace(' ', '-').strip('-')
    return texto

# Função para gerar a URL da API do iTunes
def gerar_url_itunes(artista, album):
    artista_album = f"{artista} {album}"
    artista_album = re.sub(r'[\\/]', '', artista_album)  # remove / e \
    query = '+'.join(artista_album.split())
    return f"https://itunes.apple.com/search?term={query}&entity=album&limit=1"

# Função para buscar a imagem do álbum no iTunes
def buscar_capa_album(artista, album):
    url = gerar_url_itunes(artista, album)
    try:
        resposta = requests.get(url)
        if resposta.status_code == 200:
            dados = resposta.json()
            if dados['resultCount'] > 0:
                capa_url = dados['results'][0]['artworkUrl100']
                return capa_url.replace('100x100bb.jpg', '500x500bb.jpg')
    except Exception as e:
        print(f"Erro ao buscar capa do álbum: {e}")
    return None

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
        "Mantenha a estrutura exata e não adicione explicações extras. Escolha sempre um álbum real diferente. E IMPORTANTE! Garanta que temos a mesma informação nos 3 idiomas"
    )

    resposta = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
        max_tokens=1500
    )
    
    conteudo = resposta.choices[0].message.content.strip()
    print("📝 Resposta completa da API:\n", conteudo[:1000], "\n---\n")  # Mostra parte do conteúdo para depuração
    return conteudo

# Extrai o título do álbum/artista da versão em inglês
def extrair_album_artista(texto):
    match = re.search(r'\*\*(.*?)\*\* by \*\*(.*?)\*\*', texto)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    print("⚠️ Formato inesperado do título no conteúdo inglês.")
    return None, None


# Divide o conteúdo por idioma
def separar_por_idioma(conteudo):
    partes = re.split(r'^##\s+', conteudo, flags=re.MULTILINE)
    blocos = {}

    for i, parte in enumerate(partes):
        if i == 0:
            # Tudo antes do primeiro "##", assumimos que é inglês
            blocos['en'] = parte.strip()
        elif parte.strip().startswith("ENGLISH"):
            blocos['en'] = parte.partition("\n")[2].strip()
        elif parte.strip().startswith("PORTUGUÊS"):
            blocos['pt'] = parte.partition("\n")[2].strip()
        elif parte.strip().startswith("ESPAÑOL"):
            blocos['es'] = parte.partition("\n")[2].strip()

    return blocos


def gerar_blocos_streaming(album_title, album_artist, lang):
    search_term =  quote(f"{album_title} {album_artist}")
    streaming_links = f"""- 🎧 [Spotify](https://open.spotify.com/search/{search_term})
- 🌀 [Deezer](https://www.deezer.com/search/{search_term})
- 🍎 [Apple Music](https://music.apple.com/search?term={search_term})
- ▶️ [YouTube](https://www.youtube.com/results?search_query={search_term})
- 🎵 [YouTube Music](https://music.youtube.com/search?q={search_term})"""


    if lang == 'pt':
        return f"\n\n**🎧 Ouça agora na sua plataforma favorita:**\n\n{streaming_links}"
    elif lang == 'es':
        return f"\n\n**🎧 Escucha ahora en tu plataforma favorita:**\n\n{streaming_links}"
    else:
        return f"\n\n**🎧 Listen now on your favorite platform:**\n\n{streaming_links}"


# Extrai a primeira frase de curiosidades (para meta description)
def extrair_primeira_curiosidade(texto, lang):
    if lang == 'pt':
        padrao = r"(?i)-\s*Curiosidades.*?:\s*(.*?)\."
    elif lang == 'es':
        padrao = r"(?i)-\s*Curiosidades.*?:\s*(.*?)\."
    else:
        padrao = r"(?i)-\s*Curiosities.*?:\s*(.*?)\."

    match = re.search(padrao, texto)
    if match:
        return match.group(1).strip() + "."
    return None

def formatar_topicos_com_h2(conteudo, lang):

    TOPICOS_TITULOS = {
        'en': {
            'year': 'Year',
            'country': 'Country',
            'genre': 'Genre',
            'tracks': 'Main Tracks',
            'curiosities': 'Curiosities',
        },
        'pt': {
            'year': 'Ano',
            'country': 'País',
            'genre': 'Gênero',
            'tracks': 'Faixas principais',
            'curiosities': 'Curiosidades',
        },
        'es': {
            'year': 'Año',
            'country': 'País',
            'genre': 'Género',
            'tracks': 'Canciones principales',
            'curiosities': 'Curiosidades',
        }
    }

    titulos = TOPICOS_TITULOS.get(lang, {})
    linhas = conteudo.splitlines()
    resultado = []
    for linha in linhas:
        for chave, texto in titulos.items():
            if re.match(rf"^-\s*{re.escape(texto)}", linha, re.IGNORECASE):
                resultado.append(f"## {texto}")
                break
        resultado.append(linha)
    return "\n".join(resultado)

import urllib.parse

def gerar_links_externos(album, artista):
    # Codifica para URLs seguras
    artista_encoded = urllib.parse.quote_plus(artista)
    album_encoded = urllib.parse.quote_plus(album)
    
    # Links externos formatados
    links = [
        f"- 📚 [Read more about {artista} on Wikipedia](https://en.wikipedia.org/wiki/{artista_encoded})",
        f"- 💿 [Explore the album on AllMusic](https://www.allmusic.com/search/albums/{album_encoded})",
        f"- 📀 [Check discography details on Discogs](https://www.discogs.com/search/?q={album_encoded}+{artista_encoded}&type=all)",
        f"- ✍️ [Find lyrics and meanings on Genius](https://genius.com/search?q={album_encoded}%20{artista_encoded})"
    ]
    
    return "## Learn More\n\n" + "\n".join(links)

# Salvar os arquivos index.en.md, index.pt.md, index.es.md
def salvar_multilingue(blocos, album, artista, hoje):
    titulo_base = f"{album} - {artista}"
    slug = gerar_slug(f"{album} {artista}")
    descricao_base = f"Discover the album '{album}' by {artista}, a highlight in pop music."
    keywords_base = f"pop album, {artista}, {album}, music"
    capa_url = buscar_capa_album(artista, album)

    pasta = f"content/posts/{slug}"
    os.makedirs(pasta, exist_ok=True)

    idiomas = {
        'en': {
            'title': titulo_base,
            'content': blocos.get('en', '')
        },
        'pt': {
            'title': f"{album} - {artista}",
            'content': blocos.get('pt', '')
        },
        'es': {
            'title': f"{album} - {artista}",
            'content': blocos.get('es', '')
        },
    }

    for lang, dados in idiomas.items():

        descricao = extrair_primeira_curiosidade(dados['content'], lang)
        dados['content'] = formatar_topicos_com_h2(dados['content'], lang)
        if not descricao:
            if lang == 'pt':
                descricao = f"Descubra o álbum '{album}' de {artista}, um destaque na música pop."
            elif lang == 'es':
                descricao = f"Descubre el álbum '{album}' de {artista}, un destacado de la música pop."
            else:
                descricao = f"Discover the album '{album}' by {artista}, a highlight in pop music."

        descricao = descricao.replace('"', '\\"')
        caminho = f"{pasta}/index.{lang}.md"
        with open(caminho, "w", encoding="utf-8") as f:
            f.write("---\n")
            f.write(f'title: "{dados["title"]}"\n')
            f.write(f'date: {hoje.isoformat()}\n')
            f.write(f'slug: "{slug}"\n')
            f.write(f'description: "{descricao}"\n')
            if capa_url:
                f.write("cover:\n")
                f.write(f'  image: "{capa_url}"\n')
                f.write(f'  alt: "{album} by {artista}"\n')
            keywords_formatadas = ', '.join([f'"{k.strip()}"' for k in keywords_base.split(',')])
            f.write(f"keywords: [{keywords_formatadas}]\n")
            f.write("---\n\n")
            f.write(dados['content'])
            f.write("\n\n")
            f.write(gerar_blocos_streaming(album, artista, lang))
            f.write("\n\n")
            f.write(gerar_links_externos(album, artista))

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
