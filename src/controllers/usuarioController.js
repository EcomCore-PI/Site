var usuarioModel = require("../models/usuarioModel");

function autenticar(req, res) {
    var email = req.body.emailServer;
    var senha = req.body.senhaServer;

    if (email == undefined) {
        res.status(400).send("Seu email está undefined!");
    } else if (senha == undefined) {
        res.status(400).send("Sua senha está indefinida!");
    } else {

        usuarioModel.autenticar(email, senha)
            .then(
                function (resultadoAutenticar) {
                    console.log(`\nResultados encontrados: ${resultadoAutenticar.length}`);
                    console.log(`Resultados: ${JSON.stringify(resultadoAutenticar)}`); 

                    if (resultadoAutenticar.length == 1) {
                        console.log(resultadoAutenticar);

                        res.json({
                            id: resultadoAutenticar[0].id,
                            email: resultadoAutenticar[0].email,
                            nome: resultadoAutenticar[0].nome,
                            senha: resultadoAutenticar[0].senha,
                            cargo: resultadoAutenticar[0].cargo,
                            fk_empresa: resultadoAutenticar[0].empresaId
                        });

                    } else if (resultadoAutenticar.length == 0) {
                        res.status(403).send("Email e/ou senha inválido(s)");
                    } else {
                        res.status(403).send("Mais de um usuário com o mesmo login e senha!");
                    }
                }
            ).catch(
                function (erro) {
                    console.log(erro);
                    console.log("\nHouve um erro ao realizar o login! Erro: ", erro.sqlMessage);
                    res.status(500).json(erro.sqlMessage);
                }
            );
    }

}

function cadastrar(req, res) {
    var nome = req.body.nomeServer;
    var email = req.body.emailServer;
    var senha = req.body.senhaServer;
    var cargo = req.body.cargoServer;
    var fk_empresa = req.body.fk_empresaServer;

    
    if (nome == undefined) {
        res.status(400).send("Seu nome está undefined!");
    } else if (email == undefined) {
        res.status(400).send("Seu email está undefined!");
    } else if (senha == undefined) {
        res.status(400).send("Sua senha está undefined!");
    } else if (cargo == undefined) {
        res.status(400).send("Seu cargo está undefined!");
    } else if (fk_empresa == undefined) {
        res.status(400).send("Seu id está undefined!");
    } else {

        
        usuarioModel.cadastrar(nome, email, senha, cargo, fk_empresa)
            .then(
                function (resultado) {
                    res.json(resultado);
                }
            ).catch(
                function (erro) {
                    console.log(erro);
                    console.log(
                        "\nHouve um erro ao realizar o cadastro! Erro: ",
                        erro.sqlMessage
                    );

                    // email é UNIQUE no banco: avisa de forma clara que já existe
                    if (erro.code == "ER_DUP_ENTRY") {
                        res.status(409).send("Já existe um usuário cadastrado com este e-mail.");
                    } else {
                        res.status(500).json(erro.sqlMessage);
                    }
                }
            );
    }
}

function atualizar(req, res) {
    var id = req.body.idServer;
    var nova_senha = req.body.senhaServer;
    var fk_empresa = req.body.fk_empresaServer;

    if (id == undefined) {
        res.status(400).send("O id do usuário está undefined!");
    } else if (nova_senha == undefined) {
        res.status(400).send("Sua senha está undefined!");
    } else if (String(nova_senha).length < 8) {
        res.status(400).send("A senha precisa ter pelo menos 8 caracteres.");
    } else if (fk_empresa == undefined) {
        res.status(400).send("O id da empresa está undefined!");
    } else {

        usuarioModel.atualizar(id, nova_senha, fk_empresa)
            .then(
                function (resultado) {
                    if (resultado.affectedRows == 0) {
                        res.status(404).send("Usuário não encontrado.");
                    } else {
                        res.json(resultado);
                    }
                }
            ).catch(
                function (erro) {
                    console.log(erro);
                    console.log(
                        "\nHouve um erro ao realizar a atualização do usuário! Erro: ",
                        erro.sqlMessage
                    );
                    res.status(500).json(erro.sqlMessage);
                }
            );
    }
}


function remover(req, res) {
    var id = req.body.idServer;
    var fk_empresa = req.body.fk_empresaServer;

    if (id == undefined) {
        res.status(400).send("O id do usuário está undefined!");
    } else if (fk_empresa == undefined) {
        res.status(400).send("O id da empresa está undefined!");
    } else {

        usuarioModel.remover(id, fk_empresa)
            .then(
                function (resultado) {
                    if (resultado.affectedRows == 0) {
                        res.status(404).send("Usuário não encontrado.");
                    } else {
                        res.json(resultado);
                    }
                }
            ).catch(
                function (erro) {
                    console.log(erro);
                    console.log(
                        "\nHouve um erro ao realizar a remoção do usuário! Erro: ",
                        erro.sqlMessage
                    );
                    res.status(500).json(erro.sqlMessage);
                }
            );
    }
}


function listar(req, res) {
    var fk_empresa = req.body.fk_empresaServer;

    if (fk_empresa == undefined) {
        res.status(400).send("O id da empresa está undefined!");
    } else {
        usuarioModel.listar(fk_empresa)
            .then(function (resultado) {
                res.status(200).json(resultado);
            }).catch(function (erro) {
                console.log(erro);
                res.status(500).json(erro.sqlMessage);
            });
    }
}

module.exports = {
    autenticar,
    cadastrar,
    atualizar,
    remover,
    listar
}