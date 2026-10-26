var database = require("../database/config")

function autenticar(email, senha) {
    var instrucaoSql = `
        SELECT
            u.id,
            u.nome,
            u.email,
            u.fk_empresa AS empresaId,
            tc.nome_cargo AS cargo
        FROM usuario u
        JOIN tipo_cargo tc ON tc.id = u.fk_cargo
        WHERE u.email = ? AND u.senha = ?;
    `;
    return database.executar(instrucaoSql, [email, senha]);
}

// "cargo" aqui é o NOME do cargo (rh, admin, analista, gestor).
// A subquery converte para o id gravado em fk_cargo.
function cadastrar(nome, email, senha, cargo, fk_empresa) {
    var instrucaoSql = `
        INSERT INTO usuario (nome, email, senha, fk_cargo, fk_empresa)
        VALUES (?, ?, ?, (SELECT id FROM tipo_cargo WHERE nome_cargo = ?), ?);
    `;
    return database.executar(instrucaoSql, [nome, email, senha, cargo, fk_empresa]);
}

function remover(id, fk_empresa) {
    var instrucaoSql = `
        DELETE FROM usuario WHERE id = ? AND fk_empresa = ?;
    `;
    return database.executar(instrucaoSql, [id, fk_empresa]);
}

function atualizar(id, nova_senha, fk_empresa) {
    var instrucaoSql = `
        UPDATE usuario SET senha = ? WHERE id = ? AND fk_empresa = ?;
    `;
    return database.executar(instrucaoSql, [nova_senha, id, fk_empresa]);
}

function listar(fk_empresa) {
    var instrucaoSql = `
        SELECT u.id, u.nome, u.email, tc.nome_cargo AS cargo
        FROM usuario u
        JOIN tipo_cargo tc ON tc.id = u.fk_cargo
        WHERE u.fk_empresa = ?
        ORDER BY FIELD(tc.nome_cargo, 'rh', 'gestor', 'analista', 'admin'), u.nome;
    `;
    return database.executar(instrucaoSql, [fk_empresa]);
}

function listarPorNome(fk_empresa, nome) {
    var instrucaoSql = `
        SELECT u.nome, u.email, tc.nome_cargo AS cargo
        FROM usuario u
        JOIN tipo_cargo tc ON tc.id = u.fk_cargo
        WHERE u.fk_empresa = ? AND u.nome = ?;
    `;
    return database.executar(instrucaoSql, [fk_empresa, nome]);
}

function listarPorCargo(fk_empresa, cargo) {
    var instrucaoSql = `
        SELECT u.nome, u.email, tc.nome_cargo AS cargo
        FROM usuario u
        JOIN tipo_cargo tc ON tc.id = u.fk_cargo
        WHERE u.fk_empresa = ? AND tc.nome_cargo = ?;
    `;
    return database.executar(instrucaoSql, [fk_empresa, cargo]);
}

function listarPorNomeCargo(fk_empresa, nome, cargo) {
    var instrucaoSql = `
        SELECT u.nome, u.email, tc.nome_cargo AS cargo
        FROM usuario u
        JOIN tipo_cargo tc ON tc.id = u.fk_cargo
        WHERE u.fk_empresa = ? AND u.nome = ? AND tc.nome_cargo = ?;
    `;
    return database.executar(instrucaoSql, [fk_empresa, nome, cargo]);
}

function esqueceuSenha(senha, email, id, cargo) {
    var instrucaoSql = `
        UPDATE usuario
        SET senha = ?, email = ?
        WHERE id = ?
        AND fk_cargo = (SELECT id FROM tipo_cargo WHERE nome_cargo = ?);
    `;
    return database.executar(instrucaoSql, [senha, email, id, cargo]);
}

function buscarEmailPendentes() {
    var instrucaoSql = `
        SELECT u.id, u.nome, u.email, u.senha
        FROM usuario u
        JOIN tipo_cargo c ON c.id = u.fk_cargo
        WHERE c.nome_cargo = 'rh' AND u.enviou_email = 0;
    `;
    return database.executar(instrucaoSql);
}


module.exports = {
    autenticar,
    cadastrar,
    remover,
    atualizar,
    listar,
    listarPorNome,
    listarPorCargo,
    listarPorNomeCargo,
    esqueceuSenha,
    buscarEmailPendentes
};
