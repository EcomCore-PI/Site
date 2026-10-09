drop database if exists ecommerce;
create database if not exists ecommerce;
use ecommerce;

CREATE TABLE empresa (
    id int primary key auto_increment,
    cnpj char(14) unique not null,
    razao_social varchar(160) unique not null,
    nome_fantasia varchar(160) not null,
    email_contato varchar(255) not null,
    stats enum('Ativo', 'Inativo') default 'Ativo',
    data_cadastro datetime default current_timestamp
);

create table usuario(
    id int primary key auto_increment,
    nome varchar(100) not null,
    email varchar(300) unique not null,
    senha varchar(255) not null,
    cargo enum('Analista', 'Gerente', 'RH') not null,
    enviou_email tinyint(1) default 0,
    fk_empresa int not null, 
    foreign key (fk_empresa) references empresa(id)
);

create table servidor(
    id int primary key auto_increment,
    nome varchar(100) not null, 
    fk_empresa int not null,    
    constraint fk_servidor_empresa foreign key (fk_empresa) references empresa(id)
);

create table captura(
    id int primary key auto_increment, 
    nome varchar(40) not null,        
    valor float not null,            
    unidade_de_medida varchar(30) not null,        
    horario datetime default current_timestamp,
    fk_servidor int not null,         
    constraint fk_servidor_captura foreign key (fk_servidor) references servidor(id)
);

create table alerta (
    id int primary key auto_increment,
    fk_servidor int not null,
    componente varchar(45) not null,
    valor_medido float not null,
    limite tinyint not null,
    nivel ENUM('Atenção', 'Crítico') not null,
    data_inicio datetime not null default current_timestamp,
    ultima_atualizacao datetime not null default current_timestamp,
    data_fim datetime null,
    ativo tinyint generated always as (if(data_fim is null, 1, null)) stored,
    constraint fk_alerta_servidor foreign key (fk_servidor) references servidor(id),
    unique key uq_alerta_ativo (fk_servidor, recurso, ativo)
);

CREATE OR REPLACE VIEW vwCapturas AS
SELECT 
    c.id AS captura_id,
    c.nome,
    c.valor,
    c.unidade_de_medida,
    c.horario,
    c.fk_servidor,
    s.nome AS nome_servidor,
    s.fk_empresa
FROM captura c
JOIN servidor s ON c.fk_servidor = s.id;
    
    CREATE OR REPLACE VIEW vwAviso as    
    SELECT
		e.nome_fantasia,
        s.nome AS servidor,
        c.valor AS cpu
    FROM empresa e
    JOIN servidor s
        ON e.id = s.fk_empresa
    JOIN captura c
        ON s.id = c.fk_servidor;
        
        
        
	CREATE OR REPLACE VIEW buscarDashPorEmpresa as
        SELECT s.id, e.nome_fantasia
     FROM servidor s
     JOIN empresa e on e.id = s.fk_empresa; 
    
     
     
 -- 1. Inserindo a Empresa (Assumirá ID 1)
INSERT INTO empresa (cnpj, razao_social, nome_fantasia, email_contato) 
VALUES ('60746948000112', 'Banco Bradesco S.A.', 'Bradesco', 'email@exemplo.com');

-- 2. Inserindo os primeiros usuários (Corrigida a falta do 'cargo' da Beth)
INSERT INTO usuario (nome, email, senha, cargo, fk_empresa) 
VALUES ('Beth', 'xpto@mercado.livre', '12345678', 'Gerente', 1);

INSERT INTO usuario (nome, email, senha, cargo, fk_empresa) 
VALUES ('William', 'analista@mercado.livre','87654321', 'Analista', 1);

-- 3. Inserindo os usuários solicitados (Adicionado o 'fk_empresa')
INSERT INTO usuario (nome, email, senha, cargo, fk_empresa) VALUES 
('Valdito', 'valdito@gmail.com', 'Senha123', 'Gerente', 1),
('Ashey', 'ashey@gmail.com', 'Senha123', 'Analista', 1),
('Math', 'math@gmail.com', 'Senha123', 'RH', 1);

INSERT INTO usuario (nome, email, senha, cargo, enviou_email, fk_empresa) VALUES 
('Math', 'math@gmail.com', 'Senha123', 'RH', default, 1);


INSERT INTO servidor (nome, fk_empresa) VALUES 
('Servidor SP - Banco de Dados', 1),
('Servidor RJ - Aplicação', 1);


SELECT * FROM usuario;