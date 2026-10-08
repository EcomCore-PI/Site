var database = require("../database/config");

function buscarPorId(id) {
  var instrucaoSql = `SELECT * FROM empresa WHERE id = '${id}'`;

  return database.executar(instrucaoSql);
}

function buscarPorCnpj(cnpj) {
  var instrucaoSql = `SELECT * FROM empresa WHERE cnpj = '${cnpj}'`;

  return database.executar(instrucaoSql);
}

function listar() {
  var instrucaoSql = `SELECT id, cnpj, razao_social FROM empresa`;

  return database.executar(instrucaoSql);
}


function cadastrar(cnpj, razao_social, email_contato) {
  var instrucaoSql = `INSERT INTO empresa (razao_social, cnpj) VALUES ('${cnpj}', '${razao_social}', '${email_contato}')`;

  return database.executar(instrucaoSql);
}

module.exports = { buscarPorCnpj, buscarPorId, cadastrar, listar};
