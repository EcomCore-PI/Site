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


function cadastrar(nome, email, senha, cargo, fk_empresa) {
    var instrucaoSql = `
        INSERT INTO usuario (nome, email, senha, cargo, fk_empresa) VALUES (?, ?, ?, ?, ?);
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
        SELECT id, nome, email, cargo FROM usuario
        WHERE fk_empresa = ?
        ORDER BY FIELD(cargo, 'RH', 'Gerente', 'Analista'), nome;
    `;
    return database.executar(instrucaoSql, [fk_empresa]);
}

function listarPorNome(fk_empresa, nome) {
    var instrucaoSql = `Select nome, email, cargo from usuario where fk_empresa = ${fk_empresa} and nome = ${nome}`

    return database.executar(instrucaoSql)
}

function listarPorCargo(fk_empresa, cargo) {
    var instrucaoSql = `Select nome, email, cargo from usuario where fk_empresa = ${fk_empresa} and cargo = ${cargo}`

    return database.executar(instrucaoSql)
}

function listarPorNomeCargo(fk_empresa, nome, cargo) {
    var instrucaoSql = `Select nome, email, cargo from usuario where fk_empresa = ${fk_empresa} and nome = ${nome} and cargo = ${cargo}`

    return database.executar(instrucaoSql)
}

function esqueceuSenha(senha, email, id, cargo) {
    var instrucaoSql = `update usuario
    set senha = ${senha}, email = ${email}
    where id = ${id}
    and cargo = ${cargo}`

    return database.executar(instrucaoSql)
}

function buscarEmailPendentes() {
    var instrucaoSql = `SELECT id, nome, email, senha FROM usuario WHERE cargo = 'RH' and enviou_email = 0`;

    return database.executar(instrucaoSql)
}

function marcarComoEnviado(id) {
    var instrucaoSql = `update usuario set enviou_email = 1 where id = ${id}`

    return database.executar(instrucaoSql)
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
    buscarEmailPendentes,
    marcarComoEnviado,
    esqueceuSenha,
};
