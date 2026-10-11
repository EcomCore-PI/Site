var database = require("../database/config")

// Esquema: servidor -> componente -> captura.
// O "nome" do recurso ('CPU', 'Memoria RAM', 'Disco') é o nome do componente.

function buscarUltimasCapturas(fk_servidor, limite_linhas, nome) {
    var instrucaoSql = `
        SELECT c.nome, cap.valor, cap.horario
        FROM captura cap
        JOIN componente c ON c.id = cap.fk_componente
        WHERE c.fk_servidor = ? AND c.nome = ?
        ORDER BY cap.id DESC
        LIMIT ?;
    `;
    return database.executar(instrucaoSql, [fk_servidor, nome, Number(limite_linhas)]);
}

function buscarTempoReal(fk_servidor, nome, limite_linhas) {
    var instrucaoSql = `
        SELECT cap.valor, cap.horario
        FROM captura cap
        JOIN componente c ON c.id = cap.fk_componente
        WHERE c.fk_servidor = ? AND c.nome = ?
        ORDER BY cap.id DESC
        LIMIT ?;
    `;
    return database.executar(instrucaoSql, [fk_servidor, nome, Number(limite_linhas)]);
}

function inserirCaptura(fk_componente, fk_tipo_componente, valor, unidade_medida) {
    var instrucaoSql = `
        INSERT INTO captura (fk_componente, fk_tipo_componente, valor, unidade_medida)
        VALUES (?, ?, ?, ?);
    `;
    return database.executar(instrucaoSql, [fk_componente, fk_tipo_componente, valor, unidade_medida]);
}

module.exports = { buscarTempoReal, buscarUltimasCapturas, inserirCaptura }