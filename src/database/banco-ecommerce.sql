-- drop database if exists ecommerce;
create database if not exists ecommerce;
use ecommerce;


CREATE TABLE empresa (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cnpj CHAR(14) NOT NULL UNIQUE,
    razao_social VARCHAR(160) NOT NULL,
    nome_fantasia VARCHAR(160),
    email_contato VARCHAR(255) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'ativo',
    data_cadastro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE local_empresa (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fk_empresa INT NOT NULL,
    nome_local VARCHAR(100) NOT NULL,
    cep CHAR(8),
    logradouro VARCHAR(150),
    numero VARCHAR(20),
    complemento VARCHAR(100),
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    estado CHAR(2),
    pais VARCHAR(60) DEFAULT 'Brasil',

    CONSTRAINT fk_local_empresa
        FOREIGN KEY (fk_empresa)
        REFERENCES empresa(id),

    UNIQUE KEY uk_local_empresa (id, fk_empresa)
);


CREATE TABLE usuario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(300) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL,
    cargo VARCHAR(40) NOT NULL,
    enviou_email TINYINT(1) NOT NULL DEFAULT 0,
    fk_empresa INT NOT NULL,

    CONSTRAINT fk_usuario_empresa
        FOREIGN KEY (fk_empresa)
        REFERENCES empresa(id)
);


CREATE TABLE servidor (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    fk_empresa INT NOT NULL,
    fk_local INT NOT NULL,
    hostname VARCHAR(255),
    status VARCHAR(30) NOT NULL DEFAULT 'ativo',

    CONSTRAINT fk_servidor_empresa
        FOREIGN KEY (fk_empresa)
        REFERENCES empresa(id),

    CONSTRAINT fk_servidor_local_empresa
        FOREIGN KEY (fk_local, fk_empresa)
        REFERENCES local_empresa(id, fk_empresa)
);


CREATE TABLE componente (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fk_servidor INT NOT NULL,
    nome VARCHAR(100) NOT NULL,
    descricao VARCHAR(255),
    ativo TINYINT(1) NOT NULL DEFAULT 1,

    CONSTRAINT fk_componente_servidor
        FOREIGN KEY (fk_servidor)
        REFERENCES servidor(id)
);

CREATE TABLE tipo_componente (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fk_componente INT NOT NULL,
    nome VARCHAR(100) NOT NULL UNIQUE,

    CONSTRAINT fk_tipo_componente
        FOREIGN KEY (fk_componente)
        REFERENCES componente(id)
);


CREATE TABLE metrica (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fk_tipo_componente INT NOT NULL,
    limite_atencao DECIMAL(12,3) NOT NULL,
    limite_critico DECIMAL(12,3) NOT NULL,
    ativo TINYINT(1) NOT NULL DEFAULT 1,

    CONSTRAINT fk_metrica_tipo
        FOREIGN KEY (fk_tipo_componente)
        REFERENCES tipo_componente(id),

    CONSTRAINT uk_metrica_tipo
        UNIQUE (fk_tipo_componente),

    CONSTRAINT chk_limites_metrica
        CHECK (limite_critico > limite_atencao)
);


CREATE TABLE captura (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fk_componente INT NOT NULL,
    fk_tipo_componente INT NOT NULL,
    valor DECIMAL(15,4) NOT NULL,
    unidade_medida VARCHAR(20) NOT NULL,
    horario DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_captura_componente
        FOREIGN KEY (fk_componente)
        REFERENCES componente(id),

    CONSTRAINT fk_captura_tipo
        FOREIGN KEY (fk_tipo_componente)
        REFERENCES tipo_componente(id)
);


CREATE TABLE alerta (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fk_captura INT NOT NULL,
    fk_metrica INT NOT NULL,
    fk_componente INT NOT NULL,
    valor_medido DECIMAL(15,4) NOT NULL,
    nivel ENUM('atencao', 'critico') NOT NULL,
    data_inicio DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ultima_atualizacao DATETIME,
    data_fim DATETIME,
    ativo TINYINT(1) NOT NULL DEFAULT 1,
    
    CONSTRAINT fk_alerta_componente
        FOREIGN KEY (fk_componente)
        REFERENCES componente(id),

    CONSTRAINT fk_alerta_captura
        FOREIGN KEY (fk_captura)
        REFERENCES captura(id),

    CONSTRAINT fk_alerta_metrica
        FOREIGN KEY (fk_metrica)
        REFERENCES metrica(id)
);



INSERT INTO empresa (cnpj, razao_social, nome_fantasia, email_contato)
VALUES ('60746948000112', 'Banco Bradesco S.A.', 'Bradesco', 'email@exemplo.com');

INSERT INTO usuario (nome, email, senha, cargo, fk_empresa) VALUES
('Marco',    'marco@gmail.com',     'Senha123', 'Gerente',  1),
('Isabelle', 'isa@gmail.com', 'Senha123', 'Analista', 1),
('Ana', 'ana@gmail.com',      'Senha123', 'Gerente',  1),
('João',   'joao@gmail.com',        'Senha123', 'Analista', 1),
('Math',    'math@gmail.com',         'Senha123', 'RH',       1);

INSERT INTO local_empresa (fk_empresa, nome_local, cidade, estado) VALUES
(1, 'Data Center Sao Paulo',      'Sao Paulo',      'SP'),
(1, 'Data Center Rio de Janeiro', 'Rio de Janeiro', 'RJ');

-- fk_local precisa existir em local_empresa COM a mesma fk_empresa (FK composta)
INSERT INTO servidor (nome, fk_empresa, fk_local) VALUES
('Servidor SP - Banco de Dados', 1, 1),
('Servidor RJ - Aplicacao',      1, 2);

-- Os nomes de tipo_componente e componente precisam ser IGUAIS:
-- o servidor.py liga um ao outro pelo nome.
INSERT INTO tipo_componente (nome) VALUES ('CPU'), ('Memoria RAM'), ('Disco');

INSERT INTO metrica (fk_tipo_componente, limite_atencao, limite_critico)
SELECT id, 80, 90 FROM tipo_componente;

INSERT INTO componente (fk_servidor, nome, descricao)
SELECT s.id, t.nome, CONCAT('Monitoramento de ', t.nome)
FROM servidor s CROSS JOIN tipo_componente t;