const cron = require("node-cron");
const { default: email } = require("../database/email");
var usuarioModel = require("../models/usuarioModel");

async function verificarEEnviarEmails() {
    console.log("[CRON] Verificando se existem e-mails pendentes...");
    
    try {
        const resultado = await usuarioModel.buscarEmailPendentes();
        
        if (resultado.length > 0) { 
            console.log(`[CRON] Encontrados ${resultado.length} e-mails pendentes.`);
            
            for (let i = 0; i < resultado.length; i++) {
                let usuario = resultado[i];
                let assunto = "Seu acesso foi criado";
                let texto = `Olá, ${usuario.nome}! 
Seu acesso foi criado com sucesso. Seguem abaixo os seus dados temporários para login:
E-mail: ${usuario.email}
Senha: ${usuario.senha}
Seja bem-vindo(a)!`

                try {
                    await email.send(usuario.email, assunto, texto);
                    await usuarioModel.marcarComoEnviado(usuario.id);
                    
                    console.log(`[CRON] E-mail e status atualizados para: ${usuario.nome}`);
                } catch (erro) {
                    console.error(`[CRON] Falha ao processar o usuário ${usuario.nome}:`, erro);
                }
            }
        } else {
            console.log("[CRON] Nenhum e-mail pendente no momento.");
        }
    } catch (erroBanco) {
        console.error("[CRON] Erro ao buscar no banco:", erroBanco);
    }
}

//isso aqui da 10 minutos altere aqui para testar
cron.schedule("*/1 * * * *", () => {
    verificarEEnviarEmails();
});

module.exports = {
    verificarEEnviarEmails
};