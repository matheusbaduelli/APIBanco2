# Imagem base estável para pacotes Python
FROM python:3.12.1

# Diretório de trabalho
WORKDIR /app

# Copiar arquivos do projeto
COPY . /app

# Instalar dependências do sistema necessárias para compilar pacotes Python
RUN apt-get update && \
    apt-get install -y gcc g++ libpq-dev build-essential && \
    rm -rf /var/lib/apt/lists/*

# Atualizar pip, setuptools e wheel
RUN pip install --upgrade pip setuptools wheel



# Expor a porta da aplicação
EXPOSE 8000

# Comando para rodar a aplicação
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    libtool \
    autoconf \
    automake \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Baixar e instalar TA-Lib nativo
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
    && tar -xzf ta-lib-0.4.0-src.tar.gz \
    && cd ta-lib \
    && ./configure --prefix=/usr \
    && make \
    && make install \
    && cd .. \
    && rm -rf ta-lib ta-lib-0.4.0-src.tar.gz


    # Instalar dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt
